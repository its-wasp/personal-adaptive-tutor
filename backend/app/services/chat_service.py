from sqlalchemy.orm import Session
from app.repositories.chat_repo import ChatRepository
from app.repositories.quiz_repo import QuizRepository
from app.models.chat_session import ChatSession, KnowledgeLevel
from app.models.chat_message import ChatMessage, MessageRole, MessageType
from app.llm.factory import get_llm_provider
from app.llm.prompt_builder import build_explanation_prompt, build_system_prompt
from app.llm.response_parser import parse_explanation_response
from app.services.learner_profile_service import LearnerProfileService
from app.services.engagement_service import EngagementService
from app.models.engagement_event import EventType
from app.rag import retriever as rag_retriever


class ChatService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = ChatRepository(db)
        self.llm = get_llm_provider()
        self.profile_service = LearnerProfileService(db)
        self.engagement = EngagementService(db)

    def create_chat(self, user_id, topic_name, topic_description, knowledge_level, concept_node_id=None):
        # Get learner profile for personalization
        profile = self.profile_service.get_personalization_context(user_id)

        # Retrieve relevant content via RAG (limit=2 to stay within token budget)
        retrieved = rag_retriever.retrieve(
            db=self.db,
            query_text=f"{topic_name} {topic_description or ''}",
            concept_node_id=concept_node_id,
            limit=2,
        )

        # Build personalized system prompt with RAG context
        system_prompt = build_system_prompt(profile=profile, retrieved_chunks=retrieved)

        prompt = build_explanation_prompt(
            topic_name=topic_name,
            knowledge_level=knowledge_level,
            description=topic_description,
            profile=profile,
            retrieved_chunks=retrieved,
        )

        # Run the LLM BEFORE persisting anything — if generation fails we
        # propagate the ValueError up, the router maps it to 502, and no
        # orphan session/message is left behind. Parser already guarantees
        # non-empty title + explanation, so hallucinated follow-ups can't
        # arise from a blank opener.
        parsed = self._generate_structured_explanation(system_prompt, prompt)

        session = ChatSession(
            user_id=user_id,
            topic_name=topic_name,
            topic_description=topic_description,
            initial_knowledge_level=KnowledgeLevel(knowledge_level),
            current_level=KnowledgeLevel(knowledge_level),
            concept_node_id=concept_node_id,
            title=parsed["title"],
        )
        session = self.repo.create_session(session)

        message = ChatMessage(
            chat_session_id=session.id,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.EXPLANATION,
            content=parsed["explanation"],
        )
        self.repo.create_message(message)

        # Track engagement
        self.engagement.track_event(
            user_id=user_id,
            event_type=EventType.SESSION_START,
            chat_session_id=session.id,
            concept_node_id=concept_node_id,
            payload={"topic": topic_name, "level": knowledge_level},
        )
        self.profile_service.record_session_activity(user_id)

        return session

    def list_user_sessions(self, user_id):
        return self.repo.get_user_sessions(user_id)

    def delete_session(self, chat_session_id, user_id):
        """Delete a chat session if it belongs to the user. Returns True on success."""
        session = self.repo.get_session(chat_session_id)
        if not session:
            return False
        if str(session.user_id) != str(user_id):
            # Session exists but belongs to someone else — treat as not found
            return False
        self.repo.delete_session(chat_session_id)
        return True

    def get_conversation(self, chat_session_id, user_id):
        messages = self.repo.get_session_messages(chat_session_id)
        quiz_repo = QuizRepository(self.repo.db)

        conversation = []
        for msg in messages:
            item = {
                "id": msg.id,
                "role": msg.role.value,
                "message_type": msg.message_type.value,
                "content": msg.content,
                "created_at": msg.created_at,
                "quiz_data": None,
            }

            if msg.message_type == MessageType.QUIZ and msg.metadata_json:
                quiz_id = msg.metadata_json.get("quiz_id")
                if quiz_id:
                    quiz = quiz_repo.get_quiz(quiz_id)
                    attempt = quiz_repo.get_attempt_for_user(quiz_id, user_id)
                    item["quiz_data"] = {
                        "question": quiz.question_text,
                        "options": quiz.options_json,
                        "correct_option": quiz.correct_option,
                        "difficulty": quiz.difficulty,
                        "points": quiz.points,
                        "hint": quiz.hint,
                        "explanation": quiz.explanation,
                        "selected_option": attempt.selected_option if attempt else None,
                        "is_correct": attempt.is_correct if attempt else None,
                        "points_awarded": attempt.points_awarded if attempt else None,
                    }

            conversation.append(item)

        return conversation

    def send_message(self, chat_session_id, user_id, content, reply_to_message_id=None):
        # 1. Save user message
        user_message = ChatMessage(
            chat_session_id=chat_session_id,
            role=MessageRole.USER,
            message_type=MessageType.GENERAL,
            content=content,
            reply_to_message_id=reply_to_message_id,
        )
        self.repo.create_message(user_message)

        # 2. Get session for concept context
        session = self.repo.get_session(chat_session_id)

        # 3. Get learner profile for personalization
        profile = self.profile_service.get_personalization_context(user_id)

        # 4. Retrieve relevant content via RAG
        retrieved = rag_retriever.retrieve(
            db=self.db,
            query_text=content,
            concept_node_id=session.concept_node_id if session else None,
            limit=3,
        )

        # 5. Build personalized system prompt
        system_prompt = build_system_prompt(profile=profile, retrieved_chunks=retrieved)

        # 6. Build conversation context (with summarization for long sessions)
        msg_count = self.repo.get_message_count(chat_session_id)
        messages = [{"role": "system", "content": system_prompt}]

        if msg_count > 20 and session and session.conversation_summary:
            # Long session — use summary + last 10 messages
            messages.append({
                "role": "system",
                "content": f"Summary of earlier conversation:\n{session.conversation_summary}",
            })
            recent_messages = self.repo.get_recent_messages(chat_session_id, limit=10)
        else:
            recent_messages = self.repo.get_recent_messages(chat_session_id, limit=20)

        for msg in recent_messages:
            role = "user" if msg.role == MessageRole.USER else "assistant"
            messages.append({"role": role, "content": msg.content})

        # 7. Call LLM with full context
        response = self.llm.generate(messages=messages, temperature=0.7)

        # 8. Update conversation summary if session is getting long
        if msg_count > 0 and msg_count % 20 == 0:
            self._summarize_conversation(session, chat_session_id)

        # 8. Save assistant response
        assistant_message = ChatMessage(
            chat_session_id=chat_session_id,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.GENERAL,
            content=response,
        )

        saved_message = self.repo.create_message(assistant_message)

        # Track engagement
        self.engagement.track_event(
            user_id=user_id,
            event_type=EventType.MESSAGE_SENT,
            chat_session_id=chat_session_id,
            concept_node_id=session.concept_node_id if session else None,
        )

        # Update learner memory if enough messages have accumulated
        self.profile_service.maybe_update_summary(user_id, chat_session_id)

        return saved_message

    def _generate_structured_explanation(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Generate the opening explanation and parse it into {title, explanation}.

        Uses Groq's JSON mode for server-side structured output, then falls back
        to the response parser (which handles markdown fences / unescaped newlines)
        if parsing still fails. Retries once with a stricter instruction before
        giving up — cheap insurance against transient malformed output.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Attempt 1: normal temperature, JSON mode on. A ValueError here is
        # either a parse failure or Groq's own JSON validator rejecting the
        # generation — both get the same retry treatment.
        raw = None
        first_err: Exception | None = None
        try:
            raw = self.llm.generate(messages=messages, temperature=0.7, json_mode=True)
            return parse_explanation_response(raw)
        except ValueError as e:
            first_err = e

        # Attempt 2: lower temperature + explicit reminder. If the first call
        # failed before returning text, we skip the assistant turn in history.
        retry_messages = list(messages)
        if raw is not None:
            retry_messages.append({"role": "assistant", "content": raw})
        retry_messages.append({
            "role": "user",
            "content": (
                "Your previous reply wasn't valid JSON. Reply with a single "
                'JSON object of the form {"title": "...", "explanation": "..."} '
                "and nothing else — no markdown fences, no commentary."
            ),
        })
        try:
            raw_retry = self.llm.generate(
                messages=retry_messages, temperature=0.2, json_mode=True
            )
            return parse_explanation_response(raw_retry)
        except ValueError:
            # Surface a clean error up to the router, which maps it to a 502.
            raise ValueError(
                "The tutor returned a response we couldn't parse. This is "
                "usually a transient LLM quirk — please try again."
            ) from first_err

    def _summarize_conversation(self, session, chat_session_id):
        """Generate a summary of the conversation so far for long sessions."""
        messages = self.repo.get_session_messages(chat_session_id)
        if len(messages) < 10:
            return

        # Build a condensed version of the conversation
        lines = []
        for msg in messages:
            role = "Student" if msg.role == MessageRole.USER else "Tutor"
            content = msg.content[:200] if msg.content else ""
            lines.append(f"{role}: {content}")

        conversation_text = "\n".join(lines)

        prompt = f"""Summarize this tutoring conversation concisely.
Capture: what topics were covered, what the student understood, what they struggled with,
and where the conversation left off.

{conversation_text}

Write a 3-4 sentence summary."""

        try:
            summary = self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )
            session.conversation_summary = summary.strip()
            self.db.commit()
        except Exception as e:
            print(f"Warning: conversation summarization failed: {e}")
