from google import genai
from google.genai import types
from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def embed_text(text: str) -> list[float]:
    """Converts a piece of text into a 768-dimensional embedding vector."""
    response = _client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return response.embeddings[0].values


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embeds multiple chunks in one call — more efficient during ingestion."""
    response = _client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return [e.values for e in response.embeddings]