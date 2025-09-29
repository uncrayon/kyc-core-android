# Architecture Documentation

This document explains how each component of the Android KYC Video PoC works, based on the planned architecture.

## Overview

The system is divided into two main parts: the Android mobile app for capture and prechecks, and the server-side pipeline for processing and analysis. The goal is to perform video-based KYC with robust spoofing and fraud detection.

## 1. Capture Flow (Android)

### How It Works
The capture flow is implemented as a state machine that guides the user through the video recording process. It starts in IDLE state and progresses through guided recording phases for selfie and ID.

- **State Machine Flow**:
  - IDLE: Initial state, waiting for user to start.
  - SELFIE_GUIDE: Display oval for face alignment with Mexican Spanish prompts.
  - SELFIE_RECORD_ACTIVE: Record active challenges (blink, head turn).
  - SELFIE_RECORD_PASSIVE: Record passive liveness.
  - ID_GUIDE: Guide user to place ID in frame.
  - ID_RECORD_TILT: Record ID with tilt motion.
  - ID_RECORD_BACK: Record back of ID if needed.
  - REVIEW_PRECHECKS: Run on-device checks.
  - UPLOAD: Secure upload to server.
  - DONE/RETRY: Final state or retry on failure.

- **Camera Integration**: Uses CameraX for 1280×720 at 30 fps, H.264 encoding. Limits payload to 25 MB.
- **UI Localization**: All user messages in Mexican Spanish, stored in strings.xml. Logs remain in English.
- **Active Challenges**: Randomized per session to prevent replay attacks.

### Project Structure
```
app/
  capture/     # State machine and recording logic
  precheck/    # On-device quality checks
  transport/   # Secure upload with HMAC/SHA-256
  ui/          # Jetpack Compose UI components
  core/        # Shared utilities
```

## 2. On-Device Prechecks

### How It Works
Prechecks run offline on the device at 5 fps sampling to ensure video quality before upload, reducing server load and improving UX.

- **Quality Gates**:
  - Blur detection: Laplacian variance > BLUR_MIN (default 120.0)
  - Exposure: Mean RGB between EXPOSURE_MIN (60) and EXPOSURE_MAX (200)
  - Motion: Optical flow < MOTION_MAX (1.5)
  - Compression artifacts: Heuristic check

- **Face Presence**:
  - Detect single face in ≥90% frames using MediaPipe.
  - Landmark stability within FACE_STABILITY (3.0)
  - Eye aspect ratio > 0.18 (except during blinks)

- **ID Detection**:
  - Quadrilateral detection with aspect 1.35–1.6
  - MRZ (Machine Readable Zone) presence check

- **Parameter Tuning**: Configurable via PrecheckConfig.kt. Accessible through debug panel (triple tap version) for on-device adjustment without rebuild.

## 3. Server Pipeline

### How It Works
The server processes uploaded videos asynchronously using a directed acyclic graph (DAG) of microservices.

- **Services**:
  - api (FastAPI): Ingestion endpoint
  - worker (Celery): Task queue for processing
  - storage (MinIO): Object storage for videos
  - db (Postgres): Metadata and results
  - pad_svc: Presentation Attack Detection (silent liveness)
  - deepfake_svc: Replay/deepfake detection using DeepfakeBench
  - facematch_svc: Face matching with InsightFace
  - ocr_svc: Text extraction with docTR
  - mrz_svc: MRZ parsing with PassportEye
  - doclive_svc: Document liveness check

- **Processing DAG**:
  1. INGEST: Receive and validate video
  2. FRAME EXTRACTION: Sample frames
  3. PAD: Check for spoofing (threshold 0.6)
  4. REPLAY/DEEPFAKE: Detect replays (max_score 0.4)
  5. ID PHOTO EXTRACT: Crop ID photo
  6. FACE MATCH: Compare selfie to ID (min_cosine 0.35)
  7. OCR + MRZ: Extract text and validate MRZ
  8. DOC-LIVENESS: Check document authenticity (threshold 0.6)
  9. RISK SCORING: Weighted combination (pad:0.35, replay:0.25, mrz:0.15, doclive:0.15, match:0.10)

- **Configuration**: Thresholds in config.yaml, reloadable with `make reload-config`.

## 4. Hardening for Fraud

### How It Works
Multiple layers of security to detect and prevent fraud attempts.

- **Red Team Dataset**: 60-80 labeled videos covering print attacks, screen replays, masks, fake docs, re-encoding.

- **Multi-signal PAD**:
  - Texture analysis (CNN)
  - Temporal cues (blink, head movement)
  - Optional rPPG (photoplethysmography from green channel)

- **Device Binding**:
  - Unique install-ID
  - Play Integrity check
  - Network ASN verification
  - Time skew < 2 min
  - Rate limiting per device/session

- **Transport Security**:
  - mTLS and TLS 1.2+
  - HMAC per chunk
  - SHA-256 server verification
  - Enforce duration/frame rate integrity
  - JWT-signed responses

## Monitoring and Metrics

- **Stack**: Prometheus for metrics, Grafana for dashboards, Sentry for errors.
- **KPIs**: Crash-free ≥99.5%, latency ≤8s, PAD TPR@FPR=1e-2 ≥0.95, match ROC-AUC ≥0.98, MRZ pass ≥95%, red-team rejection ≥85-90%.

## Parameter Adjustment

- **On-device**: Debug panel for prechecks.
- **Server**: config.yaml for model thresholds.
- **Red Team**: Benchmark script for tuning.

This architecture ensures a secure, efficient KYC process with strong fraud resistance.