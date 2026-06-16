from sqlalchemy.orm import Session
from app.llm.factory import get_llm_provider
from app.llm.prompt_builder import build_quiz_prompt
from app.llm.response_parser import parse_quiz_response
from app.repositories.quiz_repo import QuizRepository
from app.services.progress_service import ProgressService
from app.services.learner_profile_service import LearnerProfileService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.engagement_service import EngagementService
from app.services.spaced_repetition_service import SpacedRepetitionService
from app.services.errors import NotFoundError
from app.models.engagement_event import EventType
from app.models.chat_session import ChatSession
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.chat_message import ChatMessage, MessageRole, MessageType


class QuizService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = QuizRepository(db)
        self.llm = get_llm_provider()
        self.profile_service = LearnerProfileService(db)
        self.graph_service = KnowledgeGraphService(db)
        self.engagement = EngagementService(db)
        self.spaced_rep = SpacedRepetitionService(db)

    def _owned_session(self, chat_session_id, user_id) -> ChatSession:
        """
        Load a chat session, but only if the caller owns it.

        Filtered in SQL rather than fetch-then-compare so a session belonging
        to someone else is indistinguishable from one that doesn't exist.
        """
        session = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.id == chat_session_id,
                ChatSession.user_id == user_id,
            )
            .first()
        )
        if not session:
            raise NotFoundError("Chat session not found")
        return session

    def generate_quiz(self, chat_session_id, user_id):
        # Authorize first — the router used to load the session with no user
        # filter, so anyone could mint quizzes against another learner's session.
        chat_session = self._owned_session(chat_session_id, user_id)

        # Get learner profile for personalization + weak areas
        profile = self.profile_service.get_personalization_context(user_id)
        weak_areas = profile.get("weaknesses", [])

        prompt = build_quiz_prompt(
            topic_name=chat_session.topic_name,
            level=chat_session.current_level.value,
            profile=profile,
            weak_areas=weak_areas if weak_areas else None,
        )

        parsed = self._generate_structured_quiz(prompt)

        quiz = Quiz(
            chat_session_id=chat_session.id,
            question_text=parsed["question"],
            options_json=parsed["options"],
            correct_option=parsed["correct_option"],
            difficulty=chat_session.current_level.value,
            points=parsed["points"],
            hint=parsed.get("hint"),
            explanation=parsed.get("explanation"),
        )
        quiz = self.repo.create_quiz(quiz)

        # Save chat message referencing quiz
        message = ChatMessage(
            chat_session_id=chat_session.id,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.QUIZ,
            content="Quiz generated",
            metadata_json={"quiz_id": str(quiz.id)},
        )
        self.db.add(message)
        self.db.commit()

        # Track engagement
        self.engagement.track_event(
            user_id=user_id,
            event_type=EventType.QUIZ_STARTED,
            chat_session_id=chat_session.id,
            payload={"quiz_id": str(quiz.id), "topic": chat_session.topic_name},
        )

        return quiz

    def submit_answer(self, quiz_id, user_id, selected_option):
        quiz = self.repo.get_quiz(quiz_id)
        if not quiz:
            raise NotFoundError("Quiz not found")

        # A quiz is only answerable by the owner of the session it belongs to.
        # Without this, any quiz_id could be submitted by any account, awarding
        # points and moving mastery on a session the caller doesn't own.
        session = self._owned_session(quiz.chat_session_id, user_id)

        is_correct = selected_option == quiz.correct_option
        points = quiz.points if is_correct else 0

        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user_id,
            selected_option=selected_option,
            is_correct=is_correct,
            points_awarded=points,
        )
        self.repo.create_attempt(attempt)

        progress_service = ProgressService(self.db)
        progress = progress_service.update_progress(
            user_id=user_id,
            topic_name=session.topic_name,
            points_awarded=points,
            is_correct=is_correct,
        )

        # Sync session level
        session.current_level = progress.current_level
        self.db.commit()

        # Update concept mastery + spaced repetition if session is linked to a concept
        if session.concept_node_id:
            mastery = self.graph_service.update_mastery_after_quiz(
                user_id=user_id,
                concept_node_id=session.concept_node_id,
                is_correct=is_correct,
            )
            # Update SM-2 review schedule
            self.spaced_rep.update_after_review(mastery, is_correct)

        # Track engagement
        self.engagement.track_event(
            user_id=user_id,
            event_type=EventType.QUIZ_COMPLETED,
            chat_session_id=session.id,
            concept_node_id=session.concept_node_id,
            payload={
                "quiz_id": str(quiz_id),
                "is_correct": is_correct,
                "points_awarded": points,
            },
        )

        return {
            "correct": is_correct,
            "correct_option": quiz.correct_option,
            "points_awarded": points,
            "explanation": quiz.explanation,
            "hint": None if is_correct else quiz.hint,
            "new_level": progress.current_level,
            "total_points": progress.total_points,
        }

    def _generate_structured_quiz(self, prompt: str) -> dict:
        """
        Generate a quiz and parse it into the expected shape with one retry
        on malformed output. Mirrors chat_service._generate_structured_explanation.
        """
        messages = [{"role": "user", "content": prompt}]

        # Attempt 1. A ValueError here could come from either the parser or
        # Groq's server-side JSON validator — both get the same retry treatment.
        raw = None
        first_err: Exception | None = None
        try:
            raw = self.llm.generate(messages=messages, temperature=0.8, json_mode=True)
            return parse_quiz_response(raw)
        except ValueError as e:
            first_err = e

        retry_messages = list(messages)
        if raw is not None:
            retry_messages.append({"role": "assistant", "content": raw})
        retry_messages.append({
            "role": "user",
            "content": (
                "Your previous reply wasn't valid JSON. Reply with a single "
                "JSON object containing keys: question, options (object mapping "
                'A-D to strings), correct_option ("A"|"B"|"C"|"D"), points (int), '
                "and optionally hint and explanation. No markdown fences, "
                "no commentary."
            ),
        })
        try:
            raw_retry = self.llm.generate(
                messages=retry_messages, temperature=0.3, json_mode=True
            )
            return parse_quiz_response(raw_retry)
        except ValueError:
            raise ValueError(
                "The tutor returned a quiz we couldn't parse. This is usually "
                "a transient LLM quirk — please try again."
            ) from first_err
