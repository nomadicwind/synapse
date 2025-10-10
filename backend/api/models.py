from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import Base
import uuid

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False)
    processed_text_content = Column(Text, nullable=True)
    processed_html_content = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True, unique=True)  # Ensure each URL is only captured once
    author = Column(Text, nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(30), nullable=False, default='pending')
    source_type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

class ImageAsset(Base):
    __tablename__ = "image_assets"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_item_id = Column(PG_UUID(as_uuid=True), ForeignKey('knowledge_items.id', ondelete='CASCADE'), nullable=False)
    storage_key = Column(Text, nullable=False)
    original_url = Column(Text, nullable=True)
    mime_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
