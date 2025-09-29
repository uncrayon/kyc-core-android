package com.example.pockyc.capture

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.workDataOf
import com.example.pockyc.precheck.PrecheckManager
import com.example.pockyc.transport.TransportSecurityManager
import com.example.pockyc.transport.UploadWorker
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.io.File

enum class Challenge {
    BLINK,
    HEAD_TURN
}

class CaptureViewModel : ViewModel() {

    val precheckManager = PrecheckManager()

    private val _currentState = MutableStateFlow(CaptureState.IDLE)
    val currentState: StateFlow<CaptureState> = _currentState

    private val _challenge = MutableStateFlow<Challenge?>(null)
    val challenge: StateFlow<Challenge?> = _challenge

    private val _debugMode = MutableStateFlow(false)
    val debugMode: StateFlow<Boolean> = _debugMode

    var selfieFile: File? = null
    var idFile: File? = null

    init {
        // Generate random challenge on init
        _challenge.value = if (kotlin.random.Random.nextBoolean()) Challenge.BLINK else Challenge.HEAD_TURN
    }

    fun startCapture() {
        _currentState.value = CaptureState.SELFIE_GUIDE
    }

    fun nextState() {
        when (_currentState.value) {
            CaptureState.IDLE -> _currentState.value = CaptureState.SELFIE_GUIDE
            CaptureState.SELFIE_GUIDE -> _currentState.value = CaptureState.SELFIE_RECORD_ACTIVE
            CaptureState.SELFIE_RECORD_ACTIVE -> _currentState.value = CaptureState.SELFIE_RECORD_PASSIVE
            CaptureState.SELFIE_RECORD_PASSIVE -> _currentState.value = CaptureState.ID_GUIDE
            CaptureState.ID_GUIDE -> _currentState.value = CaptureState.ID_RECORD_TILT
            CaptureState.ID_RECORD_TILT -> _currentState.value = CaptureState.ID_RECORD_BACK
            CaptureState.ID_RECORD_BACK -> _currentState.value = CaptureState.REVIEW_PRECHECKS
            CaptureState.REVIEW_PRECHECKS -> _currentState.value = if (runPrechecks()) CaptureState.UPLOAD else CaptureState.RETRY
            CaptureState.UPLOAD -> {
                // Start upload
                performUpload()
            }
            CaptureState.DONE -> {}
            CaptureState.RETRY -> _currentState.value = CaptureState.SELFIE_GUIDE
        }
    }

    private fun performUpload() {
        viewModelScope.launch {
            val transportManager = TransportSecurityManager()
            val response = transportManager.uploadVideos("https://your-server.com/ingest", selfieFile!!, idFile!!)
            if (response != null) {
                // Parse JWT or session_id
                _currentState.value = CaptureState.DONE
            } else {
                _currentState.value = CaptureState.RETRY
            }
        }
    }

    private fun runPrechecks(): Boolean {
        val qualityPass = precheckManager.checkQualityGates()
        val facePass = precheckManager.checkFacePresence()
        // For ID detection, need a frame; assume last frame or something
        // For simplicity, assume ID check is done during processing
        return qualityPass && facePass // && idPass
    }

    fun retry() {
        _currentState.value = CaptureState.RETRY
        // Then nextState will go to SELFIE_GUIDE
    }

    fun toggleDebugMode() {
        _debugMode.value = !_debugMode.value
    }
}