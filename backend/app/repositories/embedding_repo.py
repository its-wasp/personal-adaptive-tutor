from sqlalchemy.orm import Session
from app.models.content_embedding import ContentEmbedding


class EmbeddingRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, embedding: ContentEmbedding) -> ContentEmbedding:
        self.db.add(embedding)
        self.db.commit()
        self.db.refresh(embedding)
        return embedding

    def create_batch(self, embeddings: list[ContentEmbedding]):
        self.db.add_all(embeddings)
        self.db.commit()

    def search_similar(
        self,
        query_vector: list[float],
        limit: int = 5,
        concept_node_id=None,
        difficulty_level: str = None,
    ) -> list[ContentEmbedding]:
        """
        Find the most similar content embeddings using cosine distance.
        Optionally filter by concept_node_id and difficulty_level.
        """
        query = self.db.query(ContentEmbedding).filter(
            ContentEmbedding.embedding.isnot(None)
        )

        if concept_node_id:
            query = query.filter(ContentEmbedding.concept_node_id == concept_node_id)

        if difficulty_level:
            query = query.filter(ContentEmbedding.difficulty_level == difficulty_level)

        # Order by cosine distance (smaller = more similar)
        query = query.order_by(
            ContentEmbedding.embedding.cosine_distance(query_vector)
        )

        return query.limit(limit).all()

    def count_by_concept(self, concept_node_id) -> int:
        return (
            self.db.query(ContentEmbedding)
            .filter(ContentEmbedding.concept_node_id == concept_node_id)
            .count()
        )

    def count_all(self) -> int:
        return self.db.query(ContentEmbedding).count()
