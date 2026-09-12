"""
Hugging Face model loader for RepoMind-AI.
"""

import logging
import os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


logger = logging.getLogger(__name__)


DEFAULT_MODEL = os.getenv(
    "HF_MODEL",
    "Qwen/Qwen2.5-1.5B-Instruct",
)


class ModelLoader:
    """
    Loads and manages the Hugging Face tokenizer and model.
    """

    _instances = {}

    def __new__(cls, model_name: str = DEFAULT_MODEL):
        key = model_name or DEFAULT_MODEL
        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
        return cls._instances[key]

    def __init__(self, model_name: str = DEFAULT_MODEL):
        if getattr(self, "_initialized", False):
            return

        self.model_name = model_name or DEFAULT_MODEL
        self.tokenizer = None
        self.model = None
        self.device = self._get_device()
        self._initialized = True

    @staticmethod
    def _get_device():
        """
        Prefer CPU by default on macOS because the default Qwen 1.5B model
        frequently exhausts MPS memory on Apple silicon. Users can override with
        HF_DEVICE=mps if they explicitly want the faster but memory-hungry path.
        """

        env_device = os.getenv("HF_DEVICE", "").strip().lower()
        if env_device in {"cpu", "cuda", "mps"}:
            return env_device

        if torch.backends.mps.is_available():
            allow_mps = os.getenv("ALLOW_MPS", "").strip().lower()
            if allow_mps in {"1", "true", "yes", "on"}:
                return "mps"
            return "cpu"

        if torch.cuda.is_available():
            return "cuda"

        return "cpu"

    def load(self):
        """
        Download/load the tokenizer and model.
        """

        if self.model is not None:
            return self.tokenizer, self.model

        logger.info(
            "Loading Hugging Face model: %s",
            self.model_name,
        )

        print(f"Loading model: {self.model_name}")
        print(f"Device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name
        )

        self.model.to(self.device)
        self.model.eval()

        print("Hugging Face model loaded successfully.")

        return self.tokenizer, self.model