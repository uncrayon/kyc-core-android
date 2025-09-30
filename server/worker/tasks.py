import requests
import json
import cv2
import os
import tempfile
from minio import Minio
from minio.error import S3Error
import yaml
from sqlalchemy.orm import Session
from datetime import datetime

from celery_app import celery_app
from db.database import SessionLocal
from db.models import (
    KycSession,
    FrameExtraction,
    PadResult,
    DeepfakeResult,
    FaceMatchResult,
    OcrResult,
    MrzResult,
    DocLivenessResult,
    RiskScore,
)

# Load config
with open('/app/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# MinIO client
minio_client = Minio(
    "storage:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

BUCKET_NAME = "kyc-videos"
FRAMES_BUCKET = "kyc-frames"

def download_video_from_minio(video_path):
    """Download video from MinIO to temporary file"""
    try:
        temp_dir = tempfile.mkdtemp()
        local_path = os.path.join(temp_dir, "video.mp4")
        minio_client.fget_object(BUCKET_NAME, video_path, local_path)
        return local_path
    except S3Error as e:
        raise Exception(f"Failed to download video: {str(e)}")

def upload_frames_to_minio(session_id, frames_dir):
    """Upload extracted frames to MinIO"""
    try:
        # Create frames bucket if it doesn't exist
        if not minio_client.bucket_exists(FRAMES_BUCKET):
            minio_client.make_bucket(FRAMES_BUCKET)

        frame_files = [f for f in os.listdir(frames_dir) if f.endswith('.jpg')]
        uploaded_paths = []

        for frame_file in sorted(frame_files):
            frame_path = os.path.join(frames_dir, frame_file)
            object_name = f"{session_id}/frames/{frame_file}"
            minio_client.fput_object(FRAMES_BUCKET, object_name, frame_path)
            uploaded_paths.append(object_name)

        return uploaded_paths
    except S3Error as e:
        raise Exception(f"Failed to upload frames: {str(e)}")

def extract_frames(video_path, output_dir, frame_interval=30):
    """Extract frames from video at specified intervals"""
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    extracted_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_filename = f"frame_{extracted_count:06d}.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            extracted_count += 1

        frame_count += 1

    cap.release()
    return extracted_count

def call_service(service_url, payload):
    """Call a microservice with payload"""
    try:
        response = requests.post(service_url, json=payload, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Service call failed: {str(e)}")

@celery_app.task(bind=True)
def process_kyc_video(self, session_id):
    """Main task to process KYC video through the DAG pipeline"""
    db = SessionLocal()
    try:
        # Update session status
        session = db.query(KycSession).filter(KycSession.session_id == session_id).first()
        if not session:
            raise Exception(f"Session {session_id} not found")

        session.status = "processing"
        db.commit()

        # Step 1: FRAME EXTRACTION
        print(f"[{session_id}] Starting frame extraction")
        video_local_path = download_video_from_minio(session.video_path)

        frames_dir = tempfile.mkdtemp()
        frame_count = extract_frames(video_local_path, frames_dir)

        # Upload frames to MinIO
        frame_paths = upload_frames_to_minio(session_id, frames_dir)

        # Save frame extraction result
        frame_extraction = FrameExtraction(
            session_id=session.id,
            frames_path=json.dumps(frame_paths),
            frame_count=frame_count
        )
        db.add(frame_extraction)
        db.commit()

        # Clean up
        os.remove(video_local_path)
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir, f))
        os.rmdir(frames_dir)

        # Step 2: PAD (Presentation Attack Detection)
        print(f"[{session_id}] Starting PAD analysis")
        pad_payload = {
            "session_id": session_id,
            "frames": frame_paths[:10]  # Use first 10 frames for PAD
        }
        pad_result = call_service("http://pad_svc:8000/analyze", pad_payload)

        pad_db_result = PadResult(
            session_id=session.id,
            score=pad_result.get("score", 0.0),
            threshold=config["thresholds"]["pad"],
            passed=1 if pad_result.get("score", 0.0) >= config["thresholds"]["pad"] else 0,
            details=json.dumps(pad_result)
        )
        db.add(pad_db_result)
        db.commit()

        # Step 3: REPLAY/DEEPFAKE DETECTION
        print(f"[{session_id}] Starting deepfake detection")
        deepfake_payload = {
            "session_id": session_id,
            "video_path": session.video_path
        }
        deepfake_result = call_service("http://deepfake_svc:8000/analyze", deepfake_payload)

        deepfake_db_result = DeepfakeResult(
            session_id=session.id,
            score=deepfake_result.get("score", 0.0),
            threshold=config["thresholds"]["replay"],
            passed=1 if deepfake_result.get("score", 0.0) <= config["thresholds"]["replay"] else 0,
            details=json.dumps(deepfake_result)
        )
        db.add(deepfake_db_result)
        db.commit()

        # Step 4: ID PHOTO EXTRACT (from frames)
        print(f"[{session_id}] Starting ID photo extraction")
        # For simplicity, assume first frame contains ID photo
        id_photo_path = frame_paths[0] if frame_paths else None

        # Step 5: FACE MATCH
        print(f"[{session_id}] Starting face matching")
        face_match_payload = {
            "session_id": session_id,
            "face_frames": frame_paths[:5],  # Use first 5 frames for face detection
            "id_photo_path": id_photo_path
        }
        face_match_result = call_service("http://facematch_svc:8000/match", face_match_payload)

        face_match_db_result = FaceMatchResult(
            session_id=session.id,
            cosine_similarity=face_match_result.get("cosine_similarity", 0.0),
            threshold=config["thresholds"]["facematch"],
            passed=1 if face_match_result.get("cosine_similarity", 0.0) >= config["thresholds"]["facematch"] else 0,
            face_image_path=json.dumps(face_match_result.get("face_image_path", [])),
            id_photo_path=id_photo_path,
            details=json.dumps(face_match_result)
        )
        db.add(face_match_db_result)
        db.commit()

        # Step 6: OCR + MRZ
        print(f"[{session_id}] Starting OCR and MRZ analysis")
        ocr_payload = {
            "session_id": session_id,
            "frames": frame_paths  # Use all frames for OCR
        }
        ocr_result = call_service("http://ocr_svc:8000/extract", ocr_payload)

        ocr_db_result = OcrResult(
            session_id=session.id,
            extracted_text=ocr_result.get("text", ""),
            confidence=ocr_result.get("confidence", 0.0),
            document_type=ocr_result.get("document_type", "unknown"),
            details=json.dumps(ocr_result)
        )
        db.add(ocr_db_result)
        db.commit()

        # MRZ parsing
        mrz_payload = {
            "session_id": session_id,
            "ocr_text": ocr_result.get("text", "")
        }
        mrz_result = call_service("http://mrz_svc:8000/parse", mrz_payload)

        mrz_db_result = MrzResult(
            session_id=session.id,
            mrz_data=json.dumps(mrz_result.get("mrz_data", {})),
            parsed_fields=json.dumps(mrz_result.get("parsed_fields", {})),
            valid=1 if mrz_result.get("valid", False) else 0,
            details=json.dumps(mrz_result)
        )
        db.add(mrz_db_result)
        db.commit()

        # Step 7: DOC-LIVENESS
        print(f"[{session_id}] Starting document liveness detection")
        doclive_payload = {
            "session_id": session_id,
            "frames": frame_paths
        }
        doclive_result = call_service("http://doclive_svc:8000/analyze", doclive_payload)

        doclive_db_result = DocLivenessResult(
            session_id=session.id,
            score=doclive_result.get("score", 0.0),
            threshold=config["thresholds"]["doc_liveness"],
            passed=1 if doclive_result.get("score", 0.0) >= config["thresholds"]["doc_liveness"] else 0,
            details=json.dumps(doclive_result)
        )
        db.add(doclive_db_result)
        db.commit()

        # Step 8: RISK SCORING
        print(f"[{session_id}] Calculating risk score")
        risk_payload = {
            "session_id": session_id,
            "results": {
                "pad": {"score": pad_db_result.score, "passed": bool(pad_db_result.passed)},
                "deepfake": {"score": deepfake_db_result.score, "passed": bool(deepfake_db_result.passed)},
                "face_match": {"cosine_similarity": face_match_db_result.cosine_similarity, "passed": bool(face_match_db_result.passed)},
                "doc_liveness": {"score": doclive_db_result.score, "passed": bool(doclive_db_result.passed)}
            }
        }

        # Calculate weighted risk score
        weights = config["weights"]
        component_scores = {
            "pad": 1.0 if pad_db_result.passed else 0.0,
            "deepfake": 1.0 if deepfake_db_result.passed else 0.0,
            "face_match": 1.0 if face_match_db_result.passed else 0.0,
            "doc_liveness": 1.0 if doclive_db_result.passed else 0.0
        }

        overall_score = sum(component_scores[comp] * weights[comp] for comp in component_scores)

        # Determine risk level and decision
        if overall_score >= 0.8:
            risk_level = "low"
            decision = "approve"
        elif overall_score >= 0.6:
            risk_level = "medium"
            decision = "manual_review"
        else:
            risk_level = "high"
            decision = "reject"

        risk_score = RiskScore(
            session_id=session.id,
            overall_score=overall_score,
            risk_level=risk_level,
            component_scores=json.dumps(component_scores),
            weights=json.dumps(weights),
            decision=decision
        )
        db.add(risk_score)
        db.commit()

        # Update session status
        session.status = "completed"
        db.commit()

        print(f"[{session_id}] Processing completed successfully")
        return {"status": "completed", "session_id": session_id}

    except Exception as e:
        print(f"[{session_id}] Processing failed: {str(e)}")
        session.status = "failed"
        db.commit()
        raise self.retry(countdown=60, exc=e, max_retries=3)
    finally:
        db.close()