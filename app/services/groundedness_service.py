from google import genai
from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

GROUNDEDNESS_MODEL = "gemini-3.5-flash"

_GROUNDEDNESS_PROMPT = """You are verifying whether an answer is properly grounded in the given context.

Context:
{context}

Answer to verify: "{answer}"

Is this answer fully supported by the context above? Respond with exactly one word: "yes" or "no".
Respond "no" if the answer includes any claim not found in the context, even if the claim seems reasonable."""


def is_answer_grounded(answer: str, context_chunks: list[str]) -> bool:
    context = "\n\n---\n\n".join(context_chunks)
    prompt = _GROUNDEDNESS_PROMPT.format(context=context, answer=answer)

    response = _client.models.generate_content(
        model=GROUNDEDNESS_MODEL,
        contents=prompt,
    )
    verdict = response.text.strip().lower()
    return verdict.startswith("yes")