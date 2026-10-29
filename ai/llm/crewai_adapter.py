"""
Adapter between RepoMind-AI's Hugging Face inference
engine and CrewAI.
"""

import logging
import time
from typing import Any, Optional

from crewai.llms.base_llm import BaseLLM

from .inference import InferenceEngine

logger = logging.getLogger(__name__)


class HuggingFaceCrewLLM(BaseLLM):
    """Expose local Hugging Face inference to CrewAI."""

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            model="huggingface-local",
            provider="huggingface",
        )

        if model_name:
            from .model_loader import ModelLoader

            loader = ModelLoader(model_name=model_name)
            self.engine = InferenceEngine(model_loader=loader)
        else:
            self.engine = InferenceEngine()

        self._call_count = 0

    def call(
        self,
        prompt: str,
        tools: Any = None,
        callbacks: Any = None,
        available_functions: Any = None,
        from_task: Any = None,
        from_agent: Any = None,
        response_model: Any = None,
        **kwargs: Any,
    ) -> str:
        """Generate a response using the local model."""

        self._call_count += 1
        started = time.perf_counter()
        formatted_prompt = self._messages_to_prompt(prompt)

        max_new_tokens = kwargs.get("max_new_tokens", 256)

        logger.info(
            "Crew LLM call #%d: agent=%s prompt_chars=%d "
            "max_new_tokens=%d",
            self._call_count,
            getattr(from_agent, "role", "unknown"),
            len(formatted_prompt),
            max_new_tokens,
        )

        try:
            result = self.engine.generate(
                prompt=formatted_prompt,
                max_new_tokens=max_new_tokens,
                temperature=kwargs.get("temperature", 0.2),
                top_p=kwargs.get("top_p", 0.9),
            )

            logger.info(
                "Crew LLM call #%d completed in %.2fs; "
                "response_chars=%d",
                self._call_count,
                time.perf_counter() - started,
                len(result),
            )
            return result

        except Exception:
            logger.exception(
                "Crew LLM call #%d failed after %.2fs",
                self._call_count,
                time.perf_counter() - started,
            )
            raise

    @staticmethod
    def _messages_to_prompt(messages: Any) -> str:
        """Convert CrewAI messages to a plain-text prompt."""

        if isinstance(messages, str):
            return messages

        if isinstance(messages, (list, tuple)):
            formatted = []

            for message in messages:
                if isinstance(message, dict):
                    role = message.get("role", "user")
                    content = message.get("content", "")
                else:
                    role = getattr(message, "role", "user")
                    content = getattr(message, "content", str(message))

                formatted.append(f"{role}: {content}")

            return "\n\n".join(formatted)

        return str(messages)
