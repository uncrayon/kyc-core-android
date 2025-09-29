package com.example.pockyc.capture

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.video.*
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import com.example.pockyc.precheck.PrecheckManager
import java.io.File
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

class CameraManager(private val context: Context, private val lifecycleOwner: LifecycleOwner, private val precheckManager: PrecheckManager) {

    private var cameraProvider: ProcessCameraProvider? = null
    private var preview: Preview? = null
    private var videoCapture: VideoCapture<Recorder>? = null
    private var imageAnalysis: ImageAnalysis? = null
    private var recording: Recording? = null
    private var isRecording = false

    suspend fun initializeCamera(): ProcessCameraProvider {
        return suspendCoroutine { continuation ->
            val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
            cameraProviderFuture.addListener({
                cameraProvider = cameraProviderFuture.get()
                continuation.resume(cameraProvider!!)
            }, ContextCompat.getMainExecutor(context))
        }
    }

    fun startPreview(surfaceProvider: Preview.SurfaceProvider) {
        val cameraProvider = cameraProvider ?: return
        val cameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA

        preview = Preview.Builder().build().also {
            it.setSurfaceProvider(surfaceProvider)
        }

        val recorder = Recorder.Builder()
            .setQualitySelector(QualitySelector.from(Quality.HD))
            .build()
        videoCapture = VideoCapture.withOutput(recorder)

        imageAnalysis = ImageAnalysis.Builder()
            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
            .build()
            .also {
                it.setAnalyzer(ContextCompat.getMainExecutor(context)) { image ->
                    if (isRecording) {
                        val bitmap = image.toBitmap()
                        precheckManager.processFrame(bitmap)
                    }
                    image.close()
                }
            }

        try {
            cameraProvider.unbindAll()
            cameraProvider.bindToLifecycle(
                lifecycleOwner,
                cameraSelector,
                preview,
                videoCapture,
                imageAnalysis
            )
        } catch (exc: Exception) {
            Log.e("CameraManager", "Use case binding failed", exc)
        }
    }

    fun startRecording(outputFile: File) {
        val videoCapture = videoCapture ?: return
        val outputOptions = FileOutputOptions.Builder(outputFile).build()

        recording = videoCapture.output
            .prepareRecording(context, outputOptions)
            .apply {
                // Add audio if needed
                if (ContextCompat.checkSelfPermission(context, android.Manifest.permission.RECORD_AUDIO) == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                    withAudioEnabled()
                }
            }
            .start(ContextCompat.getMainExecutor(context)) { recordEvent ->
                when (recordEvent) {
                    is VideoRecordEvent.Start -> {
                        Log.d("CameraManager", "Recording started")
                        isRecording = true
                        precheckManager.reset()
                    }
                    is VideoRecordEvent.Finalize -> {
                        if (!recordEvent.hasError()) {
                            Log.d("CameraManager", "Recording finalized: ${recordEvent.outputResults.outputUri}")
                        } else {
                            Log.e("CameraManager", "Recording error: ${recordEvent.error}")
                        }
                        isRecording = false
                    }
                }
            }
    }

    fun stopRecording() {
        recording?.stop()
        recording = null
        isRecording = false
    }

    fun release() {
        cameraProvider?.unbindAll()
    }
}