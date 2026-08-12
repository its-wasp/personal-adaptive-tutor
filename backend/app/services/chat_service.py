from sqlalchemy.orm import Session
from app.repositories.chat_repo import ChatRepository
from app.repositories.quiz_repo import QuizRepository
from app.models.chat_session import ChatSession, KnowledgeLevel
from app.models.chat_message import ChatMessage, MessageRole, MessageType
from app.llm.factory import get_llm_provider
from app.llm.prompt_builder import build_explanation_prompt, build_system_prompt
from app.llm.personalization_reasons import build_reasons
from app.llm.response_parser import parse_explanation_response
from app.llm.structured import generate_structured
from app.services.learner_profile_service import LearnerProfileService
from app.services.engagement_service import EngagementService
from app.services.errors import NotFoundError
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

        # Snapshot the signals that shaped this message. We persist them
        # (rather than recomputing at render time) because the profile
        # evolves — older messages should reflect the profile they were
        # actually generated with.
        reasons = build_reasons(profile, retrieved)
        message = ChatMessage(
            chat_session_id=session.id,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.EXPLANATION,
            content=parsed["explanation"],
            metadata_json={"reasons": reasons} if reasons else None,
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

    def _assert_owns_session(self, chat_session_id, user_id) -> ChatSession:
        """
        Return the session only if `user_id` owns it.

        Every entry point that takes a caller-supplied chat_session_id must go
        through here. A session that exists but belongs to someone else raises
        the same error as one that doesn't exist, so the response can't be used
        to probe for valid session ids.
        """
        session = self.repo.get_session(chat_session_id)
        if not session or str(session.user_id) != str(user_id):
            raise NotFoundError("Chat session not found")
        return session

    def delete_session(self, chat_session_id, user_id):
        """Delete a chat session if it belongs to the user. Returns True on success."""
        try:
            self._assert_owns_session(chat_session_id, user_id)
        except NotFoundError:
            return False
        self.repo.delete_session(chat_session_id)
        return True

    def get_conversation(self, chat_session_id, user_id):
        self._assert_owns_session(chat_session_id, user_id)
        messages = self.repo.get_session_messages(chat_session_id)
        quiz_repo = QuizRepository(self.repo.db)

        conversation = []
        for msg in messages:
            # Pull out the personalization reasons snapshot if present — the
            # same metadata_json blob also holds quiz_id for QUIZ messages.
            reasons = None
            if msg.metadata_json:
                reasons = msg.metadata_json.get("reasons") or None

            item = {
                "id": msg.id,
                "role": msg.role.value,
                "message_type": msg.message_type.value,
                "content": msg.content,
                "created_at": msg.created_at,
                "quiz_data": None,
                "personalization_reasons": reasons,
            }

            if msg.message_type == MessageType.QUIZ and msg.metadata_json:
                quiz_id = msg.metadata_json.get("quiz_id")
                quiz = quiz_repo.get_quiz(quiz_id) if quiz_id else None
                if quiz:
                    attempt = quiz_repo.get_attempt_for_user(quiz_id, user_id)
                    answered = attempt is not None
                    item["quiz_data"] = {
                        # quiz_id is what QuizCard posts back on submit. It was
                        # missing here, so a quiz reopened from history couldn't
                        # be answered at all.
                        "quiz_id": str(quiz.id),
                        "question": quiz.question_text,
                        "options": quiz.options_json,
                        "difficulty": quiz.difficulty,
                        "points": quiz.points,
                        # The answer key, the hint and the explanation each give
                        # the answer away, so none of them are serialised until
                        # an attempt exists. Previously all three shipped with
                        # every unanswered quiz and were visible in devtools.
                        "correct_option": quiz.correct_option if answered else None,
                        "hint": quiz.hint if answered else None,
                        "explanation": quiz.explanation if answered else None,
                        "selected_option": attempt.selected_option if answered else None,
                        "is_correct": attempt.is_correct if answered else None,
                        "points_awarded": attempt.points_awarded if answered else None,
                    }

            conversation.append(item)

        return conversation

    def send_message(self, chat_session_id, user_id, content, reply_to_message_id=None):
        # 1. Authorize before writing anything. This also replaces the separate
        # session fetch that used to happen after the insert — which both let a
        # stranger post into someone else's session and left an orphan message
        # behind when the session id didn't exist at all.
        session = self._assert_owns_session(chat_session_id, user_id)

        # 2. Save user message
        user_message = ChatMessage(
            chat_session_id=chat_session_id,
            role=MessageRole.USER,
            message_type=MessageType.GENERAL,
            content=content,
            reply_to_message_id=reply_to_message_id,
        )
        self.repo.create_message(user_message)

        # 3. Get learner profile for personalization
        profile = self.profile_service.get_personalization_context(user_id)

        # 4. Retrieve relevant content via RAG
        retrieved = rag_retriever.retrieve(
            db=self.db,
            query_text=content,
            concept_node_id=session.concept_node_id,
            limit=3,
        )

        # 5. Build personalized system prompt
        system_prompt = build_system_prompt(profile=profile, retrieved_chunks=retrieved)

        # 6. Build conversation context (with summarization for long sessions)
        msg_count = self.repo.get_message_count(chat_session_id)
        messages = [{"role": "system", "content": system_prompt}]

        if msg_count > 20 and session.conversation_summary:
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

        # 9. Save assistant response (with a snapshot of the personalization
        # signals that shaped it — see create_chat for rationale).
        reasons = build_reasons(profile, retrieved)
        assistant_message = ChatMessage(
            chat_session_id=chat_session_id,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.GENERAL,
            content=response,
            metadata_json={"reasons": reasons} if reasons else None,
        )

        saved_message = self.repo.create_message(assistant_message)

        # Track engagement
        self.engagement.track_event(
            user_id=user_id,
            event_type=EventType.MESSAGE_SENT,
            chat_session_id=chat_session_id,
            concept_node_id=session.concept_node_id,
        )

        # Update learner memory if enough messages have accumulated
        self.profile_service.maybe_update_summary(user_id, chat_session_id)

        return saved_message

    def _generate_structured_explanation(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Generate the opening explanation and parse it into {title, explanation}.

        Uses Groq's JSON mode for server-side structured output, falling back to
        the response parser (which handles markdown fences / unescaped newlines)
        when that still isn't clean. A failure here surfaces as ValueError and
        the router maps it to 502.
        """
        return generate_structured(
            llm=self.llm,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            parse=parse_explanation_response,
            correction=(
                "Your previous reply wasn't in the requested format. Reply with "
                "a line reading 'TITLE: <short title>', then a line containing "
                "only three dashes, then the explanation in markdown. No JSON, "
                "and do not wrap the whole reply in a code fence."
            ),
            json_mode=False,
            failure_message=(
                "The tutor returned a response we couldn't parse. This is "
                "usually a transient LLM quirk — please try again."
            ),
        )

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
