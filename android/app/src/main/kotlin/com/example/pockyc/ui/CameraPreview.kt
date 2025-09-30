package com.example.pockyc.ui

import androidx.camera.view.PreviewView
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import com.example.pockyc.capture.CameraManager

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