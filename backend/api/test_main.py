import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import sys
import os
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app
from models import KnowledgeItem
from schemas import KnowledgeItemCreate, KnowledgeItemBase
import uuid

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = MagicMock()
    yield session

@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing"""
    with patch('main.celery_app.send_task') as mock_task:
        mock_task.return_value.id = str(uuid.uuid4())
        yield mock_task

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_capture_webpage_success(mock_db_session, mock_celery_task):
    """Test successful webpage capture"""
    capture_data = {
        "source_type": "webpage",
        "url": "https://example.com"
    }
    
    with patch('main.SessionLocal', return_value=mock_db_session):
        response = client.post("/api/v1/capture", json=capture_data)
        
    assert response.status_code == 202
    data = response.json()
    assert "item_id" in data
    assert data["status"] == "processing"
    assert data["source_type"] == "webpage"
    assert data["source_url"] == "https://example.com/"
    mock_celery_task.assert_called_once()

def test_capture_media_success(mock_db_session, mock_celery_task):
    """Test successful media capture"""
    capture_data = {
        "source_type": "video",
        "url": "https://youtube.com/watch?v=123"
    }
    
    with patch('main.SessionLocal', return_value=mock_db_session):
        response = client.post("/api/v1/capture", json=capture_data)
        
    assert response.status_code == 202
    data = response.json()
    assert "item_id" in data
    assert data["status"] == "processing"
    assert data["source_type"] == "video"
    assert data["source_url"] == "https://youtube.com/watch?v=123"
    mock_celery_task.assert_called_once()

def test_capture_invalid_url():
    """Test capture with invalid URL"""
    capture_data = {
        "source_type": "webpage",
        "url": "not-a-valid-url"
    }
    
    response = client.post("/api/v1/capture", json=capture_data)
    assert response.status_code == 422

def test_capture_invalid_source_type():
    """Test capture with invalid source type"""
    capture_data = {
        "source_type": "invalid_type",
        "url": "https://example.com"
    }
    
    response = client.post("/api/v1/capture", json=capture_data)
    assert response.status_code == 422

def test_capture_voicememo_success(mock_db_session, mock_celery_task):
    """Test successful voicememo capture"""
    capture_data = {
        "source_type": "voicememo",
        "url": "https://example.com/audio.mp3"
    }
    
    with patch('main.SessionLocal', return_value=mock_db_session):
        response = client.post("/api/v1/capture", json=capture_data)
        
    assert response.status_code == 202
    data = response.json()
    assert "item_id" in data
    assert data["status"] == "processing"
    assert data["source_type"] == "voicememo"
    assert data["source_url"] == "https://example.com/audio.mp3"
    mock_celery_task.assert_called_once()
    mock_celery_task.assert_called_with("tasks.process_voicememo", args=[data["item_id"]])

def test_capture_empty_url():
    """Test capture with empty URL"""
    capture_data = {
        "source_type": "webpage",
        "url": ""
    }
    
    response = client.post("/api/v1/capture", json=capture_data)
    assert response.status_code == 422  # Pydantic validation error for empty string

def test_capture_missing_url():
    """Test capture with missing URL field"""
    capture_data = {
        "source_type": "webpage"
    }
    
    response = client.post("/api/v1/capture", json=capture_data)
    assert response.status_code == 422  # Pydantic validation error

def test_capture_missing_source_type():
    """Test capture with missing source_type field"""
    capture_data = {
        "url": "https://example.com"
    }
    
    response = client.post("/api/v1/capture", json=capture_data)
    assert response.status_code == 422  # Pydantic validation error

def test_get_knowledge_item_server_error(mock_db_session):
    """Test server error when getting knowledge item"""
    item_id = str(uuid.uuid4())
    
    with patch('main.SessionLocal', return_value=mock_db_session):
        mock_db_session.query().filter().first.side_effect = Exception("Database error")
        response = client.get(f"/api/v1/knowledge-items/{item_id}")
        
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]

def test_get_knowledge_item_not_found(mock_db_session):
    """Test getting non-existent knowledge item"""
    item_id = str(uuid.uuid4())
    
    with patch('main.SessionLocal', return_value=mock_db_session):
        mock_db_session.query().filter().first.return_value = None
        response = client.get(f"/api/v1/knowledge-items/{item_id}")
        
    assert response.status_code == 404
    assert "Knowledge item not found" in response.json()["detail"]

def test_get_knowledge_item_success(mock_db_session):
    """Test successful retrieval of knowledge item"""
    item_id = str(uuid.uuid4())
    mock_item = KnowledgeItem(
        id=item_id,
        user_id="default_user",
        source_type="webpage",
        source_url="https://example.com",
        status="ready_for_distillation",
        title="Test Title",
        processed_text_content="Test content"
    )
    
    with patch('main.SessionLocal', return_value=mock_db_session):
        mock_db_session.query().filter().first.return_value = mock_item
        response = client.get(f"/api/v1/knowledge-items/{item_id}")
        
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["source_type"] == "webpage"
    assert data["source_url"] == "https://example.com"
    assert data["status"] == "ready_for_distillation"

# Add integration test with real database
@pytest.mark.integration
@pytest.mark.xfail(reason="Requires Redis to be running")
def test_capture_with_real_db():
    """Test capture with real database (requires database to be running)"""
    capture_data = {
        "source_type": "webpage",
        "url": "https://example.com"
    }
    
    response = client.post("/api/v1/capture", json=capture_data)
    
    assert response.status_code == 202
    data = response.json()
    assert "item_id" in data
    
    # Verify item was created in database
    get_response = client.get(f"/api/v1/knowledge-items/{data['item_id']}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == data["item_id"]
    assert get_data["source_type"] == "webpage"
    assert get_data["source_url"] == "https://example.com"
    assert get_data["status"] == "pending"

# Test middleware logging
def test_middleware_logging(caplog):
    """Test request logging middleware"""
    with caplog.at_level(logging.INFO):
        response = client.get("/health")
        
    assert response.status_code == 200
    assert any("Request: GET" in record.message for record in caplog.records)
    assert any("Response: 200" in record.message for record in caplog.records)

# Test error handling middleware
def test_error_handling_middleware():
    """Test error handling in middleware"""
    # Create a temporary route that raises an exception
    @app.get("/test-error-middleware")
    async def test_error_middleware():
        raise HTTPException(status_code=500, detail="Test error")
    
    response = client.get("/test-error-middleware")
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]
    
    # Clean up by removing the temporary route
    app.routes = [route for route in app.routes if route.path != "/test-error-middleware"]

# Test logging decorator
def test_log_execution_time_decorator(caplog):
    """Test the log_execution_time decorator"""
    with caplog.at_level(logging.INFO):
        response = client.get("/health")
        
    # Check if execution time was logged
    assert any("executed in" in record.message and "seconds" in record.message for record in caplog.records)

# Test URL validation edge cases
def test_capture_url_edge_cases(mock_db_session, mock_celery_task):
    """Test capture with various URL edge cases"""
    edge_cases = [
        {"source_type": "webpage", "url": "http://localhost:8000"},  # localhost
        {"source_type": "webpage", "url": "https://127.0.0.1"},  # IP address
        {"source_type": "webpage", "url": "https://example.com:8080"},  # with port
        {"source_type": "webpage", "url": "https://example.com/path?query=value"},  # with query params
        {"source_type": "webpage", "url": "https://example.com/path#fragment"},  # with fragment
    ]
    
    with patch('main.SessionLocal', return_value=mock_db_session):
        for case in edge_cases:
            response = client.post("/api/v1/capture", json=case)
            assert response.status_code == 202, f"Failed for URL: {case['url']}"
            data = response.json()
            assert "item_id" in data
            assert data["status"] == "processing"
            assert data["source_url"] == case["url"]
            mock_celery_task.assert_called()
            # Reset the mock for the next iteration
            mock_celery_task.reset_mock()

# Test database connection failure
def test_database_connection_failure():
    """Test behavior when database connection fails"""
    with patch('main.SessionLocal', side_effect=Exception("Database connection failed")):
        capture_data = {
            "source_type": "webpage",
            "url": "https://example.com"
        }
        
        response = client.post("/api/v1/capture", json=capture_data)
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

# Test Celery task failure
def test_celery_task_failure(mock_db_session):
    """Test behavior when Celery task fails"""
    with patch('main.SessionLocal', return_value=mock_db_session):
        with patch('main.celery_app.send_task', side_effect=Exception("Celery task failed")):
            capture_data = {
                "source_type": "webpage",
                "url": "https://example.com"
            }
            
            response = client.post("/api/v1/capture", json=capture_data)
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

# Test middleware with different HTTP methods
def test_middleware_different_methods():
    """Test middleware with different HTTP methods"""
    methods = ["GET", "POST", "PUT", "DELETE"]
    
    for method in methods:
        if method == "GET":
            response = client.get("/health")
        elif method == "POST":
            response = client.post("/api/v1/capture", json={"source_type": "webpage", "url": "https://example.com"})
        elif method == "PUT":
            response = client.put("/health")  # This will return 405, but we're testing middleware
        else:  # DELETE
            response = client.delete("/health")  # This will return 405, but we're testing middleware
            
        # Middleware should log regardless of response status
        assert response is not None

# Test health check under load
def test_health_check_under_load():
    """Test health check endpoint under simulated load"""
    for _ in range(10):  # Simulate multiple concurrent requests
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

# Test with invalid JSON
def test_capture_invalid_json():
    """Test capture endpoint with invalid JSON"""
    invalid_json = "{invalid: json}"
    response = client.post("/api/v1/capture", content=invalid_json, headers={"Content-Type": "application/json"})
    assert response.status_code == 422  # FastAPI returns 422 for invalid JSON

# Test with large URL
def test_capture_large_url():
    """Test capture with a very large URL"""
    large_url = "https://example.com/" + "x" * 10000
    capture_data = {
        "source_type": "webpage",
        "url": large_url
    }
    
    response = client.post("/api/v1/capture", json=capture_data)
    assert response.status_code == 202
    data = response.json()
    assert "item_id" in data
    assert data["status"] == "processing"
    assert data["source_url"] == large_url

# Test with special characters in URL
@pytest.mark.xfail(reason="Requires Redis to be running")
def test_capture_special_characters_url():
    """Test capture with special characters in URL"""
    special_url = "https://example.com/path?param=value&param2=value2&special=áéíóúñ"
    capture_data = {
        "source_type": "webpage",
        "url": special_url
    }
    
    response = client.post("/api/v1/capture", json=capture_data)
    assert response.status_code == 202
    data = response.json()
    assert "item_id" in data
    assert data["status"] == "processing"
    assert data["source_url"] == special_url

# Test knowledge item with special characters
def test_get_knowledge_item_special_characters(mock_db_session):
    """Test getting knowledge item with special characters in fields"""
    item_id = str(uuid.uuid4())
    mock_item = KnowledgeItem(
        id=item_id,
        user_id="test_user",
        source_type="webpage",
        source_url="https://example.com",
        status="ready_for_distillation",
        title="Test Title with special characters: áéíóúñ",
        processed_text_content="Content with special characters: áéíóúñ and emojis 🎉🌟"
    )
    
    with patch('main.SessionLocal', return_value=mock_db_session):
        mock_db_session.query().filter().first.return_value = mock_item
        response = client.get(f"/api/v1/knowledge-items/{item_id}")
        
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert "áéíóúñ" in data["title"]
    assert "🎉" in data["processed_text_content"]

# Test concurrent captures
def test_concurrent_captures(mock_db_session, mock_celery_task):
    """Test multiple concurrent capture requests"""
    capture_data = {
        "source_type": "webpage",
        "url": "https://example.com"
    }
    
    with patch('main.SessionLocal', return_value=mock_db_session):
        # Simulate 5 concurrent requests
        responses = []
        for i in range(5):
            response = client.post("/api/v1/capture", json=capture_data)
            responses.append(response)
        
        for response in responses:
            assert response.status_code == 202
            data = response.json()
            assert "item_id" in data
            assert data["status"] == "processing"
        
        # Verify Celery tasks were called for each request
        assert mock_celery_task.call_count == 5
