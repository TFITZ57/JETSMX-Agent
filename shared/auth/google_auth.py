"""
Google service account authentication helpers.
"""
import json
from typing import List, Optional
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from shared.config.settings import get_settings
from shared.config.constants import ALL_SCOPES
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


_credentials_cache: Optional[service_account.Credentials] = None


def get_credentials(scopes: Optional[List[str]] = None) -> service_account.Credentials:
    """
    Get Google service account credentials with specified scopes.
    
    Args:
        scopes: List of OAuth2 scopes. If None, uses ALL_SCOPES.
        
    Returns:
        Service account credentials
    """
    global _credentials_cache
    
    settings = get_settings()
    scopes = scopes or ALL_SCOPES
    
    # Return cached credentials if valid
    if _credentials_cache and _credentials_cache.valid:
        return _credentials_cache
    
    try:
        # Load service account key file
        with open(settings.gcp_service_account_json_path, 'r') as f:
            service_account_info = json.load(f)
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes
        )
        
        # Refresh if needed
        if not credentials.valid:
            credentials.refresh(Request())
        
        _credentials_cache = credentials
        logger.info("Google service account credentials loaded successfully")
        
        return credentials
        
    except FileNotFoundError:
        logger.error(f"Service account key file not found: {settings.gcp_service_account_json_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in service account key file")
        raise
    except Exception as e:
        logger.error(f"Failed to load credentials: {str(e)}")
        raise


def get_delegated_credentials(
    user_email: str,
    scopes: Optional[List[str]] = None
) -> service_account.Credentials:
    """
    Get credentials with domain-wide delegation for a specific user.
    
    This is required for accessing Gmail, Calendar, etc. on behalf of a user.
    
    Args:
        user_email: Email of the user to impersonate
        scopes: List of OAuth2 scopes
        
    Returns:
        Delegated credentials
    """
    credentials = get_credentials(scopes)
    
    # Create delegated credentials
    delegated_credentials = credentials.with_subject(user_email)
    
    logger.info(f"Created delegated credentials for {user_email}")
    
    return delegated_credentials


def refresh_credentials(credentials: service_account.Credentials) -> None:
    """
    Refresh credentials if expired.
    
    Args:
        credentials: Credentials to refresh
    """
    if not credentials.valid:
        try:
            credentials.refresh(Request())
            logger.info("Credentials refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {str(e)}")
            raise

