import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app
import tempfile

client = TestClient(app)

@pytest.fixture
def mock_whisper_model():
    """Mock Whisper model for testing"""
    with patch('app.model') as mock_model:
        mock_model.transcribe.return_value = {
            "text": "This is a test transcription",
            "language": "en",
            "duration": 10.5
        }
        yield mock_model

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

def test_transcribe_audio_success(mock_whisper_model):
    """Test successful audio transcription"""
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"fake audio content")
        temp_path = temp_file.name
    
    try:
        # Open the file for reading in the test
        with open(temp_path, "rb") as audio_file:
            files = {"file": ("test.mp3", audio_file, "audio/mpeg")}
            response = client.post("/transcribe", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["transcript"] == "This is a test transcription"
        assert data["language"] == "en"
        assert data["duration"] == 10.5
        mock_whisper_model.transcribe.assert_called_once()
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_transcribe_no_file():
    """Test transcription with no file provided"""
    response = client.post("/transcribe")
    assert response.status_code == 422  # FastAPI validation error for missing file

def test_transcribe_error(mock_whisper_model):
    """Test transcription with error"""
    # Make the model.transcribe raise an exception
    mock_whisper_model.transcribe.side_effect = Exception("Transcription failed")
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"fake audio content")
        temp_path = temp_file.name
    
    try:
        # Open the file for reading in the test
        with open(temp_path, "rb") as audio_file:
            files = {"file": ("test.mp3", audio_file, "audio/mpeg")}
            response = client.post("/transcribe", files=files)
        
        assert response.status_code == 500
        assert "detail" in response.json()
        assert "Error transcribing audio" in response.json()["detail"]
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
