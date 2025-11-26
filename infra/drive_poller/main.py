"""
Drive Folder Poller for Cloud Functions/Cloud Run.

Polls the resumes folder for new files and publishes events to Pub/Sub.
This is a workaround for Drive API push notification limitations.
"""
import os
import json
from datetime import datetime, timedelta
from google.cloud import pubsub_v1
from tools.drive.client import get_drive_client
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


# Track processed files (in production, use Firestore or Cloud Storage)
processed_files = set()


def poll_drive_folder(request=None):
    """
    Cloud Function entry point.
    
    Polls the Drive resumes folder for new files and publishes events.
    Can be triggered by Cloud Scheduler every 1-5 minutes.
    """
    try:
        settings = get_settings()
        folder_id = settings.drive_folder_resumes_incoming
        
        if not folder_id:
            logger.error("DRIVE_FOLDER_RESUMES_INCOMING not configured")
            return {"error": "Folder ID not configured"}, 500
        
        logger.info(f"Polling Drive folder: {folder_id}")
        
        # Get files created in last 10 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        cutoff_str = cutoff_time.isoformat() + 'Z'
        
        # Query Drive for recent files
        client = get_drive_client()
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and createdTime > '{cutoff_str}'"
        
        results = client.service.files().list(
            q=query,
            fields="files(id, name, mimeType, createdTime, parents)",
            orderBy="createdTime desc"
        ).execute()
        
        files = results.get('files', [])
        logger.info(f"Found {len(files)} recent files")
        
        if not files:
            return {"status": "no_new_files", "count": 0}, 200
        
        # Publish events for new files
        publisher = pubsub_v1.PublisherClient()
        topic_path = f"projects/{settings.gcp_project_id}/topics/{settings.pubsub_topic_drive}"
        
        published_count = 0
        for file in files:
            file_id = file['id']
            
            # Skip if already processed (simple in-memory check)
            # In production, use Firestore or check Airtable for existing record
            if file_id in processed_files:
                logger.info(f"Skipping already processed file: {file['name']}")
                continue
            
            # Publish event
            event_data = {
                'event_type': 'drive.file.created',
                'file_id': file_id,
                'name': file['name'],
                'mime_type': file.get('mimeType', 'application/pdf'),
                'folder_type': 'resumes',
                'created_time': file.get('createdTime'),
                'parents': file.get('parents', [])
            }
            
            logger.info(f"Publishing event for: {file['name']} ({file_id})")
            
            future = publisher.publish(
                topic_path,
                json.dumps(event_data).encode('utf-8')
            )
            message_id = future.result()
            
            logger.info(f"Published message: {message_id}")
            processed_files.add(file_id)
            published_count += 1
        
        return {
            "status": "success",
            "files_found": len(files),
            "events_published": published_count
        }, 200
        
    except Exception as e:
        logger.error(f"Error polling Drive folder: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500


# For Cloud Run
if __name__ == "__main__":
    from flask import Flask, request
    
    app = Flask(__name__)
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
        result, status_code = poll_drive_folder(request)
        return result, status_code
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

