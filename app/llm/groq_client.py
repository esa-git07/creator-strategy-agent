import os
import importlib
from dotenv import load_dotenv

# Load environment variables from .env (if present)
load_dotenv()


def _get_client():
    """Create a Groq client using the API key from the environment.

    Raises:
        RuntimeError: If ``GROQ_API_KEY`` is not set.
        ImportError: If the Groq SDK is not installed.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ API key not configured")
    try:
        groq_mod = importlib.import_module("groq")
        Groq = groq_mod.Groq
    except Exception as e:  # pragma: no cover
        raise ImportError("The Groq SDK is required. Install it via 'pip install groq'.") from e
    return Groq(api_key=api_key)


def generate_strategy(prompt: str) -> str:
    """Generate a creator strategy using Groq's ``openai/gpt-oss-120b`` model.

    Args:
        prompt: The natural‑language prompt describing the desired strategy.

    Returns:
        The generated strategy text.

    Raises:
        RuntimeError: If the API key is missing, the API call fails, or the
            response does not contain any content.
    """
    if not prompt:
        raise ValueError("Prompt must be a non‑empty string")

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Failed to generate strategy") from exc

    try:
        content = response.choices[0].message.content  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Empty response from model") from exc

    if not content:
        raise RuntimeError("Empty response from model")
    return content
