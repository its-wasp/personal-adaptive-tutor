"""
Singleton wrapper around the sentence-transformers embedding model.
Loaded once at first use, stays in memory for the lifetime of the app.
"""
from sentence_transformers import SentenceTransformer

_model = None
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"Loading embedding model: {MODEL_NAME}...")
        _model = SentenceTransformer(MODEL_NAME)
        print(f"Embedding model loaded. Dimension: {EMBEDDING_DIM}")
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string into a 384-dim vector."""
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. More efficient than calling embed_text in a loop."""
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return [v.tolist() for v in vectors]
