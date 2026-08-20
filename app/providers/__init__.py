from app.core.config import settings
from app.providers.base import BaseEmailProvider, EmailMessage, EmailResult
from app.providers.mock import MockEmailProvider, mock_email_provider
from app.providers.smtp import SMTPProvider


def get_email_provider() -> BaseEmailProvider:
    """
    Factory function returning the configured EmailProvider implementation.
    """
    provider_name = settings.EMAIL_PROVIDER.lower()
    if provider_name == "smtp":
        return SMTPProvider()
    if provider_name == "mock":
        return mock_email_provider
    # Default fallback for testing and development
    return mock_email_provider


__all__ = [
    "BaseEmailProvider",
    "EmailMessage",
    "EmailResult",
    "MockEmailProvider",
    "mock_email_provider",
    "SMTPProvider",
    "get_email_provider",
]
