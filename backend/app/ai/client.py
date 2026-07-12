import json
import httpx
import logging
from typing import Optional
from pydantic import ValidationError
from .providers.base import AIProvider, AIResponse
from .schemas import SummarizeOutput
from .cost import estimate_cost

logger = logging.getLogger("ai")

_client: Optional[AIProvider] = None


def set_provider(provider: AIProvider):
    global _client
    _client = provider


def get_provider() -> AIProvider:
    if _client is None:
        raise RuntimeError("AI provider not initialized")
    return _client


async def summarize(text: str) -> SummarizeOutput:
    """Single seam — the only function that calls the LLM. Retries once on malformed JSON."""
    provider = get_provider()

    system_prompt = (
        "You are a precise summarization assistant. "
        "Given a piece of text, return a JSON object with exactly these fields:\n"
        '  "bullets": an array of exactly 3 concise summary strings,\n'
        '  "title": a short title for the text.\n'
        "Return ONLY valid JSON, no markdown, no explanation."
    )

    user_prompt = f"Summarize the following text into 3 bullet points:\n\n{text}"

    last_error: Optional[Exception] = None

    for attempt in range(2):
        try:
            resp: AIResponse = await provider.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=256,
                timeout=30.0,
            )

            parsed = SummarizeOutput.model_validate_json(resp.content)

            cost = estimate_cost(
                provider=resp.provider,
                model=resp.model,
                input_tokens=resp.input_tokens,
                output_tokens=resp.output_tokens,
                feature="summarize",
            )
            logger.info(
                "summarize | provider=%s model=%s in=%d out=%d cost=$%.6f",
                resp.provider,
                resp.model,
                resp.input_tokens,
                resp.output_tokens,
                cost,
            )

            return parsed

        except ValidationError as e:
            last_error = e
            logger.warning("summarize | malformed JSON (attempt %d/2): %s", attempt + 1, e)
            user_prompt = (
                "Your previous output was not valid JSON matching the schema. "
                "Here is what you produced:\n\n"
                f"{resp.content}\n\n"
                "Fix it and return ONLY the correct JSON object."
            )
            continue

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 429 or status >= 500:
                logger.warning("summarize | retryable error %d on attempt %d", status, attempt + 1)
                import asyncio
                await asyncio.sleep(2 ** attempt)
                continue
            raise

    raise RuntimeError(f"AI call failed after retries: {last_error}")
