#!/usr/bin/env python3

"""
Script to create test data for Synapse application
Usage: python scripts/create_test_data.py
"""

import sys
import os
import uuid
from datetime import datetime

# Add backend to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'api'))

from database import SessionLocal
from models import KnowledgeItem

def create_test_data():
    """Create test data for development and testing"""
    db = SessionLocal()
    
    try:
        # Create test knowledge items
        test_items = [
            {
                "id": str(uuid.uuid4()),
                "user_id": "test_user_1",
                "source_type": "webpage",
                "source_url": "https://example.com/article1",
                "status": "ready_for_distillation",
                "title": "Test Article 1",
                "processed_text_content": "This is the content of test article 1. It contains some sample text for testing purposes.",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "test_user_1",
                "source_type": "video",
                "source_url": "https://youtube.com/watch?v=test123",
                "status": "ready_for_distillation",
                "title": "Test Video 1",
                "processed_text_content": "This is the transcript of test video 1. It contains some sample text from the video.",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "test_user_2",
                "source_type": "audio",
                "source_url": "https://example.com/audio1.mp3",
                "status": "ready_for_distillation",
                "title": "Test Audio 1",
                "processed_text_content": "This is the transcript of test audio 1. It contains some sample text from the audio file.",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "test_user_2",
                "source_type": "voicememo",
                "source_url": "https://example.com/voicememo1.mp3",
                "status": "ready_for_distillation",
                "title": "Test Voicememo 1",
                "processed_text_content": "This is the transcript of test voicememo 1. It contains some sample text from the voicememo.",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        # Add test items to database
        for item_data in test_items:
            item = KnowledgeItem(**item_data)
            db.add(item)
        
        # Commit changes
        db.commit()
        
        print(f"✅ Created {len(test_items)} test knowledge items")
        
    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
