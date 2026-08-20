from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class EmailMessage:
    to_email: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmailResult:
    success: bool
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    is_transient: bool = False


class BaseEmailProvider(ABC):
    """
    Abstract Base Class for all transactional / campaign email providers.
    """

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """
        Send a single email message to the specified recipient.
        """
        pass
