import uuid
from app.providers.base import BaseEmailProvider, EmailMessage, EmailResult


class MockEmailProvider(BaseEmailProvider):
    """
    Mock Email Provider for local development and integration testing.
    Does not make external network requests.
    Supports deterministic failure simulation based on recipient email patterns.
    """

    async def send_email(self, message: EmailMessage) -> EmailResult:
        email = message.to_email.strip().lower()

        # 1. Simulate Transient Failure (e.g. rate limit / network timeout)
        if email.startswith("transient") or "transient" in message.metadata:
            return EmailResult(
                success=False,
                is_transient=True,
                error_message="Simulated temporary provider timeout or rate limit",
            )

        # 2. Simulate Permanent Failure (e.g. malformed domain / bounce)
        if email.startswith("fail") or email.endswith(".invalid") or "permanent_fail" in message.metadata:
            return EmailResult(
                success=False,
                is_transient=False,
                error_message="Simulated permanent delivery rejection: Mailbox unavailable",
            )

        # 3. Simulate Successful Delivery
        mock_id = f"mock-msg-{uuid.uuid4()}"
        return EmailResult(
            success=True,
            provider_message_id=mock_id,
            is_transient=False,
        )


mock_email_provider = MockEmailProvider()
