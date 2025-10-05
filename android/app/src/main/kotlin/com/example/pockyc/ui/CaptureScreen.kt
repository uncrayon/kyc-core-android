package com.example.pockyc.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.pointer.pointerInput
import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.pockyc.R
import com.example.pockyc.capture.CaptureState
import com.example.pockyc.capture.CaptureViewModel
import com.example.pockyc.capture.CameraManager
import com.example.pockyc.capture.Challenge
import java.io.File

@Composable
fun CaptureScreen(viewModel: CaptureViewModel = viewModel(), initialDebugMode: Boolean = false) {
    val currentState by viewModel.currentState.collectAsState()
    val challenge by viewModel.challenge.collectAsState()
    val debugMode by viewModel.debugMode.collectAsState()

    LaunchedEffect(initialDebugMode) {
        if (initialDebugMode) {
            viewModel.toggleDebugMode()
        }
    }

    var tapCount by remember { mutableStateOf(0) }

    LaunchedEffect(tapCount) {
        if (tapCount > 0) {
            kotlinx.coroutines.delay(1000) // Reset after 1 second
            tapCount = 0
        }
    }

    Box(modifier = Modifier
        .fillMaxSize()
        .pointerInput(Unit) {
            detectTapGestures(
                onTap = {
                    tapCount++
                    if (tapCount == 3) {
                        viewModel.toggleDebugMode()
                        tapCount = 0
                    }
                }
            )
        }
    ) {
        when (currentState) {
            CaptureState.IDLE -> IdleScreen(viewModel)
            CaptureState.SELFIE_GUIDE -> GuideScreen(stringResource(R.string.face_guide), viewModel)
            CaptureState.SELFIE_RECORD_ACTIVE -> RecordingScreen(challenge, viewModel)
            CaptureState.SELFIE_RECORD_PASSIVE -> RecordingScreen(null, viewModel)
            CaptureState.ID_GUIDE -> GuideScreen(stringResource(R.string.id_guide), viewModel)
            CaptureState.ID_RECORD_TILT -> RecordingScreen(null, viewModel)
            CaptureState.ID_RECORD_BACK -> RecordingScreen(null, viewModel)
            CaptureState.REVIEW_PRECHECKS -> TextScreen(stringResource(R.string.review_prechecks))
            CaptureState.UPLOAD -> TextScreen(stringResource(R.string.uploading))
            CaptureState.DONE -> TextScreen(stringResource(R.string.done))
            CaptureState.RETRY -> RetryScreen(viewModel)
        }

        if (debugMode) {
            DebugPanel(viewModel)
        }
    }
}

@Composable
fun IdleScreen(viewModel: CaptureViewModel) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = stringResource(R.string.app_name))
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = { viewModel.startCapture() }) {
            Text(stringResource(R.string.start_capture))
        }
    }
}

@Composable
fun GuideScreen(message: String, viewModel: CaptureViewModel) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = message)
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = { viewModel.nextState() }) {
            Text(stringResource(R.string.next))
        }
    }
}

@Composable
fun RecordingScreen(challenge: Challenge?, viewModel: CaptureViewModel) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val cameraManager = remember(context, lifecycleOwner) { CameraManager(context, lifecycleOwner, viewModel.precheckManager) }

    var hasPermission by remember { mutableStateOf(false) }
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = { granted -> hasPermission = granted }
    )

    LaunchedEffect(Unit) {
        launcher.launch(Manifest.permission.CAMERA)
    }

    if (hasPermission) {
        LaunchedEffect(Unit) {
            cameraManager.initializeCamera()
            val outputFile = File(context.getExternalFilesDir(null), "video_${System.currentTimeMillis()}.mp4")
            cameraManager.startRecording(outputFile)
        }

        DisposableEffect(Unit) {
            onDispose {
                cameraManager.stopRecording()
                cameraManager.release()
            }
        }

        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Top,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            CameraPreview(modifier = Modifier.weight(1f), cameraManager = cameraManager)
            Spacer(modifier = Modifier.height(16.dp))
            if (challenge != null) {
                val prompt = when (challenge) {
                    Challenge.BLINK -> stringResource(R.string.blink_prompt)
                    Challenge.HEAD_TURN -> stringResource(R.string.head_turn)
                }
                Text(text = prompt)
            }
            Text(stringResource(R.string.recording))
            Spacer(modifier = Modifier.height(16.dp))
            Button(onClick = {
                cameraManager.stopRecording()
                viewModel.nextState()
            }) {
                Text(stringResource(R.string.next))
            }
        }
    } else {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(stringResource(R.string.camera_permission_denied))
        }
    }
}

@Composable
fun TextScreen(message: String) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = message)
    }
}

@Composable
fun RetryScreen(viewModel: CaptureViewModel) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(stringResource(R.string.blur_retry))
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = { viewModel.retry() }) {
            Text(stringResource(R.string.retry))
        }
    }
}

@Composable
fun DebugPanel(viewModel: CaptureViewModel) {
    // Debug panel with sliders for parameter tuning
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.8f))
            .padding(16.dp)
    ) {
        Text("Debug Panel", style = MaterialTheme.typography.headlineSmall)

        // BLUR_MIN slider
        var blurMin by remember { mutableStateOf(com.example.pockyc.precheck.Config.BLUR_MIN.toFloat()) }
        Text("BLUR_MIN: ${blurMin}")
        Slider(
            value = blurMin,
            onValueChange = {
                blurMin = it
                com.example.pockyc.precheck.Config.BLUR_MIN = it.toDouble()
            },
            valueRange = 50f..200f,
            steps = 150
        )

        // EXPOSURE_MIN slider
        var exposureMin by remember { mutableStateOf(com.example.pockyc.precheck.Config.EXPOSURE_MIN.toFloat()) }
        Text("EXPOSURE_MIN: ${exposureMin}")
        Slider(
            value = exposureMin,
            onValueChange = {
                exposureMin = it
                com.example.pockyc.precheck.Config.EXPOSURE_MIN = it.toInt()
            },
            valueRange = 0f..150f,
            steps = 150
        )

        // EXPOSURE_MAX slider
        var exposureMax by remember { mutableStateOf(com.example.pockyc.precheck.Config.EXPOSURE_MAX.toFloat()) }
        Text("EXPOSURE_MAX: ${exposureMax}")
        Slider(
            value = exposureMax,
            onValueChange = {
                exposureMax = it
                com.example.pockyc.precheck.Config.EXPOSURE_MAX = it.toInt()
            },
            valueRange = 100f..300f,
            steps = 200
        )

        // MOTION_MAX slider
        var motionMax by remember { mutableStateOf(com.example.pockyc.precheck.Config.MOTION_MAX.toFloat()) }
        Text("MOTION_MAX: ${motionMax}")
        Slider(
            value = motionMax,
            onValueChange = {
                motionMax = it
                com.example.pockyc.precheck.Config.MOTION_MAX = it.toDouble()
            },
            valueRange = 0.5f..5f,
            steps = 45
        )

        // FACE_STABILITY slider
        var faceStability by remember { mutableStateOf(com.example.pockyc.precheck.Config.FACE_STABILITY.toFloat()) }
        Text(String.format("FACE_STABILITY: %.2f", faceStability))
        Slider(
            value = faceStability,
            onValueChange = {
                faceStability = it
                com.example.pockyc.precheck.Config.FACE_STABILITY = it.toDouble()
            },
            valueRange = 0f..1f,
            steps = 9
        )
    }
}