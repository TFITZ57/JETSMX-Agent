#!/usr/bin/env python3
"""
Process existing resumes in Drive folder.

This script finds all PDF files in the resumes folder and triggers
processing for each one by publishing events to Pub/Sub.
"""
import sys
import time
import json
from datetime import datetime
from google.cloud import pubsub_v1
from tools.drive.files import list_files_in_folder
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def get_existing_resumes():
    """Get all PDF files from the resumes folder."""
    settings = get_settings()
    folder_id = settings.drive_folder_resumes_incoming
    
    if not folder_id:
        logger.error("DRIVE_FOLDER_RESUMES_INCOMING not configured")
        return []
    
    logger.info(f"Listing files in folder: {folder_id}")
    
    try:
        # List all PDF files
        files = list_files_in_folder(folder_id, mime_type='application/pdf')
        logger.info(f"Found {len(files)} PDF files")
        return files
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        return []


def publish_resume_event(file_id, filename):
    """Publish a resume processing event to Pub/Sub."""
    settings = get_settings()
    
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = f"projects/{settings.gcp_project_id}/topics/{settings.pubsub_topic_drive}"
        
        event_data = {
            'event_type': 'drive.file.created',
            'file_id': file_id,
            'name': filename,
            'mime_type': 'application/pdf',
            'folder_type': 'resumes',
            'batch_processed': True,
            'processed_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        future = publisher.publish(
            topic_path,
            json.dumps(event_data).encode('utf-8')
        )
        message_id = future.result()
        
        logger.info(f"Published event for {filename}: {message_id}")
        return message_id
        
    except Exception as e:
        logger.error(f"Failed to publish event for {filename}: {str(e)}")
        return None


def process_batch(files, delay_seconds=2, start_index=0, end_index=None):
    """
    Process a batch of resume files.
    
    Args:
        files: List of file dicts with 'id' and 'name'
        delay_seconds: Delay between each file (to avoid overwhelming the system)
        start_index: Start processing from this index (0-based)
        end_index: Stop before this index (exclusive), None = process all
    """
    if end_index is None:
        end_index = len(files)
    
    files_to_process = files[start_index:end_index]
    total = len(files_to_process)
    
    logger.info(f"Processing {total} files (indexes {start_index} to {end_index-1})")
    
    success_count = 0
    failed_files = []
    
    for i, file_info in enumerate(files_to_process, start=1):
        file_id = file_info.get('id')
        filename = file_info.get('name', 'unknown')
        
        print(f"\n[{i}/{total}] Processing: {filename}")
        print(f"  File ID: {file_id}")
        
        message_id = publish_resume_event(file_id, filename)
        
        if message_id:
            print(f"  ✅ Event published: {message_id}")
            success_count += 1
        else:
            print(f"  ❌ Failed to publish event")
            failed_files.append({'id': file_id, 'name': filename})
        
        # Delay between files to avoid overwhelming the system
        if i < total and delay_seconds > 0:
            print(f"  ⏱️  Waiting {delay_seconds} seconds...")
            time.sleep(delay_seconds)
    
    return success_count, failed_files


def main():
    """Main function."""
    print("=" * 70)
    print("Batch Resume Processor")
    print("=" * 70)
    
    # Parse arguments
    delay_seconds = 2  # Default delay
    start_index = 0
    end_index = None
    
    if len(sys.argv) > 1:
        try:
            delay_seconds = float(sys.argv[1])
        except ValueError:
            print(f"Invalid delay: {sys.argv[1]}, using default: 2 seconds")
    
    if len(sys.argv) > 2:
        try:
            start_index = int(sys.argv[2])
        except ValueError:
            print(f"Invalid start index: {sys.argv[2]}, using default: 0")
    
    if len(sys.argv) > 3:
        try:
            end_index = int(sys.argv[3])
        except ValueError:
            print(f"Invalid end index: {sys.argv[3]}, processing all")
    
    print(f"\n📁 Scanning Drive folder for existing resumes...")
    
    # Get all resumes
    files = get_existing_resumes()
    
    if not files:
        print("\n❌ No resume files found or failed to list folder.")
        return 1
    
    print(f"\n✅ Found {len(files)} resume files")
    print(f"\n⚙️  Settings:")
    print(f"   Delay between files: {delay_seconds} seconds")
    print(f"   Processing range: {start_index} to {end_index if end_index else len(files)}")
    print(f"   Total to process: {(end_index or len(files)) - start_index}")
    
    # Show sample of files
    print(f"\n📄 Files to process:")
    preview_count = min(10, (end_index or len(files)) - start_index)
    for i in range(start_index, start_index + preview_count):
        if i < len(files):
            print(f"   {i+1:3d}. {files[i].get('name', 'unknown')}")
    
    if (end_index or len(files)) - start_index > preview_count:
        remaining = (end_index or len(files)) - start_index - preview_count
        print(f"   ... and {remaining} more files")
    
    # Confirm
    print("\n⚠️  This will trigger the Applicant Analysis Agent for each file.")
    print("   Each resume will be:")
    print("   - Downloaded and parsed")
    print("   - Analyzed by OpenAI")
    print("   - Added to Airtable")
    print("   - ICC PDF generated")
    
    response = input("\n❓ Continue? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("❌ Aborted")
        return 1
    
    # Process files
    print("\n" + "=" * 70)
    print("Processing Resumes")
    print("=" * 70)
    
    start_time = time.time()
    success_count, failed_files = process_batch(
        files,
        delay_seconds=delay_seconds,
        start_index=start_index,
        end_index=end_index
    )
    
    elapsed_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"✅ Successfully published: {success_count}")
    print(f"❌ Failed: {len(failed_files)}")
    print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
    
    if failed_files:
        print(f"\n❌ Failed files:")
        for file_info in failed_files:
            print(f"   - {file_info['name']} ({file_info['id']})")
    
    print("\n📝 Next steps:")
    print("   1. Wait a few minutes for processing to complete")
    print("   2. Check logs:")
    print("      gcloud logging read \"resource.labels.service_name=jetsmx-pubsub-handler\" --limit=50 --project=jetsmx-agent")
    print("   3. Check Airtable for new applicant records")
    
    print("\n💡 Tip: To process in smaller batches, use:")
    print(f"   python {sys.argv[0]} 2 0 10     # Process first 10 files")
    print(f"   python {sys.argv[0]} 2 10 20    # Process files 10-19")
    print(f"   python {sys.argv[0]} 2 20 40    # Process files 20-39")
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        exit(1)

