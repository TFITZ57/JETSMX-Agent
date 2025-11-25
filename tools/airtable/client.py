"""
Base Airtable API client.
"""
from pyairtable import Api
from typing import Optional
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class AirtableClient:
    """Singleton Airtable API client."""
    
    _instance: Optional['AirtableClient'] = None
    _api: Optional[Api] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._api is None:
            settings = get_settings()
            self._api = Api(settings.airtable_api_key)
            self._base_id = settings.airtable_base_id
            logger.info("Airtable client initialized")
    
    @property
    def api(self) -> Api:
        """Get the Airtable API instance."""
        return self._api
    
    @property
    def base_id(self) -> str:
        """Get the Airtable base ID."""
        return self._base_id
    
    def get_table(self, table_name: str):
        """Get a table instance."""
        return self.api.table(self._base_id, table_name)


def get_airtable_client() -> AirtableClient:
    """Get the global Airtable client instance."""
    return AirtableClient()

