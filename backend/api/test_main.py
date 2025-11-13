import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app
from models import KnowledgeItem
from schemas import KnowledgeItemCreate, KnowledgeItemBase
from database import get_db
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
    assert data["source_url"] == "https://example.com"
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
    # Find the index of the route to remove
    route_index = None
    for i, route in enumerate(app.routes):
        if hasattr(route, 'path') and route.path == "/test-error-middleware":
            route_index = i
            break
    
    # Remove the route if found
    if route_index is not None:
        app.routes.pop(route_index)

# Test logging decorator
def test_log_execution_time_decorator(mock_db_session, mock_celery_task, caplog):
    """Test the log_execution_time decorator"""
    capture_data = {
        "source_type": "webpage",
        "url": "https://example.com"
    }
    
    with caplog.at_level(logging.INFO):
        with patch('main.SessionLocal', return_value=mock_db_session):
            response = client.post("/api/v1/capture", json=capture_data)
        
    # Check if execution time was logged
    assert any("executed in" in record.message and "seconds" in record.message for record in caplog.records)
    mock_celery_task.assert_called_once()

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
            # With our custom validator, URLs are not normalized
            # We expect the exact URL that was sent
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
        
        try:
            response = client.post("/api/v1/capture", json=capture_data)
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
        except Exception as e:
            # If the exception is raised directly, check that it's handled properly
            assert "Database connection failed" in str(e)

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
@pytest.mark.xfail(reason="Requires Redis to be running")
def test_capture_large_url():
    """Test capture with a very large URL"""
    # Create a URL that is exactly 10000 characters total
    base_url = "https://example.com/"
    remaining_length = 10000 - len(base_url)
    large_url = base_url + "x" * remaining_length
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


def test_console_health_endpoint(mock_db_session, monkeypatch):
    """Console health endpoint aggregates component statuses"""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    mock_db_session.execute.return_value = None

    with patch("console_routes.redis.from_url") as mock_redis, \
            patch("console_routes.boto3.client") as mock_boto, \
            patch("console_routes.requests.get") as mock_requests_get, \
            patch("console_routes.celery_app.control.inspect") as mock_inspect:

        redis_instance = MagicMock()
        mock_redis.return_value = redis_instance
        redis_instance.ping.return_value = True

        mock_boto.return_value.head_bucket.return_value = None

        mock_response = MagicMock()
        mock_response.json.return_value = {"model": "base"}
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        inspect_instance = MagicMock()
        inspect_instance.ping.return_value = {"worker@1": {"ok": "pong"}}
        mock_inspect.return_value = inspect_instance

        response = client.get("/internal/console/health")
        assert response.status_code == 200
        components = response.json()["components"]
        assert components["redis"]["status"] == "healthy"
        assert components["worker"]["status"] == "healthy"

    app.dependency_overrides.pop(get_db, None)


def test_console_auth_token_required(mock_db_session, monkeypatch):
    """Console endpoints require auth token when configured"""
    monkeypatch.setenv("CONSOLE_API_TOKEN", "secret-token")
    app.dependency_overrides[get_db] = lambda: mock_db_session

    response = client.get("/internal/console/health")
    assert response.status_code == 401

    with patch("console_routes.redis.from_url") as mock_redis, \
            patch("console_routes.boto3.client"), \
            patch("console_routes.requests.get"), \
            patch("console_routes.celery_app.control.inspect") as mock_inspect:

        redis_instance = MagicMock()
        mock_redis.return_value = redis_instance
        redis_instance.ping.return_value = True
        inspect_instance = MagicMock()
        inspect_instance.ping.return_value = {"worker@1": {"ok": "pong"}}
        mock_inspect.return_value = inspect_instance

        response = client.get(
            "/internal/console/health",
            headers={"X-Console-Token": "secret-token"}
        )
        assert response.status_code == 200

    app.dependency_overrides.pop(get_db, None)
    monkeypatch.delenv("CONSOLE_API_TOKEN", raising=False)


def test_console_metrics_endpoint():
    """Console metrics endpoint returns Celery stats"""
    with patch("console_routes.celery_app.control.inspect") as mock_inspect:
        inspect_instance = MagicMock()
        inspect_instance.stats.return_value = {
            "worker@1": {"total": {"tasks.process_webpage": 2}, "pid": 123, "uptime": 10, "loadavg": [0.1, 0.2, 0.3]}
        }
        inspect_instance.active.return_value = {"worker@1": [{"name": "tasks.process_webpage"}]}
        inspect_instance.reserved.return_value = {"worker@1": [{"name": "tasks.process_webpage", "delivery_info": {"routing_key": "default"}}]}
        inspect_instance.scheduled.return_value = {}
        mock_inspect.return_value = inspect_instance

        response = client.get("/internal/console/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "workers" in data
        assert data["queued_tasks"]["default"] == 1


def test_console_knowledge_items_list(mock_db_session):
    """Console listing endpoint returns items filtered by status"""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    query_mock = MagicMock()
    mock_db_session.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.count.return_value = 1
    query_mock.order_by.return_value = query_mock
    query_mock.offset.return_value = query_mock
    query_mock.limit.return_value = query_mock

    fake_item = MagicMock()
    fake_item.id = uuid.uuid4()
    fake_item.source_type = "webpage"
    fake_item.source_url = "https://example.com"
    fake_item.status = "error"
    fake_item.processed_at = datetime.now()
    fake_item.created_at = datetime.now()
    fake_item.last_error = "Timeout"
    fake_item.title = "Example"
    query_mock.all.return_value = [fake_item]

    response = client.get("/internal/console/knowledge-items?status=error&limit=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["last_error"] == "Timeout"

    app.dependency_overrides.pop(get_db, None)


def test_console_retry_endpoint(mock_db_session):
    """Console retry endpoint resets item and requeues task"""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    mock_item = MagicMock()
    mock_item.id = str(uuid.uuid4())
    mock_item.source_type = "webpage"
    mock_db_session.query().filter().first.return_value = mock_item

    with patch("console_routes.celery_app.send_task") as mock_send_task:
        response = client.post(f"/internal/console/knowledge-items/{mock_item.id}/retry")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        mock_send_task.assert_called_once()
        assert mock_item.status == "pending"

    app.dependency_overrides.pop(get_db, None)


def test_console_logs_endpoint(tmp_path, monkeypatch):
    """Console logs endpoint tails file contents"""
    log_path = tmp_path / "app.log"
    log_path.write_text("line1\nline2\n")
    monkeypatch.setenv("API_LOG_PATH", str(log_path))

    response = client.get("/internal/console/logs?lines=1")
    assert response.status_code == 200
    assert response.json()["lines"] == ["line2"]

    monkeypatch.delenv("API_LOG_PATH", raising=False)


def test_console_update_item_success(mock_db_session):
    """Console patch endpoint updates editable fields"""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    mock_item = MagicMock()
    mock_item.id = str(uuid.uuid4())
    mock_item.source_type = "webpage"
    mock_item.status = "pending"
    mock_item.processed_at = None
    mock_item.created_at = datetime.now()
    mock_item.processed_text_content = "content"
    mock_db_session.query().filter().first.return_value = mock_item

    payload = {"title": "Updated", "status": "processing", "last_error": "Timeout"}
    response = client.patch(f"/internal/console/knowledge-items/{mock_item.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["status"] == "processing"
    assert data["last_error"] == "Timeout"
    assert mock_item.title == "Updated"
    assert mock_item.status == "processing"
    assert mock_item.last_error == "Timeout"
    mock_db_session.commit.assert_called_once()

    app.dependency_overrides.pop(get_db, None)


def test_console_update_item_invalid_status(mock_db_session):
    """Console patch endpoint rejects invalid status"""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    mock_item = MagicMock()
    mock_db_session.query().filter().first.return_value = mock_item

    response = client.patch(
        "/internal/console/knowledge-items/123",
        json={"status": "invalid"},
    )
    assert response.status_code == 400

    app.dependency_overrides.pop(get_db, None)
