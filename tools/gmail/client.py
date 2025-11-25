"""
Gmail API client.
"""
from typing import Optional
from googleapiclient.discovery import build
from shared.auth.google_auth import get_delegated_credentials
from shared.config.settings import get_settings
from shared.config.constants import GMAIL_SCOPES
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class GmailClient:
    """Singleton Gmail API client."""
    
    _instance: Optional['GmailClient'] = None
    _service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._service is None:
            settings = get_settings()
            credentials = get_delegated_credentials(
                user_email=settings.gmail_user_email,
                scopes=GMAIL_SCOPES
            )
            self._service = build('gmail', 'v1', credentials=credentials)
            logger.info(f"Gmail client initialized for {settings.gmail_user_email}")
    
    @property
    def service(self):
        """Get the Gmail service instance."""
        return self._service


def get_gmail_client() -> GmailClient:
    """Get the global Gmail client instance."""
    return GmailClient()

