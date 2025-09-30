from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, Response
import uuid
import os
from datetime import datetime
import aiofiles
from minio import Minio
from minio.error import S3Error
import redis
import json
import jwt
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest
import time

from ..db.database import get_db
from ..db.models import KycSession

app = FastAPI(title="KYC Processing API", version="1.0.0")


REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path or "unknown")

    REQUEST_LATENCY.labels(request.method, path).observe(process_time)
    REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()

    return response


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# JWT Secret
JWT_SECRET = "your-secret-key"  # In production, use environment variable

# MinIO client
minio_client = Minio(
    "storage:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Redis for Celery
redis_client = redis.Redis(host='redis', port=6379, db=0)

BUCKET_NAME = "kyc-videos"

@app.on_event("startup")
async def startup_event():
    """Create MinIO bucket if it doesn't exist"""
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
    except S3Error as exc:
        print(f"MinIO error: {exc}")

@app.post("/ingest")
async def ingest_videos(
    selfie: UploadFile = File(...),
    id_video: UploadFile = File(...),
    selfie_hmac: str = None,
    selfie_sha256: str = None,
    id_hmac: str = None,
    id_sha256: str = None,
    db: Session = Depends(get_db)
):
    """
    Ingest selfie and ID video files for KYC processing.
    Verifies HMAC and SHA256, stores the videos in MinIO and queues a Celery task for processing.
    """
    for file in [selfie, id_video]:
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(status_code=400, detail="Invalid file format. Only video files are accepted.")

    # Read file contents
    selfie_content = await selfie.read()
    id_content = await id_video.read()

    # Verify HMAC and SHA256
    import hmac
    import hashlib
    import base64

    # For simplicity, use a shared secret (in production, use per-session key)
    secret = b"shared_secret"

    expected_selfie_hmac = base64.b64encode(hmac.new(secret, selfie_content, hashlib.sha256).digest()).decode()
    expected_selfie_sha256 = base64.b64encode(hashlib.sha256(selfie_content).digest()).decode()

    expected_id_hmac = base64.b64encode(hmac.new(secret, id_content, hashlib.sha256).digest()).decode()
    expected_id_sha256 = base64.b64encode(hashlib.sha256(id_content).digest()).decode()

    if selfie_hmac != expected_selfie_hmac or selfie_sha256 != expected_selfie_sha256:
        raise HTTPException(status_code=400, detail="Selfie integrity verification failed")

    if id_hmac != expected_id_hmac or id_sha256 != expected_id_sha256:
        raise HTTPException(status_code=400, detail="ID video integrity verification failed")

    # Generate unique session ID
    session_id = str(uuid.uuid4())

    # Create KYC session in database
    kyc_session = KycSession(
        session_id=session_id,
        selfie_video_path="",  # Will be set after upload
        id_video_path="",  # Will be set after upload
        status="pending"
    )
    db.add(kyc_session)
    db.commit()
    db.refresh(kyc_session)

    try:
        # Upload selfie
        selfie_temp_path = f"/tmp/{session_id}_selfie_{selfie.filename}"
        async with aiofiles.open(selfie_temp_path, 'wb') as f:
            await f.write(selfie_content)

        selfie_object_name = f"{session_id}/selfie_{selfie.filename}"
        minio_client.fput_object(
            BUCKET_NAME,
            selfie_object_name,
            selfie_temp_path
        )

        # Upload ID video
        id_temp_path = f"/tmp/{session_id}_id_{id_video.filename}"
        async with aiofiles.open(id_temp_path, 'wb') as f:
            await f.write(id_content)

        id_object_name = f"{session_id}/id_{id_video.filename}"
        minio_client.fput_object(
            BUCKET_NAME,
            id_object_name,
            id_temp_path
        )

        # Update session with video paths
        kyc_session.selfie_video_path = selfie_object_name
        kyc_session.id_video_path = id_object_name
        db.commit()

        # Queue Celery task
        task_data = {
            "session_id": session_id,
            "selfie_video_path": selfie_object_name,
            "id_video_path": id_object_name
        }
        redis_client.lpush("kyc_processing_queue", json.dumps(task_data))

        # Clean up temp files
        os.remove(selfie_temp_path)
        os.remove(id_temp_path)

        # Create JWT token
        token_payload = {
            "session_id": session_id,
            "status": "queued",
            "exp": datetime.utcnow().timestamp() + 3600  # 1 hour
        }
        token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")

        return JSONResponse(
            status_code=200,
            content={
                "token": token,
                "session_id": session_id,
                "status": "queued",
                "message": "Videos uploaded successfully and queued for processing"
            }
        )

    except S3Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload videos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/status/{session_id}")
async def get_processing_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get the processing status of a KYC session"""
    session = db.query(KycSession).filter(KycSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "status": session.status,
        "created_at": session.created_at,
        "updated_at": session.updated_at
    }

@app.get("/results/{session_id}")
async def get_processing_results(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get the complete processing results for a KYC session"""
    session = db.query(KycSession).filter(KycSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "completed":
        return {
            "session_id": session.session_id,
            "status": session.status,
            "message": "Processing not yet completed"
        }

    # Build results response
    results = {
        "session_id": session.session_id,
        "status": session.status,
        "results": {}
    }

    if session.pad_result:
        results["results"]["pad"] = {
            "score": session.pad_result.score,
            "passed": bool(session.pad_result.passed)
        }

    if session.deepfake_result:
        results["results"]["deepfake"] = {
            "score": session.deepfake_result.score,
            "passed": bool(session.deepfake_result.passed)
        }

    if session.face_match_result:
        results["results"]["face_match"] = {
            "cosine_similarity": session.face_match_result.cosine_similarity,
            "passed": bool(session.face_match_result.passed)
        }

    if session.doc_liveness_result:
        results["results"]["doc_liveness"] = {
            "score": session.doc_liveness_result.score,
            "passed": bool(session.doc_liveness_result.passed)
        }

    if session.risk_score:
        results["results"]["risk_score"] = {
            "overall_score": session.risk_score.overall_score,
            "risk_level": session.risk_score.risk_level,
            "decision": session.risk_score.decision
        }

    return results