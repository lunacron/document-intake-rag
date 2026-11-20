from functools import lru_cache

from sentence_transformers import SentenceTransformer

from .config import settings


@lru_cache
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.embed_model)


def embed(texts: list[str]) -> list[list[float]]:
    return _model().encode(texts, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    # arctic-embed expects this prefix on queries, not on documents.
    return embed(["Represent this sentence for searching relevant passages: " + text])[0]
