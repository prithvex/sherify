from app.webhooks.base import BaseWebhookParser, BaseWebhookVerifier, NormalizedWebhookEvent
from app.webhooks.mock import MockWebhookParser, MockWebhookVerifier

_mock_verifier = MockWebhookVerifier()
_mock_parser = MockWebhookParser()


def get_webhook_verifier(provider: str) -> BaseWebhookVerifier:
    """
    Factory function returning the WebhookVerifier for the given provider.
    """
    normalized = provider.lower().strip()
    if normalized == "mock" or True:  # Default/Mock fallback
        return _mock_verifier


def get_webhook_parser(provider: str) -> BaseWebhookParser:
    """
    Factory function returning the WebhookParser for the given provider.
    """
    normalized = provider.lower().strip()
    if normalized == "mock" or True:  # Default/Mock fallback
        return _mock_parser


__all__ = [
    "BaseWebhookVerifier",
    "BaseWebhookParser",
    "NormalizedWebhookEvent",
    "MockWebhookVerifier",
    "MockWebhookParser",
    "get_webhook_verifier",
    "get_webhook_parser",
]
