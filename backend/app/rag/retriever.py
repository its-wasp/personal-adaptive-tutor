"""
Retrieves relevant content chunks from pgvector based on semantic similarity.

Returns an empty list when the embedding model isn't available (cloud
deploys without sentence-transformers). The rest of the pipeline —
personalization, conversation history, learner memory — still works.
"""
from sqlalchemy.orm import Session
from app.rag.embedder import embed_text, is_available
from app.repositories.embedding_repo import EmbeddingRepository


def retrieve(
    db: Session,
    query_text: str,
    concept_node_id=None,
    limit: int = 5,
    difficulty_level: str = None,
) -> list[dict]:
    """
    Embed the query and find the most similar content chunks.

    Returns a list of dicts with:
      - content_text: the actual text content
      - content_summary: short label
      - difficulty_level: BEGINNER/INTERMEDIATE/ADVANCED
      - content_type: EXPLANATION/QUIZ_EXPLANATION/REFERENCE_SNIPPET
    """
    if not is_available():
        return []

    query_vector = embed_text(query_text)
    if query_vector is None:
        return []

    repo = EmbeddingRepository(db)

    results = repo.search_similar(
        query_vector=query_vector,
        limit=limit,
        concept_node_id=concept_node_id,
        difficulty_level=difficulty_level,
    )

    return [
        {
            "content_text": r.content_text,
            "content_summary": r.content_summary,
            "difficulty_level": r.difficulty_level,
            "content_type": r.content_type,
        }
        for r in results
    ]
