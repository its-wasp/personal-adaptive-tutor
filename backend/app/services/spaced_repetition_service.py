"""
SM-2 Spaced Repetition Algorithm.

Quality ratings (mapped from quiz performance):
  0 — Complete blackout, no recall
  1 — Incorrect, but recognized the answer when shown
  2 — Incorrect, but the answer seemed easy to recall
  3 — Correct with serious difficulty
  4 — Correct after hesitation
  5 — Perfect recall

We simplify to: correct → quality 4, incorrect → quality 1.
Repeated correct answers on hard concepts bump to 5.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repositories.knowledge_graph_repo import KnowledgeGraphRepository
from app.models.concept_mastery import ConceptMastery


class SpacedRepetitionService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = KnowledgeGraphRepository(db)

    def update_after_review(self, mastery: ConceptMastery, is_correct: bool):
        """
        Apply SM-2 algorithm to update review schedule after a quiz/review.
        """
        # Map performance to SM-2 quality (0-5)
        if is_correct:
            # If high mastery already, it's easy recall (5), otherwise solid recall (4)
            quality = 5 if mastery.mastery_level >= 0.7 else 4
        else:
            # Wrong answer — recognized when shown (1)
            quality = 1

        # Update ease factor: EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        ef = mastery.ease_factor
        ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        mastery.ease_factor = max(1.3, ef)  # SM-2 minimum is 1.3

        if quality < 3:
            # Failed — reset interval to 1 day
            mastery.review_interval_days = 1.0
        else:
            # Passed — grow the interval
            if mastery.review_interval_days < 1:
                mastery.review_interval_days = 1.0
            elif mastery.review_interval_days == 1.0:
                mastery.review_interval_days = 6.0
            else:
                mastery.review_interval_days = round(
                    mastery.review_interval_days * mastery.ease_factor, 1
                )

        # Set next review date
        mastery.last_reviewed_at = datetime.utcnow()
        mastery.next_review_at = datetime.utcnow() + timedelta(
            days=mastery.review_interval_days
        )

        self.db.commit()
        return mastery

    def get_due_reviews(self, user_id, limit: int = 10):
        """
        Get concepts that are due for review (next_review_at <= now).
        Returns enriched data with concept info.
        """
        due = self.repo.get_ready_for_review(user_id)[:limit]
        node_map = self.repo.get_nodes_by_ids(m.concept_node_id for m in due)

        results = []
        for mastery in due:
            node = node_map.get(mastery.concept_node_id)
            if not node:
                continue

            days_overdue = 0
            if mastery.next_review_at:
                delta = datetime.utcnow() - mastery.next_review_at
                days_overdue = max(0, round(delta.total_seconds() / 86400, 1))

            results.append({
                "concept_node_id": str(mastery.concept_node_id),
                "concept_name": node.display_name,
                "mastery_level": mastery.mastery_level,
                "confidence": mastery.confidence,
                "days_overdue": days_overdue,
                "review_interval_days": mastery.review_interval_days,
                "ease_factor": mastery.ease_factor,
                "last_reviewed_at": mastery.last_reviewed_at.isoformat() if mastery.last_reviewed_at else None,
            })

        return results

    def get_review_stats(self, user_id):
        """Get a summary of the user's review state."""
        due = self.repo.get_ready_for_review(user_id)
        all_mastery = self.repo.get_all_user_mastery(user_id)

        upcoming = [
            m for m in all_mastery
            if m.next_review_at and m.next_review_at > datetime.utcnow()
        ]

        return {
            "due_now": len(due),
            "upcoming_reviews": len(upcoming),
            "total_concepts_studied": len(all_mastery),
        }
