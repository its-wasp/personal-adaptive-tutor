from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.knowledge_graph_repo import KnowledgeGraphRepository
from app.models.concept_mastery import ConceptMastery


class KnowledgeGraphService:

    def __init__(self, db: Session):
        self.repo = KnowledgeGraphRepository(db)

    def get_graph(self, subject: str):
        """Return the full graph with nodes and edges."""
        nodes = self.repo.get_all_nodes(subject)
        edges = self.repo.get_all_edges(subject)

        return {
            "nodes": [
                {
                    "id": str(n.id),
                    "name": n.name,
                    "display_name": n.display_name,
                    "description": n.description,
                    "difficulty_tier": n.difficulty_tier,
                    "estimated_minutes": n.estimated_minutes,
                    "tags": n.tags_json or [],
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "from_node_id": str(e.from_node_id),
                    "to_node_id": str(e.to_node_id),
                    "relation_type": e.relation_type.value,
                    "weight": e.weight,
                }
                for e in edges
            ],
        }

    def get_graph_with_mastery(self, subject: str, user_id):
        """Return the graph with user's mastery overlay on each node."""
        graph = self.get_graph(subject)
        mastery_list = self.repo.get_all_user_mastery(user_id)
        mastery_map = {str(m.concept_node_id): m for m in mastery_list}

        for node in graph["nodes"]:
            m = mastery_map.get(node["id"])
            node["mastery_level"] = m.mastery_level if m else 0.0
            node["confidence"] = m.confidence if m else 0.0
            node["next_review_at"] = m.next_review_at.isoformat() if m and m.next_review_at else None

        return graph

    def get_next_recommended(self, user_id, subject: str):
        """Recommend the next concept to study based on mastery and prerequisites."""
        unlocked = self.repo.get_unlocked_concepts(user_id, subject)
        mastery_list = self.repo.get_all_user_mastery(user_id)
        mastery_map = {m.concept_node_id: m.mastery_level for m in mastery_list}

        # Filter to concepts not yet mastered (mastery < 0.8)
        candidates = [
            n for n in unlocked
            if mastery_map.get(n.id, 0.0) < 0.8
        ]

        if not candidates:
            return None

        # Sort by: lowest mastery first, then by difficulty tier (easiest first)
        candidates.sort(key=lambda n: (mastery_map.get(n.id, 0.0), n.difficulty_tier))

        node = candidates[0]
        return {
            "id": str(node.id),
            "name": node.name,
            "display_name": node.display_name,
            "description": node.description,
            "difficulty_tier": node.difficulty_tier,
            "current_mastery": mastery_map.get(node.id, 0.0),
        }

    def update_mastery_after_quiz(self, user_id, concept_node_id, is_correct: bool):
        """Update mastery level for a concept after a quiz answer."""
        mastery = self.repo.get_user_mastery(user_id, concept_node_id)

        if not mastery:
            mastery = ConceptMastery(
                user_id=user_id,
                concept_node_id=concept_node_id,
            )
            mastery = self.repo.create_mastery(mastery)

        mastery.total_interactions += 1
        mastery.total_answers += 1
        if is_correct:
            mastery.correct_answers += 1

        # Calculate mastery as a weighted accuracy (more recent answers matter more)
        if mastery.total_answers > 0:
            accuracy = mastery.correct_answers / mastery.total_answers
            # Blend: 70% accuracy, 30% previous mastery (smoothing)
            mastery.mastery_level = min(1.0, 0.7 * accuracy + 0.3 * mastery.mastery_level)

        # Confidence increases with more interactions
        mastery.confidence = min(1.0, mastery.total_interactions / 10.0)
        mastery.last_reviewed_at = datetime.utcnow()

        return self.repo.save_mastery(mastery)
