"""
Simple web interface for uploading resumes.
Uploads to Drive and automatically triggers agent processing.
"""
import os
import json
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from google.cloud import pubsub_v1
from tools.drive.files import upload_file
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

app = Flask(__name__)
logger = setup_logger(__name__)
settings = get_settings()


@app.route('/')
def index():
    """Render upload form."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_resume():
    """
    Handle resume upload.
    
    1. Upload file to Drive
    2. Publish event to Pub/Sub
    3. Return success with tracking info
    """
    try:
        # Check if file is present
        if 'resume' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        logger.info(f"Uploading resume: {file.filename}")
        
        # Read file content
        file_content = file.read()
        
        # Upload to Drive
        folder_id = settings.drive_folder_resumes_incoming
        if not folder_id:
            return jsonify({'error': 'Drive folder not configured'}), 500
        
        file_id = upload_file(
            name=file.filename,
            content=file_content,
            mime_type='application/pdf',
            parent_folder_id=folder_id
        )
        
        if not file_id:
            return jsonify({'error': 'Failed to upload to Drive'}), 500
        
        logger.info(f"File uploaded to Drive: {file_id}")
        
        # Publish event to Pub/Sub
        publisher = pubsub_v1.PublisherClient()
        topic_path = f"projects/{settings.gcp_project_id}/topics/{settings.pubsub_topic_drive}"
        
        event_data = {
            'event_type': 'drive.file.created',
            'file_id': file_id,
            'name': file.filename,
            'mime_type': 'application/pdf',
            'folder_type': 'resumes',
            'uploaded_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        future = publisher.publish(
            topic_path,
            json.dumps(event_data).encode('utf-8')
        )
        message_id = future.result()
        
        logger.info(f"Published event to Pub/Sub: {message_id}")
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'message_id': message_id,
            'message': 'Resume uploaded successfully! Processing has started automatically.'
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

