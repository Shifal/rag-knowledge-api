from google import genai
from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

GENERATION_MODEL = "gemini-3.5-flash"

_PROMPT_TEMPLATE = """You are a helpful assistant answering questions using ONLY the context provided below.

Context:
{context}

Question: {question}

Instructions:
- Answer using only information found in the context above.
- If the context does not contain enough information to answer the question, say "I don't have enough information in the provided documents to answer that" — do not guess or use outside knowledge.
- Be concise and direct.

Answer:"""


def generate_answer(question: str, context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    prompt = _PROMPT_TEMPLATE.format(context=context, question=question)

    response = _client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )
    return response.text.strip()