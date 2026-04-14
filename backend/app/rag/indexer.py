"""
Indexes new content into the vector store (content_embeddings table).
"""
from sqlalchemy.orm import Session
from app.rag.embedder import embed_text, embed_batch
from app.models.content_embedding import ContentEmbedding
from app.repositories.embedding_repo import EmbeddingRepository


def index_content(
    db: Session,
    content_type: str,
    content_text: str,
    concept_node_id=None,
    difficulty_level: str = None,
    content_summary: str = None,
    metadata: dict = None,
    source_id=None,
) -> ContentEmbedding:
    """Embed and store a single content chunk."""
    vector = embed_text(content_text)

    embedding = ContentEmbedding(
        content_type=content_type,
        source_id=source_id,
        concept_node_id=concept_node_id,
        content_text=content_text,
        content_summary=content_summary,
        difficulty_level=difficulty_level,
        metadata_json=metadata,
        embedding=vector,
    )

    repo = EmbeddingRepository(db)
    return repo.create(embedding)


def index_batch(
    db: Session,
    items: list[dict],
) -> int:
    """
    Embed and store a batch of content chunks.

    Each item in the list should have:
      - content_type: str
      - content_text: str
      - concept_node_id: UUID (optional)
      - difficulty_level: str (optional)
      - content_summary: str (optional)
      - metadata: dict (optional)
    """
    texts = [item["content_text"] for item in items]
    vectors = embed_batch(texts)

    embeddings = []
    for item, vector in zip(items, vectors):
        embeddings.append(ContentEmbedding(
            content_type=item["content_type"],
            concept_node_id=item.get("concept_node_id"),
            content_text=item["content_text"],
            content_summary=item.get("content_summary"),
            difficulty_level=item.get("difficulty_level"),
            metadata_json=item.get("metadata"),
            embedding=vector,
        ))

    repo = EmbeddingRepository(db)
    repo.create_batch(embeddings)
    return len(embeddings)
