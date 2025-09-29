package com.example.pockyc.ui

import android.util.Log
import androidx.camera.view.PreviewView
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.example.pockyc.capture.CameraManager
import kotlinx.coroutines.launch

@Composable
fun CameraPreview(modifier: Modifier = Modifier, cameraManager: CameraManager) {
    AndroidView(
        factory = { ctx ->
            PreviewView(ctx).apply {
                cameraManager.startPreview(surfaceProvider)
            }
        },
        modifier = modifier
    )
}