"""
Webhook signature verification helpers.
"""
import hmac
import hashlib
from typing import Optional
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: Optional[str] = None
) -> bool:
    """
    Verify HMAC signature for incoming webhooks.
    
    Args:
        payload: Raw request body bytes
        signature: Signature from request header
        secret: Webhook secret (uses settings if not provided)
        
    Returns:
        True if signature is valid
    """
    if secret is None:
        settings = get_settings()
        secret = settings.webhook_secret
    
    if not secret:
        logger.warning("No webhook secret configured, skipping verification")
        return True
    
    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures (constant-time comparison)
    is_valid = hmac.compare_digest(signature, expected_signature)
    
    if not is_valid:
        logger.warning("Invalid webhook signature")
    
    return is_valid


def verify_airtable_webhook(payload: bytes, signature: str) -> bool:
    """Verify Airtable webhook signature."""
    return verify_webhook_signature(payload, signature)


def verify_gmail_notification(payload: bytes, signature: str) -> bool:
    """Verify Gmail push notification signature."""
    return verify_webhook_signature(payload, signature)

