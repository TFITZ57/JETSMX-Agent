"""
Google Cloud Pub/Sub client.
"""
from typing import Optional
from google.cloud import pubsub_v1
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class PubSubClient:
    """Singleton Pub/Sub client."""
    
    _instance: Optional['PubSubClient'] = None
    _publisher = None
    _subscriber = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._publisher is None:
            settings = get_settings()
            self._publisher = pubsub_v1.PublisherClient()
            self._subscriber = pubsub_v1.SubscriberClient()
            self._project_id = settings.gcp_project_id
            logger.info(f"Pub/Sub client initialized for project {self._project_id}")
    
    @property
    def publisher(self) -> pubsub_v1.PublisherClient:
        """Get the publisher client."""
        return self._publisher
    
    @property
    def subscriber(self) -> pubsub_v1.SubscriberClient:
        """Get the subscriber client."""
        return self._subscriber
    
    @property
    def project_id(self) -> str:
        """Get the project ID."""
        return self._project_id


def get_pubsub_client() -> PubSubClient:
    """Get the global Pub/Sub client instance."""
    return PubSubClient()

