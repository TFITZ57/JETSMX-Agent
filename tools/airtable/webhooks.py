"""
Airtable Webhooks API client.

Manages webhook subscriptions using Airtable's Web API.
Docs: https://airtable.com/developers/web/api/webhooks-overview
"""
import hashlib
import hmac
import httpx
from typing import Dict, List, Optional, Any
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class AirtableWebhookClient:
    """Client for Airtable Webhooks API."""
    
    BASE_URL = "https://api.airtable.com/v0"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize webhook client."""
        settings = get_settings()
        self.api_key = api_key or settings.airtable_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_webhook(
        self,
        base_id: str,
        notification_url: str,
        specification: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a webhook subscription.
        
        Args:
            base_id: Airtable base ID
            notification_url: URL to receive webhook notifications
            specification: Optional webhook spec (filters, options)
                Example: {
                    "options": {
                        "filters": {
                            "dataTypes": ["tableData"],
                            "recordChangeScope": "tblXXXXXXXXXXXXXX"
                        }
                    }
                }
        
        Returns:
            Webhook object with id, macSecretBase64, expirationTime
        """
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks"
        
        payload = {
            "notificationUrl": notification_url
        }
        
        if specification:
            payload["specification"] = specification
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                
                webhook = response.json()
                logger.info(
                    f"Created webhook {webhook['id']} for base {base_id}",
                    extra={"extra_fields": {
                        "webhook_id": webhook['id'],
                        "base_id": base_id,
                        "notification_url": notification_url
                    }}
                )
                return webhook
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create webhook: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error creating webhook: {str(e)}")
            raise
    
    def list_webhooks(self, base_id: str) -> List[Dict[str, Any]]:
        """
        List all webhooks for a base.
        
        Args:
            base_id: Airtable base ID
            
        Returns:
            List of webhook objects
        """
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                webhooks = data.get("webhooks", [])
                
                logger.info(f"Found {len(webhooks)} webhooks for base {base_id}")
                return webhooks
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list webhooks: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error listing webhooks: {str(e)}")
            raise
    
    def get_webhook(self, base_id: str, webhook_id: str) -> Dict[str, Any]:
        """
        Get webhook details.
        
        Args:
            base_id: Airtable base ID
            webhook_id: Webhook ID
            
        Returns:
            Webhook object
        """
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks/{webhook_id}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get webhook: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting webhook: {str(e)}")
            raise
    
    def delete_webhook(self, base_id: str, webhook_id: str) -> None:
        """
        Delete a webhook subscription.
        
        Args:
            base_id: Airtable base ID
            webhook_id: Webhook ID to delete
        """
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks/{webhook_id}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.delete(url, headers=self.headers)
                response.raise_for_status()
                
                logger.info(f"Deleted webhook {webhook_id} from base {base_id}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to delete webhook: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error deleting webhook: {str(e)}")
            raise
    
    def enable_notifications(self, base_id: str, webhook_id: str) -> Dict[str, Any]:
        """
        Enable notifications for a webhook.
        
        Must be called after creating webhook to start receiving notifications.
        
        Args:
            base_id: Airtable base ID
            webhook_id: Webhook ID
            
        Returns:
            Updated webhook object
        """
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks/{webhook_id}/enableNotifications"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                # Send empty JSON object as body
                response = client.post(url, json={}, headers=self.headers)
                response.raise_for_status()
                
                webhook = response.json()
                logger.info(f"Enabled notifications for webhook {webhook_id}")
                return webhook
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to enable notifications: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error enabling notifications: {str(e)}")
            raise
    
    def refresh_webhook(self, base_id: str, webhook_id: str) -> Dict[str, Any]:
        """
        Refresh webhook to extend expiration time.
        
        Webhooks expire after 7 days of no activity.
        
        Args:
            base_id: Airtable base ID
            webhook_id: Webhook ID
            
        Returns:
            Updated webhook object with new expiration time
        """
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks/{webhook_id}/refresh"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self.headers)
                response.raise_for_status()
                
                webhook = response.json()
                logger.info(
                    f"Refreshed webhook {webhook_id}, new expiration: {webhook.get('expirationTime')}"
                )
                return webhook
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to refresh webhook: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error refreshing webhook: {str(e)}")
            raise
    
    @staticmethod
    def verify_webhook_signature(
        payload_body: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature using HMAC-SHA256.
        
        Args:
            payload_body: Raw request body bytes
            signature: X-Airtable-Content-MAC header value
            secret: Webhook MAC secret (macSecretBase64 from webhook creation)
            
        Returns:
            True if signature is valid
        """
        try:
            # Compute expected signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload_body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant-time comparison)
            return hmac.compare_digest(signature.lower(), expected_signature.lower())
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    def list_webhook_payloads(
        self,
        base_id: str,
        webhook_id: str,
        cursor: Optional[int] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List recent webhook payloads (for testing/debugging).
        
        Args:
            base_id: Airtable base ID
            webhook_id: Webhook ID
            cursor: Pagination cursor
            limit: Max payloads to return (1-100)
            
        Returns:
            Object with payloads array and might_have_more flag
        """
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks/{webhook_id}/payloads"
        
        params = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list payloads: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error listing payloads: {str(e)}")
            raise


def get_webhook_client() -> AirtableWebhookClient:
    """Get Airtable webhook client instance."""
    return AirtableWebhookClient()

