
"""
llm.py
------
Thin wrapper around an open-source chat model served through
Hugging Face Inference Providers.

Requirements:
    pip install huggingface_hub python-dotenv

Environment variables in .env:
    HF_TOKEN=hf_your_token_here

Optional:
    LLM_MODEL=Qwen/Qwen3-4B-Instruct-2507
    HF_PROVIDER=auto

If the LLM is unavailable, LLMUnavailableError is raised so that
agents.py can use its rule-based fallback.
"""

import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


# ---------------------------------------------------------
# Load environment variables from .env
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DEFAULT_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-120b",
)

DEFAULT_PROVIDER = os.getenv(
    "HF_PROVIDER",
    "auto",
)


# ---------------------------------------------------------
# Custom exception
# ---------------------------------------------------------

class LLMUnavailableError(Exception):
    """Raised when the Hugging Face LLM cannot be used."""


# ---------------------------------------------------------
# LLM Client
# ---------------------------------------------------------

class LLMClient:

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        provider: str = DEFAULT_PROVIDER,
    ):
        self.model = model
        self.provider = provider

        # Read HF_TOKEN from .env / environment
        self.token = os.getenv("HF_TOKEN")

        self._client = None

        # Token is required
        if not self.token:
            return

        try:
            self._client = InferenceClient(
                provider=self.provider,
                api_key=self.token,
            )

        except Exception as exc:
            raise LLMUnavailableError(
                f"Failed to initialize Hugging Face client: {exc}"
            ) from exc

    # -----------------------------------------------------
    # Check whether client is configured
    # -----------------------------------------------------

    @property
    def available(self) -> bool:
        return self._client is not None

    # -----------------------------------------------------
    # Generate response
    # -----------------------------------------------------

    def generate(
        self,
        prompt: str,
        max_tokens: int = 400,
        temperature: float = 0.6,
    ) -> str:

        # -------------------------------------------------
        # Check token/client
        # -------------------------------------------------

        if not self.token:
            raise LLMUnavailableError(
                "HF_TOKEN was not found. "
                "Make sure your .env file contains:\n"
                "HF_TOKEN=hf_your_token_here"
            )

        if not self._client:
            raise LLMUnavailableError(
                "Hugging Face client is not initialized."
            )

        # -------------------------------------------------
        # Call Hugging Face
        # -------------------------------------------------

        try:

            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # -------------------------------------------------
            # Validate response
            # -------------------------------------------------

            if not completion:
                raise LLMUnavailableError(
                    "Hugging Face returned an empty completion."
                )

            if not completion.choices:
                raise LLMUnavailableError(
                    "Hugging Face returned no choices."
                )

            message = completion.choices[0].message

            if not message:
                raise LLMUnavailableError(
                    "Hugging Face returned an empty message."
                )

            content = message.content

            if not content:
                raise LLMUnavailableError(
                    "The model returned an empty response."
                )

            return content.strip()

        # -------------------------------------------------
        # Preserve our own errors
        # -------------------------------------------------

        except LLMUnavailableError:
            raise

        # -------------------------------------------------
        # Convert Hugging Face errors
        # -------------------------------------------------

        except Exception as exc:

            raise LLMUnavailableError(
                f"Hugging Face LLM request failed: {exc}"
            ) from exc