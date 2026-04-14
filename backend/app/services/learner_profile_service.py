from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.learner_profile_repo import LearnerProfileRepository
from app.repositories.knowledge_graph_repo import KnowledgeGraphRepository
from app.repositories.chat_repo import ChatRepository
from app.models.learner_profile import LearnerProfile
from app.llm.factory import get_llm_provider


# Update the learner summary every N messages within a session
SUMMARY_UPDATE_INTERVAL = 5


class LearnerProfileService:

    def __init__(self, db: Session):
        self.repo = LearnerProfileRepository(db)
        self.graph_repo = KnowledgeGraphRepository(db)
        self.chat_repo = ChatRepository(db)

    def get_or_create_profile(self, user_id) -> LearnerProfile:
        profile = self.repo.get_by_user_id(user_id)
        if not profile:
            profile = LearnerProfile(user_id=user_id)
            profile = self.repo.create(profile)
        return profile

    def update_preferences(self, user_id, preferences: dict) -> LearnerProfile:
        profile = self.get_or_create_profile(user_id)

        if "learning_style" in preferences:
            profile.learning_style = preferences["learning_style"]
        if "pace_preference" in preferences:
            profile.pace_preference = preferences["pace_preference"]
        if "explanation_detail_level" in preferences:
            profile.explanation_detail_level = preferences["explanation_detail_level"]
        if "preferred_code_complexity" in preferences:
            profile.preferred_code_complexity = preferences["preferred_code_complexity"]
        if "analogy_preference" in preferences:
            profile.analogy_preference = preferences["analogy_preference"]

        return self.repo.save(profile)

    def get_personalization_context(self, user_id) -> dict:
        """
        Build a dict of personalization signals that gets injected into LLM prompts.
        This is the bridge between the profile data and the prompt builder.
        """
        profile = self.get_or_create_profile(user_id)

        # Get mastery data for strengths/weaknesses
        mastery_list = self.graph_repo.get_all_user_mastery(user_id)
        strengths = []
        weaknesses = []
        for m in mastery_list:
            node = self.graph_repo.get_node_by_id(m.concept_node_id)
            if not node:
                continue
            if m.mastery_level >= 0.7:
                strengths.append(node.display_name)
            elif m.mastery_level < 0.4 and m.total_answers > 0:
                weaknesses.append(node.display_name)

        return {
            "learning_style": profile.learning_style or "not set",
            "pace_preference": profile.pace_preference or "MODERATE",
            "explanation_detail_level": profile.explanation_detail_level or "STANDARD",
            "preferred_code_complexity": profile.preferred_code_complexity or "SIMPLE",
            "use_analogies": profile.analogy_preference,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "total_sessions": profile.total_sessions,
            "onboarding_completed": profile.onboarding_completed,
            "learner_summary": profile.learner_summary,
        }

    def record_session_activity(self, user_id):
        """Update session count and last active timestamp."""
        profile = self.get_or_create_profile(user_id)
        profile.total_sessions += 1
        profile.last_active_at = datetime.utcnow()
        return self.repo.save(profile)

    def maybe_update_summary(self, user_id, chat_session_id):
        """
        Check if we should update the learner summary based on message count.
        Called after every send_message — only triggers the LLM call
        when the message count crosses a multiple of SUMMARY_UPDATE_INTERVAL.
        """
        msg_count = self.chat_repo.get_message_count(chat_session_id)
        # Only update at multiples of the interval (5, 10, 15, ...)
        # User messages are roughly half, so total of 10 means ~5 exchanges
        if msg_count < SUMMARY_UPDATE_INTERVAL or msg_count % SUMMARY_UPDATE_INTERVAL != 0:
            return

        self._generate_summary(user_id, chat_session_id)

    def _generate_summary(self, user_id, chat_session_id):
        """
        Call the LLM to generate/update the learner summary based on
        recent conversation + existing summary.
        """
        profile = self.get_or_create_profile(user_id)

        # Get recent messages from this session
        recent_messages = self.chat_repo.get_recent_messages(chat_session_id, limit=20)
        if not recent_messages:
            return

        # Build conversation snippet for the LLM
        conversation_lines = []
        for msg in recent_messages:
            role = "Student" if msg.role.value == "USER" else "Tutor"
            # Truncate long messages to keep token usage reasonable
            content = msg.content[:300] if msg.content else ""
            conversation_lines.append(f"{role}: {content}")

        conversation_text = "\n".join(conversation_lines)
        existing_summary = profile.learner_summary or "No previous summary — this is the first observation."

        # Get session topic for context
        session = self.chat_repo.get_session(chat_session_id)
        topic = session.topic_name if session else "unknown topic"

        prompt = f"""You are analyzing a learning session to build a learner profile summary.

EXISTING LEARNER SUMMARY:
{existing_summary}

RECENT CONVERSATION (topic: {topic}):
{conversation_text}

Based on the conversation above, update the learner summary. The summary should capture:
- How this learner thinks and approaches problems
- What explanations or styles helped them understand (or didn't)
- Specific concepts they grasped quickly or struggled with
- Patterns in their questions (do they ask for examples? formal definitions? analogies?)
- Any breakthroughs or persistent confusions

Keep it concise (3-5 sentences). Write in third person ("This learner...").
Merge new observations with the existing summary — don't repeat, evolve it.
If the existing summary contradicts what you see now, trust the newer evidence.

Return ONLY the updated summary text, nothing else."""

        try:
            llm = get_llm_provider()
            summary = llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )

            profile.learner_summary = summary.strip()
            profile.summary_updated_at = datetime.utcnow()
            self.repo.save(profile)
        except Exception as e:
            # Don't let summary generation failures break the main flow
            print(f"Warning: learner summary update failed: {e}")
