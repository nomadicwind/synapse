import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging
import os
from datetime import datetime
import subprocess
import requests
from bs4 import BeautifulSoup
from readability import Document
import boto3
from urllib.parse import urlparse
import tempfile
import uuid
from models import KnowledgeItem, ImageAsset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery('synapse_worker')
celery_app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
celery_app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse:synapse@localhost:5432/synapse")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MinIO/S3 setup
s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://localhost:9000'),
    aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
    aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
    region_name='us-east-1'
)
BUCKET_NAME = os.getenv('MINIO_BUCKET', 'synapse')

@celery_app.task(name='tasks.process_webpage')
def process_webpage(item_id):
    """Process a webpage capture request"""
    db = SessionLocal()
    try:
        # Get the item from database
        item = db.query(models.KnowledgeItem).filter(models.KnowledgeItem.id == item_id).first()
        if not item:
            logger.error(f"Item {item_id} not found")
            return

        # Update status to processing
        item.status = 'processing'
        item.processed_at = datetime.now()
        db.commit()

        # Fetch and process the webpage
        response = requests.get(item.source_url, timeout=30)
        response.raise_for_status()

        # Use readability to extract main content
        doc = Document(response.content)
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
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                try:
                    # Download image
                    img_url = src if src.startswith('http') else f"{urlparse(item.source_url).scheme}://{urlparse(item.source_url).netloc}{src}"
                    img_response = requests.get(img_url, timeout=30)
                    
                    if img_response.status_code == 200:
                        # Generate storage key
                        ext = os.path.splitext(src)[1] if '.' in src else '.jpg'
                        storage_key = f"images/{item_id}/{uuid.uuid4()}{ext}"
                        
                        # Upload to MinIO
                        s3_client.put_object(
                            Bucket=BUCKET_NAME,
                            Key=storage_key,
                            Body=img_response.content,
                            ContentType=img_response.headers.get('content-type', 'image/jpeg')
                        )
                        
                        # Create image asset record
                        image_asset = models.ImageAsset(
                            knowledge_item_id=item_id,
                            storage_key=storage_key,
                            original_url=src,
                            mime_type=img_response.headers.get('content-type', 'image/jpeg')
                        )
                        db.add(image_asset)
                        images.append(image_asset)
                        
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
        
        db.commit()
        logger.info(f"Successfully processed webpage {item_id}")
        
    except Exception as e:
        logger.error(f"Error processing webpage {item_id}: {str(e)}")
        if item:
            item.status = 'error'
            db.commit()
    finally:
        db.close()

@celery_app.task(name='tasks.process_media')
def process_media(item_id):
    """Process a media (video/audio) capture request"""
    db = SessionLocal()
    try:
        # Get the item from database
        item = db.query(models.KnowledgeItem).filter(models.KnowledgeItem.id == item_id).first()
        if not item:
            logger.error(f"Item {item_id} not found")
            return

        # Update status to processing
        item.status = 'processing'
        item.processed_at = datetime.now()
        db.commit()

        # Download audio using yt-dlp
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
            
            try:
                # Use yt-dlp to download audio
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
                
                db.commit()
                logger.info(f"Successfully processed media {item_id}")
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
    except Exception as e:
        logger.error(f"Error processing media {item_id}: {str(e)}")
        if item:
            item.status = 'error'
            db.commit()
    finally:
        db.close()
