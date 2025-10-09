from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Literal
from datetime import datetime
import uuid
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import KnowledgeItem as models_KnowledgeItem, ImageAsset
from schemas import CaptureRequest, CaptureResponse, KnowledgeItemBase, KnowledgeItemCreate, KnowledgeItem as schemas_KnowledgeItem
from database import engine, SessionLocal, Base
from sqlalchemy.orm import Session
from celery import Celery

import json
from functools import wraps

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_execution_time(func):
    """Decorator to log execution time of functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = await func(*args, **kwargs)
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Function {func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize Celery
celery_app = Celery('synapse_api')
celery_app.conf.broker_url = 'redis://localhost:6379/0'
celery_app.conf.result_backend = 'redis://localhost:6379/0'

app = FastAPI(
    title="Synapse API",
    description="API for the Synapse knowledge management system - a platform for capturing, processing, and organizing knowledge from various sources",
    version="1.0.0",
    contact={
        "name": "Synapse Development Team",
        "email": "team@synapse.example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# We'll use the schemas from schemas.py instead of defining them here

@app.get("/health",
         tags=["System"],
         summary="Health check endpoint",
         description="Returns the health status of the API service. Used for monitoring and load balancing.",
         response_description="Health status with timestamp")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/capture", 
          response_model=CaptureResponse, 
          status_code=status.HTTP_202_ACCEPTED,
          tags=["Capture"],
          summary="Capture content from various sources",
          description="""
          Capture content from different sources (webpage, video, audio) for processing.
          This endpoint returns immediately with a 202 Accepted status while the actual processing happens asynchronously in the background.
          The client can use the returned item_id to check the processing status later.
          """,
          response_description="Capture request accepted and queued for processing")
@log_execution_time
async def capture_item(request: CaptureRequest, db: Session = Depends(get_db)):
    """
    Capture endpoint for processing different types of content.
    Returns 202 Accepted immediately while processing happens asynchronously.
    """
    try:
        # Validate request
        if not request.url:
            logger.warning("Capture request received with empty URL")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL is required"
            )
            
        if request.source_type not in ["webpage", "video", "audio", "voicememo"]:
            logger.warning(f"Invalid source_type received: {request.source_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid source_type. Must be 'webpage', 'video', 'audio', or 'voicememo'"
            )

        # Generate a unique item ID
        item_id = str(uuid.uuid4())
        
        # Create a new KnowledgeItem in the database
        db_item = models_KnowledgeItem(
            id=item_id,
            user_id=str(uuid.uuid4()),  # Generate a random UUID for now
            source_url=str(request.url),
            source_type=request.source_type,
            status="pending"
        )
        
        # Add to database
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        # Log the capture request with structured data
        logger.info("Capture request received", extra={
            "item_id": item_id,
            "source_type": request.source_type,
            "url": str(request.url),
            "timestamp": datetime.now().isoformat()
        })
        
        # Enqueue task to Celery/Redis queue
        if request.source_type == "webpage":
            task_name = "tasks.process_webpage"
        elif request.source_type == "voicememo":
            task_name = "tasks.process_voicememo"
        else:  # video or audio
            task_name = "tasks.process_media"
            
        # Send task to Celery
        celery_app.send_task(task_name, args=[item_id])
        
        logger.info(f"Task {task_name} enqueued for item {item_id}")
        
        return CaptureResponse(
            item_id=item_id,
            status="processing",
            message="Capture request received and queued for processing",
            source_type=request.source_type,
            source_url=str(request.url)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the full error with traceback
        logger.error(f"Error processing capture request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/v1/knowledge-items/{item_id}", 
         response_model=schemas_KnowledgeItem,
         tags=["Knowledge Items"],
         summary="Get a specific knowledge item",
         description="Retrieve a specific knowledge item by its unique identifier",
         response_description="The requested knowledge item")
@log_execution_time
async def get_knowledge_item(item_id: str, db: Session = Depends(get_db)):
    """
    Get a specific knowledge item by ID
    """
    try:
        db_item = db.query(models_KnowledgeItem).filter(models_KnowledgeItem.id == item_id).first()
        if db_item is None:
            logger.warning(f"Knowledge item not found: {item_id}")
            raise HTTPException(status_code=404, detail="Knowledge item not found")
            
        logger.info(f"Knowledge item retrieved: {item_id}")
        return db_item
    except HTTPException as he:
        # Re-raise HTTP exceptions (like 404) without wrapping them
        raise he
    except Exception as e:
        logger.error(f"Error retrieving knowledge item {item_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
