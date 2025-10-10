import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pydantic import BaseModel, Field, field_validator
from typing import Literal
import re

class CaptureRequest(BaseModel):
    source_type: Literal["webpage", "video", "audio", "voicememo", "note"]
    url: str
    
    @field_validator('url')
    def validate_url(cls, v):
        # Check URL length
        if len(v) > 10000:
            raise ValueError('URL length exceeds maximum of 10000 characters')
        # Basic URL validation
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        # Check if it's a valid URL format
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v

class CaptureResponse(BaseModel):
    item_id: str
    status: str = "pending"
    message: str = "Capture request received and queued for processing"
    source_type: str
    source_url: str

class KnowledgeItemBase(BaseModel):
    user_id: str
    processed_text_content: str | None = None
    processed_html_content: str | None = None
    title: str | None = None
    source_url: str | None = None
    author: str | None = None
    published_date: str | None = None
    status: str
    source_type: str
    created_at: str | None = None
    processed_at: str | None = None

class KnowledgeItemCreate(KnowledgeItemBase):
    pass

class KnowledgeItem(KnowledgeItemBase):
    id: str

    class Config:
        orm_mode = True
