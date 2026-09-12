"""
Adapter between RepoMind-AI's Hugging Face inference
engine and CrewAI.

This keeps model execution inside our existing
LLM module instead of using a paid API.
"""

from typing import Any, Optional

from crewai.llms.base_llm import BaseLLM

from .inference import InferenceEngine


class HuggingFaceCrewLLM(BaseLLM):
    """
    Lightweight adapter that exposes our local
    Hugging Face inference engine to the agent layer.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
    ):
        super().__init__(
            model="huggingface-local",
            provider="huggingface",
        )

        if model_name:
            from .model_loader import ModelLoader

            loader = ModelLoader(
                model_name=model_name
            )

            self.engine = InferenceEngine(
                model_loader=loader
            )
        else:
            self.engine = InferenceEngine()

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
        """
        Generate a response using the local
        Hugging Face model.
        """

        return self.engine.generate(
            prompt=self._messages_to_prompt(prompt),
            max_new_tokens=kwargs.get("max_new_tokens", 512),
            temperature=kwargs.get("temperature", 0.2),
            top_p=kwargs.get("top_p", 0.9),
        )

    @staticmethod
    def _messages_to_prompt(messages: Any) -> str:
        if isinstance(messages, str):
            return messages

        return "\n\n".join(
            f"{message.get('role', 'user')}: {message.get('content', '')}"
            for message in messages
        )

    