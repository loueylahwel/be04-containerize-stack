from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIResponse:
    content: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str


class AIProvider(ABC):
    """Abstract interface for LLM providers. Switching providers touches only this file's implementations."""

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> AIResponse:
        ...

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def model_id(self) -> str:
        ...
