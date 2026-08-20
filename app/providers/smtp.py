import asyncio
import email.utils
import logging
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import aiosmtplib
from app.core.config import settings
from app.providers.base import BaseEmailProvider, EmailMessage, EmailResult

logger = logging.getLogger(__name__)


class SMTPProvider(BaseEmailProvider):
    """
    Production-grade asynchronous SMTP Email Provider using aiosmtplib.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        use_ssl: Optional[bool] = None,
        timeout: Optional[int] = None,
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port if port is not None else settings.SMTP_PORT
        self.username = username if username is not None else settings.SMTP_USERNAME
        self.password = password if password is not None else settings.SMTP_PASSWORD
        self.use_tls = use_tls if use_tls is not None else settings.SMTP_USE_TLS
        self.use_ssl = use_ssl if use_ssl is not None else settings.SMTP_USE_SSL
        self.timeout = timeout if timeout is not None else settings.EMAIL_PROVIDER_TIMEOUT_SECONDS

    def _build_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")

        # Sender identity formatting
        from_email = message.from_email or settings.EMAIL_FROM_ADDRESS
        from_name = message.from_name or settings.EMAIL_FROM_NAME
        if from_name:
            msg["From"] = email.utils.formataddr((from_name, from_email))
        else:
            msg["From"] = from_email

        msg["To"] = message.to_email
        msg["Subject"] = message.subject

        reply_to = message.reply_to or settings.EMAIL_REPLY_TO
        if reply_to:
            msg["Reply-To"] = reply_to

        # Provider message ID header for tracking and verification
        provider_msg_id = f"<{uuid.uuid4()}@{self.host}>"
        msg["Message-ID"] = provider_msg_id

        # Plain text part
        if message.text_content:
            msg.attach(MIMEText(message.text_content, "plain", "utf-8"))

        # HTML part
        if message.html_content:
            msg.attach(MIMEText(message.html_content, "html", "utf-8"))

        return msg

    async def send_email(self, message: EmailMessage) -> EmailResult:
        mime_msg = self._build_mime_message(message)
        provider_msg_id = mime_msg["Message-ID"].strip("<>")

        try:
            # If SSL is requested (typically port 465) vs STARTTLS (typically port 587)
            start_tls = self.use_tls and not self.use_ssl

            await aiosmtplib.send(
                mime_msg,
                hostname=self.host,
                port=self.port,
                username=self.username if self.username else None,
                password=self.password if self.password else None,
                use_tls=self.use_ssl,
                start_tls=start_tls,
                timeout=self.timeout,
            )

            logger.info(f"Successfully dispatched email via SMTP to {message.to_email} (MsgID: {provider_msg_id})")
            return EmailResult(
                success=True,
                provider_message_id=provider_msg_id,
                is_transient=False,
            )

        except aiosmtplib.SMTPResponseException as exc:
            code = exc.code
            is_transient = 400 <= code < 500
            error_detail = f"SMTP {code} error: {exc.message}"
            logger.warning(f"SMTP error dispatching to {message.to_email}: {error_detail} (Transient: {is_transient})")
            return EmailResult(
                success=False,
                is_transient=is_transient,
                error_message=error_detail,
            )

        except (
            aiosmtplib.SMTPConnectTimeoutError,
            aiosmtplib.SMTPServerDisconnected,
            aiosmtplib.SMTPConnectError,
            aiosmtplib.SMTPTimeoutError,
            asyncio.TimeoutError,
            TimeoutError,
            ConnectionError,
            OSError,
        ) as exc:
            error_detail = f"SMTP connection/timeout failure: {exc}"
            logger.warning(f"Transient network error sending to {message.to_email}: {error_detail}")
            return EmailResult(
                success=False,
                is_transient=True,
                error_message=error_detail,
            )

        except Exception as exc:
            error_detail = f"Unexpected SMTP failure: {exc}"
            logger.error(f"Permanent error sending to {message.to_email}: {error_detail}", exc_info=True)
            return EmailResult(
                success=False,
                is_transient=False,
                error_message=error_detail,
            )
