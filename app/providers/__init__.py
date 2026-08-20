from app.core.config import settings
from app.providers.base import BaseEmailProvider, EmailMessage, EmailResult
from app.providers.mock import MockEmailProvider, mock_email_provider


def get_email_provider() -> BaseEmailProvider:
    """
    Factory function returning the configured EmailProvider implementation.
    """
    provider_name = settings.EMAIL_PROVIDER.lower()
    if provider_name == "mock":
        return mock_email_provider
    # Prepared for future providers (e.g. SES, SendGrid, Resend)
    return mock_email_provider


__all__ = [
    "BaseEmailProvider",
    "EmailMessage",
    "EmailResult",
    "MockEmailProvider",
    "mock_email_provider",
    "get_email_provider",
]
