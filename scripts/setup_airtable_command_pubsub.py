#!/usr/bin/env python3
"""
Set up Pub/Sub topic and subscription for Airtable commands.
"""
import subprocess
import sys
from google.cloud import pubsub_v1
from shared.config.settings import get_settings

settings = get_settings()


def setup_pubsub_topic():
    """Create Pub/Sub topic for Airtable commands."""
    project_id = settings.gcp_project_id
    topic_name = "jetsmx-airtable-commands"
    
    print(f"🚀 Setting up Airtable Commands Pub/Sub infrastructure...")
    print(f"   Project: {project_id}")
    print(f"   Topic: {topic_name}")
    
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)
    
    # Create topic
    try:
        topic = publisher.create_topic(request={"name": topic_path})
        print(f"✓ Created topic: {topic.name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"✓ Topic already exists: {topic_path}")
        else:
            print(f"❌ Failed to create topic: {e}")
            sys.exit(1)
    
    # Create subscription for the pubsub handler
    subscriber = pubsub_v1.SubscriberClient()
    subscription_name = "jetsmx-airtable-commands-sub"
    subscription_path = subscriber.subscription_path(project_id, subscription_name)
    
    try:
        subscription = subscriber.create_subscription(
            request={
                "name": subscription_path,
                "topic": topic_path,
                "ack_deadline_seconds": 300,  # 5 minutes for long-running commands
                "message_retention_duration": {"seconds": 604800},  # 7 days
            }
        )
        print(f"✓ Created subscription: {subscription.name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"✓ Subscription already exists: {subscription_path}")
        else:
            print(f"❌ Failed to create subscription: {e}")
            sys.exit(1)
    
    # Create push subscription to pubsub handler (if deployed)
    push_subscription_name = "jetsmx-airtable-commands-push"
    push_subscription_path = subscriber.subscription_path(project_id, push_subscription_name)
    
    # Get pubsub handler URL
    try:
        result = subprocess.run(
            [
                "gcloud", "run", "services", "describe",
                "jetsmx-pubsub-handler",
                "--region", "us-central1",
                "--format", "value(status.url)"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        handler_url = result.stdout.strip()
        push_endpoint = f"{handler_url}/pubsub/airtable-commands"
        
        print(f"\n📍 Pub/Sub Handler URL: {handler_url}")
        
        try:
            subscription = subscriber.create_subscription(
                request={
                    "name": push_subscription_path,
                    "topic": topic_path,
                    "push_config": {
                        "push_endpoint": push_endpoint,
                    },
                    "ack_deadline_seconds": 300,
                }
            )
            print(f"✓ Created push subscription: {subscription.name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"✓ Push subscription already exists: {push_subscription_path}")
            else:
                print(f"⚠️ Could not create push subscription: {e}")
    except subprocess.CalledProcessError:
        print("⚠️ Pub/Sub handler not deployed yet, skipping push subscription")
    
    print("\n✅ Airtable Commands Pub/Sub setup complete!")
    print(f"\n📬 Topic: {topic_path}")
    print(f"📥 Subscription: {subscription_path}")
    
    print("\n💡 Usage example:")
    print("""
from tools.pubsub.publisher import publish_message

# Send a bulk export command
publish_message(
    topic="jetsmx-airtable-commands",
    message={
        "command_id": "cmd_12345",
        "command_type": "export",
        "table": "Applicants",
        "format": "csv",
        "callback_url": "https://my-service.run.app/export-complete"
    }
)
    """)


if __name__ == "__main__":
    setup_pubsub_topic()

