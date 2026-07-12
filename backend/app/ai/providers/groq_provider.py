import httpx
from .base import AIProvider, AIResponse


class GroqProvider(AIProvider):
    """Groq LLM provider — fast inference, free tier, no card required."""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self._api_key = api_key
        self._model = model

    def name(self) -> str:
        return "groq"

    def model_id(self) -> str:
        return self._model

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> AIResponse:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(self.API_URL, json=payload, headers=headers)
            resp.raise_for_status()

        data = resp.json()
        usage = data.get("usage", {})
        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            provider=self.name(),
            model=self._model,
        )
