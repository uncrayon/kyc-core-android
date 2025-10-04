import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import hashlib
import hmac
import base64
import uuid
from io import BytesIO

from api.main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

# Use a file-based SQLite database for test stability
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def client():
    """Pytest fixture to create a TestClient with a file-based temporary database."""
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    # Teardown
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="module")
def test_data():
    file_size = 10 * 1024  # 10 KB
    content = os.urandom(file_size)
    secret = b"shared_secret"
    correct_hmac = base64.b64encode(hmac.new(secret, content, hashlib.sha256).digest()).decode()
    correct_sha256 = base64.b64encode(hashlib.sha256(content).digest()).decode()

    return {
        "content": content,
        "correct_hmac": correct_hmac,
        "correct_sha256": correct_sha256,
        "incorrect_hmac": "incorrect_hmac_value",
    }

@patch("api.main.minio_client")
@patch("api.main.redis_client")
@patch("api.main.uuid.uuid4", return_value=uuid.UUID('12345678-1234-5678-1234-567812345678'))
def test_ingest_file_with_invalid_hmac(mock_uuid, redis_mock, minio_mock, client, test_data):
    """Test that uploading a file with an invalid HMAC is rejected."""
    content = test_data["content"]
    response = client.post(
        "/ingest",
        files={
            "selfie": ("selfie.mp4", BytesIO(content), "video/mp4"),
            "id_video": ("id.mp4", BytesIO(content), "video/mp4"),
        },
        data={
            "selfie_hmac": test_data["incorrect_hmac"],
            "selfie_sha256": test_data["correct_sha256"],
            "id_hmac": test_data["correct_hmac"],
            "id_sha256": test_data["correct_sha256"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Selfie integrity verification failed"
    minio_mock.fput_object.assert_not_called()

@patch("api.main.minio_client")
@patch("api.main.redis_client")
@patch("api.main.uuid.uuid4", return_value=uuid.UUID('87654321-4321-8765-4321-876543210987'))
def test_ingest_valid_files(mock_uuid, redis_mock, minio_mock, client, test_data):
    """Test successful ingestion of valid files."""
    content = test_data["content"]
    response = client.post(
        "/ingest",
        files={
            "selfie": ("selfie.mp4", BytesIO(content), "video/mp4"),
            "id_video": ("id.mp4", BytesIO(content), "video/mp4"),
        },
        data={
            "selfie_hmac": test_data["correct_hmac"],
            "selfie_sha256": test_data["correct_sha256"],
            "id_hmac": test_data["correct_hmac"],
            "id_sha256": test_data["correct_sha256"],
        },
    )

    assert response.status_code == 200, f"Request failed: {response.json()}"
    json_response = response.json()
    assert json_response["status"] == "queued"
    assert "session_id" in json_response
    assert "token" in json_response

    assert minio_mock.fput_object.call_count == 2
    redis_mock.lpush.assert_called_once()