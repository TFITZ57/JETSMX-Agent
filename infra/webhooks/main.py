"""
FastAPI webhook receiver for external events.
"""
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from infra.webhooks.routes import airtable, gmail, drive, chat, scheduler
from infra.webhooks.middleware import setup_middleware
from shared.logging.logger import setup_logger
from shared.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="JetsMX Webhook Receiver",
    description="Receives webhooks from Airtable, Gmail, Drive, and Chat. Provides HTTP endpoint for Applicant Analysis Agent.",
    version="1.0.0"
)

# Setup middleware (logging, auth)
setup_middleware(app)

# Include routers
app.include_router(airtable.router, prefix="/webhooks/airtable", tags=["airtable"])
app.include_router(gmail.router, prefix="/webhooks/gmail", tags=["gmail"])
app.include_router(drive.router, prefix="/webhooks/drive", tags=["drive"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(scheduler.router, prefix="/internal/scheduler", tags=["scheduler"])

# Try to import and register agent router
try:
    from infra.webhooks.routes import agent
    app.include_router(agent.router, prefix="/agent", tags=["agent"])
    logger.info("✓ Agent router registered successfully")
except Exception as e:
    logger.error(f"✗ Failed to register agent router: {str(e)}", exc_info=True)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "jetsmx-webhooks"}


@app.get("/health")
async def health():
    """Health check for Cloud Run."""
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

