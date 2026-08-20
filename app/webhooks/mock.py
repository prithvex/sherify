import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any, Dict
from app.core.config import settings
from app.webhooks.base import BaseWebhookParser, BaseWebhookVerifier, NormalizedWebhookEvent


class MockWebhookVerifier(BaseWebhookVerifier):
    """
    Verifier for mock/test provider webhooks supporting HMAC-SHA256 signature verification.
    """

    async def verify_signature(self, raw_body: bytes, headers: Dict[str, str]) -> bool:
        signature_header = (
            headers.get("x-webhook-signature")
            or headers.get("X-Webhook-Signature")
            or headers.get("x-signature")
        )
        if not signature_header:
            return False

        # Support test bypass token
        if signature_header == "mock-valid-signature":
            return True

        # Verify HMAC-SHA256
        secret = settings.WEBHOOK_SIGNING_SECRET.encode("utf-8")
        expected_signature = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()

        return hmac.compare_digest(signature_header, expected_signature)


class MockWebhookParser(BaseWebhookParser):
    """
    Parser for mock/test provider webhooks.
    """

    def parse_event(self, raw_body: bytes, payload_json: Dict[str, Any]) -> NormalizedWebhookEvent:
        event_id = payload_json.get("event_id") or payload_json.get("id") or "mock-unknown-event-id"
        raw_type = str(payload_json.get("event_type") or payload_json.get("type") or "unknown").lower()

        # Map event type
        if raw_type in ["bounce", "bounced", "hard_bounce", "soft_bounce"]:
            event_type = "bounced"
        elif raw_type in ["open", "opened"]:
            event_type = "opened"
        elif raw_type in ["delivery", "delivered"]:
            event_type = "delivered"
        else:
            event_type = "unsupported"

        message_id = payload_json.get("message_id") or payload_json.get("provider_message_id")
        recipient_email = payload_json.get("email") or payload_json.get("recipient")

        # Parse timestamp
        raw_ts = payload_json.get("timestamp") or payload_json.get("occurred_at")
        if raw_ts:
            try:
                if isinstance(raw_ts, (int, float)):
                    occurred_at = datetime.fromtimestamp(raw_ts, tz=timezone.utc)
                else:
                    occurred_at = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
            except Exception:
                occurred_at = datetime.now(timezone.utc)
        else:
            occurred_at = datetime.now(timezone.utc)

        return NormalizedWebhookEvent(
            provider="mock",
            provider_event_id=event_id,
            event_type=event_type,
            provider_message_id=message_id,
            occurred_at=occurred_at,
            recipient_email=recipient_email,
            raw_payload=payload_json,
        )
