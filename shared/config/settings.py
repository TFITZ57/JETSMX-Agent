"""
Centralized configuration management using Pydantic Settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Google Cloud Platform
    gcp_project_id: str = Field(default="jetsmx-agent")
    gcp_service_account_json_path: str = Field(default="./google-service-account-keys.json")
    
    # Airtable
    airtable_api_key: str = Field(...)
    airtable_base_id: str = Field(...)
    
    # Gmail Configuration
    gmail_user_email: str = Field(default="jobs@jetstreammx.com")
    gmail_watch_topic: str = Field(default="projects/jetsmx-agent/topics/jetsmx-gmail-events")
    
    # Google Calendar
    calendar_id: str = Field(default="primary")
    
    # Google Chat
    google_chat_space_id: Optional[str] = Field(default=None)
    
    # Pub/Sub Topics
    pubsub_topic_airtable: str = Field(default="jetsmx-airtable-events")
    pubsub_topic_gmail: str = Field(default="jetsmx-gmail-events")
    pubsub_topic_drive: str = Field(default="jetsmx-drive-events")
    pubsub_topic_chat: str = Field(default="jetsmx-chat-events")
    
    # Drive Folders
    drive_folder_resumes_incoming: Optional[str] = Field(default=None)
    drive_folder_transcripts_probe: Optional[str] = Field(default=None)
    drive_folder_transcripts_interview: Optional[str] = Field(default=None)
    
    # Environment
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # Cloud Run (for webhooks)
    webhook_secret: Optional[str] = Field(default=None)
    
    # Vertex AI
    vertex_ai_location: str = Field(default="us-central1")


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

