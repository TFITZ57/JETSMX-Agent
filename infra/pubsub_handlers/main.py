"""
FastAPI app for handling Pub/Sub push messages.
"""
import base64
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from infra.pubsub_handlers.router import route_event
from shared.logging.logger import setup_logger
from shared.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="JetsMX Pub/Sub Handler",
    description="Processes Pub/Sub events and routes to agents",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Health check."""
    return {"status": "healthy", "service": "jetsmx-pubsub-handler"}


@app.get("/health")
async def health():
    """Health check for Cloud Run."""
    return {"status": "ok"}


@app.post("/pubsub/airtable")
async def handle_airtable_pubsub(request: Request):
    """Handle Airtable events from Pub/Sub."""
    try:
        envelope = await request.json()
        
        # Decode Pub/Sub message
        if 'message' not in envelope:
            return {"status": "ignored", "reason": "No message in envelope"}
        
        message = envelope['message']
        data = base64.b64decode(message['data']).decode('utf-8')
        event_data = json.loads(data)
        
        logger.info(f"Received Airtable Pub/Sub message: {message.get('messageId')}")
        
        # Route event
        result = route_event("airtable", event_data)
        
        return {"status": "processed", "result": result}
        
    except Exception as e:
        logger.error(f"Error processing Airtable Pub/Sub: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pubsub/gmail")
async def handle_gmail_pubsub(request: Request):
    """Handle Gmail events from Pub/Sub."""
    try:
        envelope = await request.json()
        
        if 'message' not in envelope:
            return {"status": "ignored"}
        
        message = envelope['message']
        data = base64.b64decode(message['data']).decode('utf-8')
        event_data = json.loads(data)
        
        logger.info(f"Received Gmail Pub/Sub message: {message.get('messageId')}")
        
        result = route_event("gmail", event_data)
        
        return {"status": "processed", "result": result}
        
    except Exception as e:
        logger.error(f"Error processing Gmail Pub/Sub: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pubsub/drive")
async def handle_drive_pubsub(request: Request):
    """Handle Drive events from Pub/Sub."""
    try:
        envelope = await request.json()
        
        if 'message' not in envelope:
            return {"status": "ignored"}
        
        message = envelope['message']
        data = base64.b64decode(message['data']).decode('utf-8')
        event_data = json.loads(data)
        
        logger.info(f"Received Drive Pub/Sub message: {message.get('messageId')}")
        
        result = route_event("drive", event_data)
        
        return {"status": "processed", "result": result}
        
    except Exception as e:
        logger.error(f"Error processing Drive Pub/Sub: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pubsub/chat")
async def handle_chat_pubsub(request: Request):
    """Handle Chat events from Pub/Sub."""
    try:
        envelope = await request.json()
        
        if 'message' not in envelope:
            return {"status": "ignored"}
        
        message = envelope['message']
        data = base64.b64decode(message['data']).decode('utf-8')
        event_data = json.loads(data)
        
        logger.info(f"Received Chat Pub/Sub message: {message.get('messageId')}")
        
        result = route_event("chat", event_data)
        
        return {"status": "processed", "result": result}
        
    except Exception as e:
        logger.error(f"Error processing Chat Pub/Sub: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)

