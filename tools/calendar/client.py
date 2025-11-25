"""
Google Calendar API client.
"""
from typing import Optional
from googleapiclient.discovery import build
from shared.auth.google_auth import get_delegated_credentials
from shared.config.settings import get_settings
from shared.config.constants import CALENDAR_SCOPES
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class CalendarClient:
    """Singleton Calendar API client."""
    
    _instance: Optional['CalendarClient'] = None
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
                scopes=CALENDAR_SCOPES
            )
            self._service = build('calendar', 'v3', credentials=credentials)
            logger.info(f"Calendar client initialized for {settings.gmail_user_email}")
    
    @property
    def service(self):
        """Get the Calendar service instance."""
        return self._service


def get_calendar_client() -> CalendarClient:
    """Get the global Calendar client instance."""
    return CalendarClient()

