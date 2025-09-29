# 📱 Android KYC Video PoC Plan

**Objective:** Build a stable, Android-focused PoC for video-based KYC that can detect spoofing and fraud reliably.  
**Core Components:**  
1. Capture flow (mobile SDK)  
2. On-device prechecks  
3. Server pipeline  
4. Hardening for fraud  

---

## 🧰 0) Scope & Non-Negotiables

**Target Device:** Android 10+ (API 29+)

**Stability KPIs:**
- Crash-free sessions ≥ 99.5 %
- End-to-end latency ≤ 8 s on Wi-Fi
- PAD TPR@FPR=1e-2 ≥ 0.95 (basic spoof set)
- Face-match ROC-AUC ≥ 0.98

**Security:**
- mTLS, TLS 1.2+
- Play Integrity BASIC verdict
- SHA-256 + HMAC chunk verification
- JWT-signed responses

**Stack:**
- **Android:** Kotlin, CameraX, MediaPipe, OpenCV, WorkManager, Jetpack Compose  
- **Server:** FastAPI, Celery, Redis, MinIO, Postgres, docTR, PassportEye, InsightFace, DeepfakeBench model  
- **Monitoring:** Prometheus, Grafana, Sentry

---

## 1) 📸 Capture Flow (Android)

### 1.1 Project Structure
```
app/
  capture/
  precheck/
  transport/
  ui/
  core/
```

### 1.2 State Machine
```
IDLE → SELFIE_GUIDE → SELFIE_RECORD_ACTIVE → SELFIE_RECORD_PASSIVE
     → ID_GUIDE → ID_RECORD_TILT → ID_RECORD_BACK
     → REVIEW_PRECHECKS → UPLOAD → DONE / RETRY
```

### 1.3 Camera Settings
- Resolution: 1280×720, 30 fps
- Codec: H.264 baseline
- Max payload: 25 MB (selfie + ID)
- Active challenge: randomized per session

### 1.4 User Messages (MX Spanish)
All UI-visible messages **must be in Mexican Spanish**, for example:

| Context | Message |
|---------|---------|
| Face alignment | `Coloca tu rostro dentro del óvalo y asegúrate de que esté bien iluminado.` |
| Blink prompt | `Por favor, parpadea dos veces.` |
| Head turn | `Gira lentamente la cabeza hacia la izquierda.` |
| ID guide | `Coloca tu identificación dentro del recuadro.` |
| Retry blur | `La imagen salió borrosa. Vamos a intentarlo otra vez.` |
| Upload | `Estamos verificando tu información, esto puede tardar unos segundos…` |

> **Note:** Logs and technical telemetry remain in English; **only user-facing prompts are localized.**

---

## 2) 🧠 On-Device Prechecks

Implemented offline, fast, and adjustable.

### 2.1 Quality Gates (sample @ 5 fps)
- Blur: Laplacian variance > `BLUR_MIN`
- Exposure: mean RGB between `EXPOSURE_MIN` and `EXPOSURE_MAX`
- Motion jitter: optical flow < `MOTION_MAX`
- Compression blocking heuristic

### 2.2 Face Presence
- Single face required ≥ 90 % frames
- Landmark stability within threshold
- Eye aspect ratio > 0.18 (except during blink)

### 2.3 ID Detection
- Quadrilateral aspect 1.35–1.6
- MRZ ROI present

### 2.4 Parameter Tuning
All thresholds are in `precheck/Config.kt`:

```kotlin
object PrecheckConfig {
    var BLUR_MIN = 120.0
    var EXPOSURE_MIN = 60
    var EXPOSURE_MAX = 200
    var MOTION_MAX = 1.5
    var FACE_STABILITY = 3.0
}
```

You can use **Android debug menu** (e.g., triple tap on version) to expose a **"Developer Panel"** where testers can change these values **on device** without rebuilding.

---

## 3) 🖥️ Server Pipeline

### 3.1 Services
- `api` (FastAPI)
- `worker` (Celery)
- `storage` (MinIO)
- `db` (Postgres)
- `pad_svc` (silent liveness)
- `deepfake_svc` (replay detector)
- `facematch_svc` (InsightFace)
- `ocr_svc` (docTR)
- `mrz_svc` (PassportEye)
- `doclive_svc` (doc-liveness)

### 3.2 Processing DAG
```
INGEST → FRAME EXTRACTION
       → PAD
       → REPLAY/DEEPFAKE
       → ID PHOTO EXTRACT
       → FACE MATCH
       → OCR + MRZ
       → DOC-LIVENESS
       → RISK SCORING
```

### 3.3 Parameter Configuration
All model thresholds and weights are in `config.yaml`:

```yaml
pad:
  threshold: 0.6
replay:
  max_score: 0.4
facematch:
  min_cosine: 0.35
doc_liveness:
  threshold: 0.6
weights:
  pad: 0.35
  replay: 0.25
  mrz: 0.15
  doclive: 0.15
  match: 0.10
```

Reload without restart:

```bash
make reload-config
```

---

## 4) 🧱 Hardening for Fraud

### 4.1 Red Team Dataset
Create 60–80 test videos:
- Print attacks
- Screen replays
- Mask attempts
- Fake docs (on-screen / prints)
- Re-encoded media

### 4.2 Multi-signal PAD
Combine:
- Texture (CNN)
- Temporal (blink/head)
- Optional rPPG (green channel periodicity)

### 4.3 Device Binding
- Install-ID + Play Integrity + network ASN
- Session time skew < 2 min
- Rate limit by device/session

### 4.4 Transport Security
- HMAC per chunk
- SHA-256 verification server-side
- Enforce media duration/frame rate integrity

---

## 5) 🧪 Testing & Parameter Adjustment

### 5.1 Local Android Testing
- Use **adb** to install PoC APK
- Run with `--dev-panel` to expose parameter sliders
- Capture under various lighting, devices, and edge cases

### 5.2 Server Testing
- Run `make run` (Docker Compose)
- Use `scripts/seed_red_team.py` to inject red-team sessions
- Adjust `config.yaml` and re-run to evaluate threshold changes
- View metrics at `http://localhost:3000` (Grafana)

### 5.3 Metrics Dashboard
- PAD score distribution
- Replay score distribution
- Match ROC
- MRZ success rate
- Latency p50/p95
- Session error rates

---

## 6) 📝 Deliverables

- Android APK (internal testing)
- Docker Compose stack
- Postman collection
- Grafana dashboards
- Red team dataset (labeled)
- One-pager "Lessons Learned & Gaps"

---

## 7) 📌 Out of Scope

- NFC chip reading
- iBeta/NIST certification
- PII legal frameworks
- iOS support
- Real-time on-device ML acceleration

---

## 🧭 Quickstart

```bash
# Android
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk

# Server
make run
make seed-red-team
```

---

## 🗣️ Localization Note

All **user-facing messages** must be in **Mexican Spanish**, stored in:
```
app/src/main/res/values-es-rMX/strings.xml
```

Example:

```xml
<string name="face_guide">Coloca tu rostro dentro del óvalo y asegúrate de que esté bien iluminado.</string>
<string name="blink_prompt">Por favor, parpadea dos veces.</string>
<string name="head_turn">Gira lentamente la cabeza hacia la izquierda.</string>
<string name="id_guide">Coloca tu identificación dentro del recuadro.</string>
<string name="blur_retry">La imagen salió borrosa. Vamos a intentarlo otra vez.</string>
<string name="uploading">Estamos verificando tu información, esto puede tardar unos segundos…</string>
```

No English strings should appear in the final UI.

---

## ⚙️ Parameter Adjustment Philosophy

- **On device:** for prechecks → use debug panel  
- **Server:** for model thresholds → use `config.yaml` + `make reload-config`  
- **Red team:** for tuning PAD/replay thresholds → rerun `scripts/benchmark_red_team.py`

This separation ensures quick iteration without frequent redeployments.

---

## ✅ Success Criteria for PoC

| Area | Metric | Target |
|------|--------|--------|
| Stability | Crash-free | ≥ 99.5 % |
| Latency | End-to-end | ≤ 8 s |
| PAD | TPR@FPR=1e-2 | ≥ 0.95 |
| Match | ROC-AUC | ≥ 0.98 |
| OCR | MRZ checksum pass | ≥ 95 % |
| Fraud | Red-team rejection | ≥ 85–90 % |