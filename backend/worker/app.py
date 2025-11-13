import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from celery import Celery
import logging
from typing import Dict, Any
import uuid
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import subprocess
import requests
from bs4 import BeautifulSoup
from readability import Document
import shutil
from urllib.parse import urlparse
import tempfile

# Import models from backend/api
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from api.models import KnowledgeItem, ImageAsset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse:synapse@localhost:5432/synapse")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Local file storage setup
STORAGE_ROOT = os.getenv('STORAGE_ROOT', '/Users/xyw/Repos/synapse/storage')
os.makedirs(STORAGE_ROOT, exist_ok=True)

# Initialize Celery app
celery_app = Celery('synapse_worker')

# Configure Celery
celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
)

@celery_app.task(name='tasks.process_webpage')
def process_webpage(item_id: str) -> Dict[str, Any]:
    """
    Process a webpage capture request.
    This task will fetch the page, extract content, and store it.
    """
    db = SessionLocal()
    try:
        # Get the item from database
        item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
        if not item:
            logger.error(f"Item {item_id} not found")
            return {"status": "error", "item_id": item_id, "message": "Item not found"}

        # Update status to processing
        item.status = 'processing'
        item.processed_at = datetime.now()
        item.last_error = None
        # Don't commit yet, wait until the end

        # Fetch and process the webpage
        response = requests.get(item.source_url, timeout=30)
        response.raise_for_status()

        # Decode content to string for readability
        content_str = response.content.decode('utf-8', errors='ignore')
        
        # Use readability to extract main content
        doc = Document(content_str)
        title = doc.title()
        content = doc.summary()

        # Parse HTML for image extraction
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract metadata
        author_meta = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', attrs={'property': 'article:author'})
        author = author_meta.get('content') if author_meta else None

        date_meta = soup.find('meta', attrs={'property': 'article:published_time'}) or soup.find('meta', attrs={'name': 'date'})
        published_date = date_meta.get('content') if date_meta else None

        # Process images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                try:
                    # Download image
                    img_url = src if src.startswith('http') else f"{urlparse(item.source_url).scheme}://{urlparse(item.source_url).netloc}{src}"
                    img_response = requests.get(img_url, timeout=30)
                    
                    if img_response.status_code == 200:
                        # Generate storage path
                        ext = os.path.splitext(src)[1] if '.' in src else '.jpg'
                        storage_key = f"images/{item_id}/{uuid.uuid4()}{ext}"
                        storage_path = os.path.join(STORAGE_ROOT, storage_key)
                        
                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
                        
                        # Save image to local storage
                        with open(storage_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        # Create image asset record
                        image_asset = ImageAsset(
                            knowledge_item_id=item_id,
                            storage_key=storage_key,
                            original_url=src,
                            mime_type=img_response.headers.get('content-type', 'image/jpeg')
                        )
                        db.add(image_asset)
                        
                except Exception as e:
                    logger.error(f"Error processing image {src}: {str(e)}")
                    continue

        # Update item with processed content
        item.title = title
        item.processed_text_content = BeautifulSoup(content, 'html.parser').get_text()
        item.processed_html_content = content
        item.author = author
        item.published_date = published_date if published_date else None
        item.status = 'ready_for_distillation'
        item.last_error = None
        
        # Commit all changes at once
        db.commit()
        logger.info(f"Successfully processed webpage {item_id}")
        
        return {
            "status": "success",
            "item_id": item_id,
            "message": "Webpage processing completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error processing webpage for item {item_id}: {str(e)}")
        if 'item' in locals() and item:
            item.status = 'error'
            item.last_error = str(e)
            db.commit()  # Commit the error status
        return {
            "status": "error",
            "item_id": item_id,
            "message": f"Error processing webpage: {str(e)}"
        }
    finally:
        db.close()

@celery_app.task(name='tasks.process_media')
def process_media(item_id: str, source_type: str) -> Dict[str, Any]:
    """
    Process a video or audio capture request.
    This task will download the audio stream and transcribe it.
    """
    db = SessionLocal()
    temp_path = None
    try:
        # Get the item from database
        item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
        if not item:
            logger.error(f"Item {item_id} not found")
            return {"status": "error", "item_id": item_id, "message": "Item not found"}

        # Update status to processing
        item.status = 'processing'
        item.processed_at = datetime.now()
        item.last_error = None
        # Don't commit yet, wait until the end

        # Download audio using yt-dlp
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
            
            cmd = [
                'yt-dlp',
                '-x',  # Extract audio
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '-o', temp_path,
                item.source_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"yt-dlp failed: {result.stderr}")

            # Send to STT service
            stt_url = os.getenv('STT_SERVICE_URL', 'http://localhost:5000/transcribe')
            
            with open(temp_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                response = requests.post(stt_url, files=files, timeout=300)
                response.raise_for_status()
                
                transcript = response.json().get('transcript', '')

            # Update item with transcript
            item.processed_text_content = transcript
            item.status = 'ready_for_distillation'
            item.last_error = None
            
            # Commit all changes at once
            db.commit()
            logger.info(f"Successfully processed media {item_id}")
            
            return {
                "status": "success",
                "item_id": item_id,
                "message": f"{source_type.capitalize()} processing completed successfully"
            }
            
    except Exception as e:
        logger.error(f"Error processing media for item {item_id}: {str(e)}")
        if 'item' in locals() and item:
            item.status = 'error'
            item.last_error = str(e)
            db.commit()
        return {
            "status": "error",
            "item_id": item_id,
            "message": f"Error processing media: {str(e)}"
        }
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        db.close()


@celery_app.task(name='tasks.process_voicememo')
def process_voicememo(item_id: str) -> Dict[str, Any]:
    """
    Process a voice memo capture request.
    This task will transcribe the provided audio data.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting voice memo processing for item: {item_id}")
        
        # Get the item from database
        item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
        if not item:
            logger.error(f"Item {item_id} not found")
            return {"status": "error", "item_id": item_id, "message": "Item not found"}

        # Update status to processing
        item.status = 'processing'
        item.processed_at = datetime.now()
        item.last_error = None

        # TODO: Implement actual voice memo processing logic
        # 1. Receive audio data (from database or direct upload)
        # 2. Make HTTP request to STT service with audio file
        # 3. Receive and process transcript
        # 4. Update database record with transcript and status
        
        # For now, simulate successful processing
        item.processed_text_content = "Voice memo transcription placeholder"
        item.status = 'ready_for_distillation'
        item.last_error = None
        db.commit()
        
        logger.info(f"Completed voice memo processing for item: {item_id}")
        
        return {
            "status": "success",
            "item_id": item_id,
            "message": "Voice memo processing completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error processing voice memo for item {item_id}: {str(e)}")
        if 'item' in locals() and item:
            item.status = 'error'
            item.last_error = str(e)
            db.commit()
        return {
            "status": "error",
            "item_id": item_id,
            "message": f"Error processing voice memo: {str(e)}"
        }
    finally:
        db.close()

# Health check function
def health_check() -> Dict[str, Any]:
    """Simple health check for the worker service"""
    return {
        "status": "healthy",
        "worker_id": str(uuid.uuid4()),
        "tasks": [
            "tasks.process_webpage",
            "tasks.process_media",
            "tasks.process_voicememo"
        ]
    }
