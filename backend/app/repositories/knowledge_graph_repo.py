from datetime import datetime
from sqlalchemy.orm import Session
from app.models.concept_node import ConceptNode
from app.models.concept_edge import ConceptEdge, RelationType
from app.models.concept_mastery import ConceptMastery


# Mastery a prerequisite must reach before the concepts depending on it unlock.
# The frontend mirrors this value in Dashboard.jsx and ConceptGrid.jsx.
UNLOCK_THRESHOLD = 0.6


class KnowledgeGraphRepository:

    def __init__(self, db: Session):
        self.db = db

    # ── Concept Nodes ──

    def get_all_nodes(self, subject: str) -> list[ConceptNode]:
        return (
            self.db.query(ConceptNode)
            .filter(ConceptNode.subject == subject)
            .order_by(ConceptNode.difficulty_tier, ConceptNode.name)
            .all()
        )

    def get_node_by_name(self, subject: str, name: str) -> ConceptNode | None:
        return (
            self.db.query(ConceptNode)
            .filter(ConceptNode.subject == subject, ConceptNode.name == name)
            .first()
        )

    def get_node_by_id(self, node_id) -> ConceptNode | None:
        return self.db.query(ConceptNode).filter(ConceptNode.id == node_id).first()

    def get_nodes_by_ids(self, node_ids) -> dict:
        """
        Resolve many node ids in a single query.

        Returns {node_id: ConceptNode}. Callers that need display names for a
        list of mastery rows should use this instead of calling
        get_node_by_id in a loop.
        """
        ids = list(node_ids)
        if not ids:
            return {}
        nodes = self.db.query(ConceptNode).filter(ConceptNode.id.in_(ids)).all()
        return {n.id: n for n in nodes}

    # ── Edges ──

    def get_all_edges(self, subject: str) -> list[ConceptEdge]:
        return (
            self.db.query(ConceptEdge)
            .join(ConceptNode, ConceptEdge.from_node_id == ConceptNode.id)
            .filter(ConceptNode.subject == subject)
            .all()
        )

    def get_prerequisites(self, node_id) -> list[ConceptNode]:
        """
        Get all nodes that are prerequisites for the given node.

        Two queries per call. For whole-graph work use get_prerequisite_map.
        """
        edges = (
            self.db.query(ConceptEdge)
            .filter(
                ConceptEdge.to_node_id == node_id,
                ConceptEdge.relation_type == RelationType.PREREQUISITE,
            )
            .all()
        )
        prereq_ids = [e.from_node_id for e in edges]
        if not prereq_ids:
            return []
        return self.db.query(ConceptNode).filter(ConceptNode.id.in_(prereq_ids)).all()

    def get_prerequisite_map(self, subject: str) -> dict:
        """
        {to_node_id: [from_node_id, ...]} for every PREREQUISITE edge in a subject.

        One query for the entire graph. Only ids are selected because callers
        resolving unlock state need to look up mastery, not concept rows.
        """
        edges = (
            self.db.query(ConceptEdge.from_node_id, ConceptEdge.to_node_id)
            .join(ConceptNode, ConceptEdge.from_node_id == ConceptNode.id)
            .filter(
                ConceptNode.subject == subject,
                ConceptEdge.relation_type == RelationType.PREREQUISITE,
            )
            .all()
        )
        prereq_map: dict = {}
        for from_id, to_id in edges:
            prereq_map.setdefault(to_id, []).append(from_id)
        return prereq_map

    # ── Mastery ──

    def get_user_mastery(self, user_id, concept_node_id) -> ConceptMastery | None:
        return (
            self.db.query(ConceptMastery)
            .filter(
                ConceptMastery.user_id == user_id,
                ConceptMastery.concept_node_id == concept_node_id,
            )
            .first()
        )

    def get_all_user_mastery(self, user_id) -> list[ConceptMastery]:
        return (
            self.db.query(ConceptMastery)
            .filter(ConceptMastery.user_id == user_id)
            .all()
        )

    def create_mastery(self, mastery: ConceptMastery) -> ConceptMastery:
        self.db.add(mastery)
        self.db.commit()
        self.db.refresh(mastery)
        return mastery

    def save_mastery(self, mastery: ConceptMastery) -> ConceptMastery:
        self.db.commit()
        self.db.refresh(mastery)
        return mastery

    def get_ready_for_review(self, user_id) -> list[ConceptMastery]:
        """Get concepts that are due for spaced repetition review."""
        now = datetime.utcnow()
        return (
            self.db.query(ConceptMastery)
            .filter(
                ConceptMastery.user_id == user_id,
                ConceptMastery.next_review_at <= now,
                ConceptMastery.mastery_level > 0,
            )
            .order_by(ConceptMastery.next_review_at.asc())
            .all()
        )

    def get_unlocked_concepts(self, user_id, subject: str) -> list[ConceptNode]:
        """
        Get concepts where ALL prerequisites are at or above UNLOCK_THRESHOLD.
        Concepts with no prerequisites are always unlocked.

        Three queries total. This used to call get_prerequisites once per node,
        which meant two more queries per concept — around fifty extra round
        trips for the 25-node DSA graph, on a path the dashboard hits on load.
        """
        all_nodes = self.get_all_nodes(subject)
        mastery_map = {
            m.concept_node_id: m.mastery_level
            for m in self.get_all_user_mastery(user_id)
        }
        prereq_map = self.get_prerequisite_map(subject)

        # all(()) is True, so nodes with no prerequisites fall out as unlocked.
        return [
            node
            for node in all_nodes
            if all(
                mastery_map.get(prereq_id, 0.0) >= UNLOCK_THRESHOLD
                for prereq_id in prereq_map.get(node.id, ())
            )
        ]
