"""
Hindsight persistent memory client integration.

This module provides a minimal wrapper around the official hindsight-client SDK,
handling configuration, connection management, memory retention (write), and
memory recall (read) while keeping credentials secure.
"""

import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from hindsight_client import Hindsight


class HindsightMemoryError(Exception):
    """Base exception for Hindsight memory operations."""
    pass


class HindsightConfigurationError(HindsightMemoryError):
    """Raised when required Hindsight configuration or credentials are missing."""
    pass


class HindsightConnectionError(HindsightMemoryError):
    """Raised when connection or authentication to Hindsight fails."""
    pass


class HindsightMemoryClient:
    """
    Client wrapper for Hindsight persistent memory service.
    Responsible for connecting to Hindsight and providing write (retain)
    and read (recall) operations.
    """

    DEFAULT_BASE_URL: str = "https://api.hindsight.vectorize.io"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        load_dotenv()

        self._api_key = api_key or os.getenv("HINDSIGHT_API_KEY")
        raw_url = base_url or os.getenv("HINDSIGHT_BASE_URL") or self.DEFAULT_BASE_URL
        self._base_url = raw_url.rstrip("/")
        self._timeout = timeout

        # Local endpoints (e.g. docker container) do not require an API key,
        # but cloud endpoints require HINDSIGHT_API_KEY to authenticate.
        is_local = "localhost" in self._base_url or "127.0.0.1" in self._base_url
        if not is_local and not self._api_key:
            raise HindsightConfigurationError(
                "HINDSIGHT_API_KEY is not configured. Please set HINDSIGHT_API_KEY in your .env file."
            )

        try:
            self._client = Hindsight(
                base_url=self._base_url,
                api_key=self._api_key,
                timeout=self._timeout,
            )
        except Exception as e:
            raise HindsightConnectionError(
                f"Failed to initialize Hindsight client: {self._sanitize_message(str(e))}"
            ) from e

    @property
    def base_url(self) -> str:
        """Returns the configured base URL."""
        return self._base_url

    def _sanitize_message(self, message: str) -> str:
        """Ensures the API key is never exposed in error messages or logs."""
        if self._api_key and self._api_key in message:
            return message.replace(self._api_key, "[REDACTED]")
        return message

    def __repr__(self) -> str:
        key_status = "[SET]" if self._api_key else "[NOT SET]"
        return f"<HindsightMemoryClient base_url='{self._base_url}' api_key={key_status}>"

    def retain_memory(
        self,
        bank_id: str,
        content: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Store (write) a memory into a specific memory bank.

        Parameters:
            bank_id: The identifier for the memory bank (e.g. creator ID).
            content: The text content of the experience, insight, or event.
            context: Optional contextual notes or background.
            metadata: Optional key-value dictionary of metadata strings.

        Returns:
            Dict[str, Any]: Summary of the retain operation.

        Raises:
            ValueError: If bank_id or content is empty.
            HindsightMemoryError: If the retention request fails.
        """
        clean_bank_id = (bank_id or "").strip()
        clean_content = (content or "").strip()

        if not clean_bank_id:
            raise ValueError("bank_id must be a non-empty string.")
        if not clean_content:
            raise ValueError("content must be a non-empty string.")

        try:
            response = self._client.retain(
                bank_id=clean_bank_id,
                content=clean_content,
                context=context.strip() if context else None,
                metadata=metadata,
            )
            return {
                "success": getattr(response, "success", True),
                "bank_id": getattr(response, "bank_id", clean_bank_id),
                "items_count": getattr(response, "items_count", 1),
                "operation_id": getattr(response, "operation_id", None),
            }
        except Exception as e:
            safe_error = self._sanitize_message(str(e))
            raise HindsightMemoryError(
                f"Failed to retain memory in Hindsight: {safe_error}"
            ) from e

    def recall_memories(
        self,
        bank_id: str,
        query: str,
        max_tokens: int = 4096,
    ) -> List[Dict[str, Any]]:
        """
        Query (read) relevant memories from a specific memory bank.

        Parameters:
            bank_id: The identifier for the memory bank to query.
            query: The search query or question.
            max_tokens: Token budget for recalled memories.

        Returns:
            List[Dict[str, Any]]: List of retrieved memories containing id, text, etc.

        Raises:
            ValueError: If bank_id or query is empty.
            HindsightMemoryError: If the recall request fails.
        """
        clean_bank_id = (bank_id or "").strip()
        clean_query = (query or "").strip()

        if not clean_bank_id:
            raise ValueError("bank_id must be a non-empty string.")
        if not clean_query:
            raise ValueError("query must be a non-empty string.")

        try:
            response = self._client.recall(
                bank_id=clean_bank_id,
                query=clean_query,
                max_tokens=max_tokens,
            )
            raw_results = getattr(response, "results", []) or []
            results: List[Dict[str, Any]] = []
            for item in raw_results:
                results.append({
                    "id": getattr(item, "id", None),
                    "text": getattr(item, "text", ""),
                    "type": getattr(item, "type", None),
                    "context": getattr(item, "context", None),
                    "metadata": getattr(item, "metadata", None),
                    "scores": getattr(item, "scores", None),
                })
            return results
        except Exception as e:
            safe_error = self._sanitize_message(str(e))
            raise HindsightMemoryError(
                f"Failed to recall memories from Hindsight: {safe_error}"
            ) from e


def get_hindsight_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> HindsightMemoryClient:
    """
    Factory helper function to obtain a configured HindsightMemoryClient.
    """
    return HindsightMemoryClient(api_key=api_key, base_url=base_url)
