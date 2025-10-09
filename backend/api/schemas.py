import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pydantic import BaseModel, HttpUrl
from typing import Literal

class CaptureRequest(BaseModel):
    source_type: Literal["webpage", "video", "audio", "voicememo", "note"]
    url: HttpUrl

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
