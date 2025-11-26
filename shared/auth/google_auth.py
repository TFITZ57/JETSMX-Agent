"""
Google service account authentication helpers.
"""
import json
import os
from typing import List, Optional
from google.oauth2 import service_account
from google.auth import default
from google.auth.transport.requests import Request
from shared.config.settings import get_settings
from shared.config.constants import ALL_SCOPES
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


_credentials_cache: Optional[service_account.Credentials] = None


def get_credentials(scopes: Optional[List[str]] = None) -> service_account.Credentials:
    """
    Get Google service account credentials with specified scopes.
    
    In Cloud Run or other managed environments, uses Application Default Credentials.
    Locally, loads from service account key file.
    
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
    
    # Try to load from file first (for local development)
    sa_file_path = settings.gcp_service_account_json_path
    logger.info(f"Attempting to load credentials. File path: {sa_file_path}, exists: {os.path.exists(sa_file_path)}")
    
    if os.path.exists(sa_file_path):
        try:
            logger.info(f"Loading credentials from file: {sa_file_path}")
            with open(sa_file_path, 'r') as f:
                service_account_info = json.load(f)
            
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=scopes
            )
            
            if not credentials.valid:
                credentials.refresh(Request())
            
            _credentials_cache = credentials
            logger.info("Google service account credentials loaded from file successfully")
            return credentials
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse service account file: {e}")
    else:
        logger.info(f"Service account file not found at {sa_file_path}, using Application Default Credentials")
    
    # Fallback to Application Default Credentials (for Cloud Run, etc.)
    try:
        logger.info("Attempting to use Application Default Credentials (ADC)")
        credentials, project = default(scopes=scopes)
        
        if not credentials.valid:
            credentials.refresh(Request())
        
        _credentials_cache = credentials
        logger.info(f"Application Default Credentials loaded successfully (project: {project})")
        return credentials
        
    except Exception as e:
        logger.error(f"Failed to get any credentials: {e}", exc_info=True)
        raise RuntimeError(f"Could not load credentials: {e}")
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
    settings = get_settings()
    scopes = scopes or ALL_SCOPES
    
    # For delegated credentials, we MUST use a service account key file
    # ADC (Application Default Credentials) doesn't support with_subject()
    sa_file_path = settings.gcp_service_account_json_path
    
    if not os.path.exists(sa_file_path):
        raise RuntimeError(
            f"Service account key file required for domain-wide delegation not found at {sa_file_path}. "
            "In Cloud Run, mount the key from Secret Manager or set GCP_SERVICE_ACCOUNT_JSON_PATH."
        )
    
    try:
        logger.info(f"Loading service account for delegation from {sa_file_path}")
        with open(sa_file_path, 'r') as f:
            service_account_info = json.load(f)
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes
        )
        
        # Create delegated credentials
        delegated_credentials = credentials.with_subject(user_email)
        
        logger.info(f"Created delegated credentials for {user_email}")
        
        return delegated_credentials
        
    except Exception as e:
        logger.error(f"Failed to create delegated credentials: {e}", exc_info=True)
        raise RuntimeError(f"Could not create delegated credentials for {user_email}: {e}")


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

