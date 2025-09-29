package com.example.pockyc.capture

enum class CaptureState {
    IDLE,
    SELFIE_GUIDE,
    SELFIE_RECORD_ACTIVE,
    SELFIE_RECORD_PASSIVE,
    ID_GUIDE,
    ID_RECORD_TILT,
    ID_RECORD_BACK,
    REVIEW_PRECHECKS,
    UPLOAD,
    DONE,
    RETRY
}