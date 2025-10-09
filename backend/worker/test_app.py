import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import process_webpage, process_media
import uuid

@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = MagicMock()
    yield session

@pytest.fixture
def mock_requests():
    """Mock requests for testing"""
    with patch('app.requests') as mock_req:
        mock_response = MagicMock()
        mock_response.content = b"<html><title>Test</title><body><p>Test content</p></body></html>"
        mock_response.text = "<html><title>Test</title><body><p>Test content</p></body></html>"
        mock_response.status_code = 200
        mock_req.get.return_value = mock_response
        yield mock_req

@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing"""
    with patch('app.s3_client') as mock_s3:
        yield mock_s3

def test_process_webpage_success(mock_db_session, mock_requests, mock_s3_client):
    """Test successful webpage processing"""
    item_id = str(uuid.uuid4())
    
    # Mock database query
    mock_item = MagicMock()
    mock_item.id = item_id
    mock_item.source_url = "https://example.com"
    mock_item.status = "processing"
    
    with patch('app.SessionLocal', return_value=mock_db_session):
        mock_db_session.query().filter().first.return_value = mock_item
        
        result = process_webpage(item_id)
        
    assert result["status"] == "success"
    assert result["item_id"] == item_id
    assert mock_item.status == "ready_for_distillation"
    mock_db_session.commit.assert_called_once()

def test_process_webpage_not_found(mock_db_session):
    """Test webpage processing when item not found"""
    item_id = str(uuid.uuid4())
    
    with patch('app.SessionLocal', return_value=mock_db_session):
        mock_db_session.query().filter().first.return_value = None
        
        result = process_webpage(item_id)
        
    assert result["status"] == "error"
    assert result["item_id"] == item_id
    assert "not found" in result["message"]

def test_process_webpage_error(mock_db_session, mock_requests):
    """Test webpage processing with error"""
    item_id = str(uuid.uuid4())
    
    mock_item = MagicMock()
    mock_item.id = item_id
    mock_item.source_url = "https://example.com"
    mock_item.status = "processing"
    
    # Make requests.get raise an exception
    mock_requests.get.side_effect = Exception("Network error")
    
    with patch('app.SessionLocal', return_value=mock_db_session):
        mock_db_session.query().filter().first.return_value = mock_item
        
        result = process_webpage(item_id)
        
    assert result["status"] == "error"
    assert result["item_id"] == item_id
    assert mock_item.status == "error"
    mock_db_session.commit.assert_called_once()

def test_process_media_success(mock_db_session):
    """Test successful media processing"""
    item_id = str(uuid.uuid4())
    
    mock_item = MagicMock()
    mock_item.id = item_id
    mock_item.source_url = "https://youtube.com/watch?v=123"
    mock_item.status = "processing"
    
    with patch('app.SessionLocal', return_value=mock_db_session):
        with patch('app.subprocess.run') as mock_subprocess:
            with patch('app.requests.post') as mock_post:
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stderr = ""
                
                mock_response = MagicMock()
                mock_response.json.return_value = {"transcript": "Test transcript"}
                mock_response.status_code = 200
                mock_post.return_value = mock_response
                
                mock_db_session.query().filter().first.return_value = mock_item
                
                result = process_media(item_id, "video")
                
    assert result["status"] == "success"
    assert result["item_id"] == item_id
    assert mock_item.status == "ready_for_distillation"
    mock_db_session.commit.assert_called_once()

def test_process_media_not_found(mock_db_session):
    """Test media processing when item not found"""
    item_id = str(uuid.uuid4())
    
    with patch('app.SessionLocal', return_value=mock_db_session):
        mock_db_session.query().filter().first.return_value = None
        
        result = process_media(item_id, "video")
        
    assert result["status"] == "error"
    assert result["item_id"] == item_id
    assert "not found" in result["message"]

def test_process_media_error(mock_db_session):
    """Test media processing with error"""
    item_id = str(uuid.uuid4())
    
    mock_item = MagicMock()
    mock_item.id = item_id
    mock_item.source_url = "https://youtube.com/watch?v=123"
    mock_item.status = "processing"
    
    with patch('app.SessionLocal', return_value=mock_db_session):
        with patch('app.subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = Exception("yt-dlp failed")
            
            mock_db_session.query().filter().first.return_value = mock_item
            
            result = process_media(item_id, "video")
            
    assert result["status"] == "error"
    assert result["item_id"] == item_id
    assert mock_item.status == "error"
    mock_db_session.commit.assert_called_once()
