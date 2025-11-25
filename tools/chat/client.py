"""
Google Chat API client.
"""
from typing import Optional
from googleapiclient.discovery import build
from shared.auth.google_auth import get_credentials
from shared.config.constants import CHAT_SCOPES
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class ChatClient:
    """Singleton Chat API client."""
    
    _instance: Optional['ChatClient'] = None
    _service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._service is None:
            credentials = get_credentials(scopes=CHAT_SCOPES)
            self._service = build('chat', 'v1', credentials=credentials)
            logger.info("Chat client initialized")
    
    @property
    def service(self):
        """Get the Chat service instance."""
        return self._service


def get_chat_client() -> ChatClient:
    """Get the global Chat client instance."""
    return ChatClient()

