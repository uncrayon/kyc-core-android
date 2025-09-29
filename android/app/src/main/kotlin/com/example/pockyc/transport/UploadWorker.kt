package com.example.pockyc.transport

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import com.example.pockyc.capture.CaptureViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

class UploadWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val selfiePath = inputData.getString("selfie_path") ?: return@withContext Result.failure()
        val idPath = inputData.getString("id_path") ?: return@withContext Result.failure()
        val serverUrl = inputData.getString("server_url") ?: "https://your-server.com/ingest"  // Placeholder

        val transportManager = TransportSecurityManager()
        val selfieFile = File(selfiePath)
        val idFile = File(idPath)

        if (!selfieFile.exists() || !idFile.exists()) {
            return@withContext Result.failure()
        }

        val response = transportManager.uploadVideos(serverUrl, selfieFile, idFile)

        return@withContext if (response != null) {
            // Parse response for session_id or token
            Result.success(workDataOf("response" to response))
        } else {
            Result.retry()
        }
    }
}