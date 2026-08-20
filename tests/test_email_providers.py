import pytest
from unittest.mock import AsyncMock, patch
import aiosmtplib
from app.providers.base import EmailMessage
from app.providers.mock import MockEmailProvider
from app.providers.smtp import SMTPProvider


@pytest.mark.asyncio
async def test_mock_provider_scenarios():
    provider = MockEmailProvider()

    # 1. Successful send
    msg_success = EmailMessage(
        to_email="user@example.com",
        subject="Hello",
        html_content="<p>Test</p>",
    )
    res_success = await provider.send_email(msg_success)
    assert res_success.success is True
    assert res_success.provider_message_id is not None
    assert res_success.is_transient is False

    # 2. Transient error simulation
    msg_transient = EmailMessage(
        to_email="transient.user@example.com",
        subject="Hello",
        html_content="<p>Test</p>",
    )
    res_transient = await provider.send_email(msg_transient)
    assert res_transient.success is False
    assert res_transient.is_transient is True

    # 3. Permanent error simulation
    msg_fail = EmailMessage(
        to_email="fail.user@example.com",
        subject="Hello",
        html_content="<p>Test</p>",
    )
    res_fail = await provider.send_email(msg_fail)
    assert res_fail.success is False
    assert res_fail.is_transient is False


@pytest.mark.asyncio
async def test_smtp_provider_mime_and_sender_construction():
    provider = SMTPProvider(
        host="smtp.example.com",
        port=587,
        username="testuser",
        password="testpassword",
    )

    msg = EmailMessage(
        to_email="recipient@example.com",
        subject="Exclusive Announcement",
        html_content="<h1>Welcome</h1>",
        text_content="Welcome",
        from_name="Acme Marketing",
        from_email="news@acme.com",
        reply_to="support@acme.com",
    )

    mime = provider._build_mime_message(msg)
    assert mime["To"] == "recipient@example.com"
    assert mime["Subject"] == "Exclusive Announcement"
    assert "Acme Marketing <news@acme.com>" in mime["From"]
    assert mime["Reply-To"] == "support@acme.com"
    assert mime["Message-ID"] is not None


@pytest.mark.asyncio
async def test_smtp_provider_success_dispatch():
    provider = SMTPProvider(host="smtp.example.com")
    msg = EmailMessage(
        to_email="user@example.com",
        subject="Test Subject",
        html_content="<p>Body</p>",
    )

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = ({}, "250 2.0.0 OK")
        result = await provider.send_email(msg)

        assert result.success is True
        assert result.provider_message_id is not None
        assert result.is_transient is False
        mock_send.assert_awaited_once()


@pytest.mark.asyncio
async def test_smtp_provider_transient_error_classification():
    provider = SMTPProvider(host="smtp.example.com")
    msg = EmailMessage(
        to_email="user@example.com",
        subject="Test Subject",
        html_content="<p>Body</p>",
    )

    # 421 Service not available (Transient)
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = aiosmtplib.SMTPResponseException(421, "Service not available, closing channel")
        result = await provider.send_email(msg)

        assert result.success is False
        assert result.is_transient is True
        assert "421" in result.error_message


@pytest.mark.asyncio
async def test_smtp_provider_permanent_error_classification():
    provider = SMTPProvider(host="smtp.example.com")
    msg = EmailMessage(
        to_email="invalid@example.com",
        subject="Test Subject",
        html_content="<p>Body</p>",
    )

    # 550 Mailbox unavailable (Permanent)
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = aiosmtplib.SMTPResponseException(550, "User unknown")
        result = await provider.send_email(msg)

        assert result.success is False
        assert result.is_transient is False
        assert "550" in result.error_message


@pytest.mark.asyncio
async def test_smtp_provider_timeout_classification():
    provider = SMTPProvider(host="smtp.example.com")
    msg = EmailMessage(
        to_email="user@example.com",
        subject="Test Subject",
        html_content="<p>Body</p>",
    )

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = aiosmtplib.SMTPTimeoutError("Connection timed out")
        result = await provider.send_email(msg)

        assert result.success is False
        assert result.is_transient is True
        assert "timeout" in result.error_message.lower()
