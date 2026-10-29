
"""
Inference engine for RepoMind-AI.

Responsible for sending repository-analysis prompts
to the local Hugging Face model.
"""

import logging
import time

import torch

from .model_loader import ModelLoader

logger = logging.getLogger(__name__)


class InferenceEngine:
    """Handles text generation using the Hugging Face model."""

    def __init__(
        self,
        model_loader: ModelLoader | None = None,
    ):
        self.loader = model_loader if model_loader is not None else ModelLoader()
        self.tokenizer = None
        self.model = None

    def _ensure_model(self):
        """Load the model if it has not already been loaded."""
        if self.model is None:
            self.tokenizer, self.model = self.loader.load()

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> str:
        """Generate a response and log inference timing."""

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        started = time.perf_counter()

        # Load the model if needed.
        self._ensure_model()
        loaded_at = time.perf_counter()

        # Tokenize and move tensors to the model's device.
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096,
        )
        inputs = {
            key: value.to(self.loader.device)
            for key, value in inputs.items()
        }
        tokenized_at = time.perf_counter()

        # MPS operations may be asynchronous. Synchronize before
        # and after generation to measure elapsed time more accurately.
        is_mps = self.loader.device == "mps"

        if is_mps:
            torch.mps.synchronize()

        generation_started = time.perf_counter()

        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        if is_mps:
            torch.mps.synchronize()

        generated_at = time.perf_counter()

        # Decode only the newly generated tokens.
        input_length = inputs["input_ids"].shape[-1]
        generated_tokens = output[0][input_length:]

        response = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        ).strip()

        logger.info(
            "HF inference: device=%s input_tokens=%d "
            "output_tokens=%d load_s=%.2f tokenize_s=%.2f "
            "generate_s=%.2f total_s=%.2f",
            self.loader.device,
            input_length,
            len(generated_tokens),
            loaded_at - started,
            tokenized_at - loaded_at,
            generated_at - generation_started,
            time.perf_counter() - started,
        )

        return response

    def analyze_repository(self, repository_context: str) -> str:
        """Generate a complete repository analysis."""
        from .prompt_templates import build_repository_analysis_prompt

        prompt = build_repository_analysis_prompt(repository_context)
        return self.generate(prompt)

    def analyze_architecture(self, repository_context: str) -> str:
        """Generate architecture analysis."""
        from .prompt_templates import build_architecture_prompt

        prompt = build_architecture_prompt(repository_context)
        return self.generate(prompt)

    def analyze_code_quality(self, repository_context: str) -> str:
        """Generate code-quality analysis."""
        from .prompt_templates import build_code_quality_prompt

        prompt = build_code_quality_prompt(repository_context)
        return self.generate(prompt)
