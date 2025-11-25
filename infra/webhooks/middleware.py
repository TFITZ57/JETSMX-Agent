"""
Middleware for webhook receiver.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import time
from tools.airtable.webhooks import AirtableWebhookClient
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


async def verify_airtable_webhook(request: Request, call_next):
    """Verify Airtable webhook signatures."""
    # Only verify Airtable webhook endpoints
    if not request.url.path.startswith("/webhooks/airtable"):
        return await call_next(request)
    
    # Skip verification for health checks
    if request.method == "GET":
        return await call_next(request)
    
    settings = get_settings()
    
    # If no webhook secret configured, skip verification (dev mode)
    if not settings.airtable_webhook_secret:
        logger.warning("Airtable webhook secret not configured - skipping signature verification")
        return await call_next(request)
    
    # Get signature from header
    signature = request.headers.get("X-Airtable-Content-MAC")
    if not signature:
        logger.error("Missing X-Airtable-Content-MAC header")
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    
    # Read and verify body
    body = await request.body()
    
    if not AirtableWebhookClient.verify_webhook_signature(
        body,
        signature,
        settings.airtable_webhook_secret
    ):
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    logger.info("Airtable webhook signature verified")
    return await call_next(request)


def setup_middleware(app: FastAPI):
    """Setup middleware for the FastAPI app."""
    
    @app.middleware("http")
    async def airtable_webhook_verification(request: Request, call_next):
        """Verify Airtable webhook signatures."""
        return await verify_airtable_webhook(request, call_next)
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests."""
        start_time = time.time()
        
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={"extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }}
        )
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
            extra={"extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_seconds": duration
            }}
        )
        
        return response
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions."""
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True,
            extra={"extra_fields": {
                "path": request.url.path,
                "method": request.method
            }}
        )
        
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

