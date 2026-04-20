"""
Singleton wrapper around the sentence-transformers embedding model.
Loaded once at first use, stays in memory for the lifetime of the app.

For cloud deploys where sentence-transformers is too heavy (requires
~500MB+ PyTorch), the import fails gracefully and embed_text / embed_batch
return None. The retriever handles this by returning empty results —
the tutor still works via personalization + conversation history, just
without RAG grounding.
"""

_model = None
_available = True
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    _available = False
    print("sentence-transformers not installed — RAG embedding disabled")


def is_available() -> bool:
    return _available


def _get_model():
    global _model
    if not _available:
        return None
    if _model is None:
        print(f"Loading embedding model: {MODEL_NAME}...")
        _model = SentenceTransformer(MODEL_NAME)
        print(f"Embedding model loaded. Dimension: {EMBEDDING_DIM}")
    return _model


def embed_text(text: str) -> list[float] | None:
    """Embed a single text string into a 384-dim vector. Returns None if unavailable."""
    model = _get_model()
    if model is None:
        return None
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]] | None:
    """Embed a batch of texts. Returns None if unavailable."""
    model = _get_model()
    if model is None:
        return None
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return [v.tolist() for v in vectors]
