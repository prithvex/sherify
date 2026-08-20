from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class NormalizedWebhookEvent:
    """
    Standardized internal representation of a provider-dispatched webhook event.
    """
    provider: str
    provider_event_id: str
    event_type: str  # e.g. "bounced", "opened", "delivered", "unsupported"
    provider_message_id: Optional[str]
    occurred_at: datetime
    recipient_email: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None


class BaseWebhookVerifier(ABC):
    """
    Abstract interface for provider-specific webhook authentication and HMAC signature verification.
    """

    @abstractmethod
    async def verify_signature(self, raw_body: bytes, headers: Dict[str, str]) -> bool:
        """
        Verify that the incoming HTTP request payload authenticity and signature are valid.
        """
        pass


class BaseWebhookParser(ABC):
    """
    Abstract interface for parsing provider webhook payloads into NormalizedWebhookEvents.
    """

    @abstractmethod
    def parse_event(self, raw_body: bytes, payload_json: Dict[str, Any]) -> NormalizedWebhookEvent:
        """
        Parse raw provider JSON into standardized internal event.
        """
        pass
