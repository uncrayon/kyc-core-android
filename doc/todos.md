# Project Todos

This file lists actionable todos extracted from the project plan. Check off items as they are completed.

## Android Development

- [x] Set up Android project structure (app/capture/, precheck/, transport/, ui/, core/)
- [x] Implement capture flow state machine (IDLE → SELFIE_GUIDE → etc.)
- [x] Configure camera settings (1280×720, 30 fps, H.264, max 25 MB)
- [x] Add active challenge randomization per session
- [x] Localize all user-facing messages to Mexican Spanish in strings.xml
- [x] Implement on-device prechecks (quality gates, face presence, ID detection)
- [x] Add parameter tuning via debug panel (PrecheckConfig.kt)
- [x] Ensure crash-free sessions ≥ 99.5%

## Server Development

- [x] Set up services: api (FastAPI), worker (Celery), storage (MinIO), db (Postgres), pad_svc, deepfake_svc, facematch_svc, ocr_svc, mrz_svc, doclive_svc
- [x] Implement processing DAG: INGEST → FRAME EXTRACTION → PAD → REPLAY/DEEPFAKE → ID PHOTO EXTRACT → FACE MATCH → OCR + MRZ → DOC-LIVENESS → RISK SCORING
- [x] Configure model thresholds and weights in config.yaml
- [x] Add parameter reload without restart (make reload-config)
- [x] Implement monitoring with Prometheus, Grafana, Sentry

## Fraud Hardening

- [x] Create red team dataset (60-80 test videos: print attacks, screen replays, masks, fake docs, re-encoded media)
- [x] Implement multi-signal PAD (texture CNN, temporal blink/head, optional rPPG)
- [x] Add device binding (Install-ID, Play Integrity, ASN, time skew < 2 min, rate limiting)
- [x] Secure transport (HMAC per chunk, SHA-256 verification, enforce media integrity)

## Testing & Parameter Adjustment

- [x] Set up local Android testing (adb install, --dev-panel for sliders)
- [x] Set up server testing (make run, seed_red_team.py, adjust config.yaml)
- [x] Create metrics dashboard (PAD/replay distributions, Match ROC, MRZ success, latency, error rates)
- [x] Tune parameters for KPIs: latency ≤ 8s, PAD TPR@FPR=1e-2 ≥ 0.95, Match ROC-AUC ≥ 0.98, etc.
- [x] Benchmark red team with scripts/benchmark_red_team.py

## Deliverables

- [x] Build Android APK for internal testing
- [x] Create Docker Compose stack
- [x] Prepare Postman collection for API testing
- [x] Set up Grafana dashboards
- [x] Label and prepare red team dataset
## Next Steps

- Conduct comprehensive end-to-end testing across all components
- Perform security audit and penetration testing
- Optimize performance for production workloads
- Implement CI/CD pipelines for automated deployment
- Develop user documentation and training materials
- Plan for scalability and high-availability architecture
- Explore integration with existing identity systems
- [x] Write one-pager "Lessons Learned & Gaps"

## Out of Scope (Do Not Implement)

- NFC chip reading
- iBeta/NIST certification
- PII legal frameworks
- iOS support
- Real-time on-device ML acceleration