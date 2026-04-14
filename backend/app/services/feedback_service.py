from sqlalchemy.orm import Session
from app.repositories.feedback_repo import FeedbackRepository
from app.services.engagement_service import EngagementService
from app.services.learner_profile_service import LearnerProfileService
from app.models.message_feedback import MessageFeedback
from app.models.engagement_event import EventType


# After this many consistent feedback signals, auto-adjust preferences
ADJUSTMENT_THRESHOLD = 3


class FeedbackService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = FeedbackRepository(db)
        self.engagement = EngagementService(db)
        self.profile_service = LearnerProfileService(db)

    def submit_feedback(self, user_id, message_id, is_helpful, feedback_text=None, feedback_category=None):
        feedback = MessageFeedback(
            message_id=message_id,
            is_helpful=is_helpful,
            feedback_text=feedback_text,
            feedback_category=feedback_category,
        )
        saved = self.repo.create_feedback(feedback)

        # Track engagement
        self.engagement.track_event(
            user_id=user_id,
            event_type=EventType.FEEDBACK_GIVEN,
            payload={
                "message_id": str(message_id),
                "is_helpful": is_helpful,
                "category": feedback_category,
            },
        )

        # Auto-adjust profile based on feedback patterns
        if feedback_category:
            self._maybe_adjust_profile(user_id, feedback_category)

        return saved

    def _maybe_adjust_profile(self, user_id, latest_category: str):
        """
        Check recent feedback patterns and auto-adjust profile if user
        is consistently giving the same signal.
        """
        recent = self.repo.get_recent_by_user(user_id, limit=ADJUSTMENT_THRESHOLD * 2)
        if len(recent) < ADJUSTMENT_THRESHOLD:
            return

        # Count recent feedback categories
        recent_categories = [f.feedback_category for f in recent if f.feedback_category]
        if len(recent_categories) < ADJUSTMENT_THRESHOLD:
            return

        last_n = recent_categories[:ADJUSTMENT_THRESHOLD]

        # If last N feedbacks are all the same category, adjust
        if all(c == "TOO_COMPLEX" for c in last_n):
            self.profile_service.update_preferences(user_id, {
                "pace_preference": "DETAILED",
                "explanation_detail_level": "VERBOSE",
                "preferred_code_complexity": "SIMPLE",
            })

        elif all(c == "TOO_SIMPLE" for c in last_n):
            self.profile_service.update_preferences(user_id, {
                "pace_preference": "QUICK",
                "explanation_detail_level": "CONCISE",
                "preferred_code_complexity": "ADVANCED",
            })
