package com.example.pockyc.transport

import android.media.MediaMetadataRetriever
import android.net.Uri
import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileInputStream
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManager
import javax.net.ssl.X509TrustManager
import java.security.cert.X509Certificate
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import java.io.IOException

class TransportSecurityManager {

    private val hmacKey = "shared_secret".toByteArray()  // Use shared secret for server verification
    private val sha256Digest = MessageDigest.getInstance("SHA-256")

    data class ChunkResult(
        val chunkIndex: Int,
        val hmac: String,
        val sha256: String,
        val data: ByteArray
    )

    data class MediaIntegrityResult(
        val durationValid: Boolean,
        val frameRateValid: Boolean,
        val overallValid: Boolean
    )


    fun computeHmac(data: ByteArray): String {
        val mac = Mac.getInstance("HmacSHA256")
        val keySpec = SecretKeySpec(hmacKey, "HmacSHA256")
        mac.init(keySpec)
        val hmacBytes = mac.doFinal(data)
        return Base64.encodeToString(hmacBytes, Base64.NO_WRAP)
    }

    fun computeSha256(data: ByteArray): String {
        sha256Digest.reset()
        val hash = sha256Digest.digest(data)
        return Base64.encodeToString(hash, Base64.NO_WRAP)
    }

    fun processChunk(chunkIndex: Int, data: ByteArray): ChunkResult {
        val hmac = computeHmac(data)
        val sha256 = computeSha256(data)
        return ChunkResult(chunkIndex, hmac, sha256, data)
    }

    fun verifyChunk(chunk: ChunkResult): Boolean {
        val expectedHmac = computeHmac(chunk.data)
        val expectedSha256 = computeSha256(chunk.data)
        return expectedHmac == chunk.hmac && expectedSha256 == chunk.sha256
    }

    suspend fun checkMediaIntegrity(videoFile: File): MediaIntegrityResult = withContext(Dispatchers.IO) {
        try {
            val retriever = MediaMetadataRetriever()
            retriever.setDataSource(videoFile.absolutePath)

            // Check duration (should be reasonable for a KYC video, e.g., 5-30 seconds)
            val durationStr = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)
            val durationMs = durationStr?.toLongOrNull() ?: 0L
            val durationValid = durationMs in 5000..30000 // 5-30 seconds

            // Check frame rate (should be reasonable, e.g., 15-60 fps)
            val frameRateStr = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_CAPTURE_FRAMERATE)
            val frameRate = frameRateStr?.toFloatOrNull() ?: 0f
            val frameRateValid = frameRate in 15f..60f

            retriever.release()

            MediaIntegrityResult(
                durationValid = durationValid,
                frameRateValid = frameRateValid,
                overallValid = durationValid && frameRateValid
            )
        } catch (e: Exception) {
            MediaIntegrityResult(false, false, false)
        }
    }

    fun createSecureHttpClient(): OkHttpClient {
        val sslContext = SSLContext.getInstance("TLSv1.2")
        sslContext.init(null, null, SecureRandom())

        return OkHttpClient.Builder()
            .sslSocketFactory(sslContext.socketFactory, object : X509TrustManager {
                override fun checkClientTrusted(chain: Array<X509Certificate>, authType: String) {}
                override fun checkServerTrusted(chain: Array<X509Certificate>, authType: String) {}
                override fun getAcceptedIssuers(): Array<X509Certificate> = arrayOf()
            })
            .build()
    }

    suspend fun secureUpload(url: String, chunks: List<ChunkResult>): Boolean = withContext(Dispatchers.IO) {
        try {
            val client = createSecureHttpClient()

            // Verify all chunks before upload
            val allChunksValid = chunks.all { verifyChunk(it) }
            if (!allChunksValid) return@withContext false

            // Upload chunks with multipart
            val multipartBody = okhttp3.MultipartBody.Builder()
                .setType(okhttp3.MultipartBody.FORM)
                .addFormDataPart("session_id", "temp_session")  // Placeholder, will be set properly later

            for (chunk in chunks) {
                multipartBody.addFormDataPart(
                    "chunk_${chunk.chunkIndex}",
                    "chunk_${chunk.chunkIndex}.bin",
                    okhttp3.RequestBody.create(okhttp3.MediaType.parse("application/octet-stream"), chunk.data)
                ).addFormDataPart("hmac_${chunk.chunkIndex}", chunk.hmac)
                .addFormDataPart("sha256_${chunk.chunkIndex}", chunk.sha256)
            }

            val request = Request.Builder()
                .url(url)
                .post(multipartBody.build())
                .build()

            val response: Response = client.newCall(request).execute()
            val success = response.isSuccessful
            response.close()
            success
        } catch (e: IOException) {
            false
        }
    }

    suspend fun uploadVideos(url: String, selfieFile: File, idFile: File): String? = withContext(Dispatchers.IO) {
        try {
            // Check media integrity
            val selfieIntegrity = checkMediaIntegrity(selfieFile)
            val idIntegrity = checkMediaIntegrity(idFile)
            if (!selfieIntegrity.overallValid || !idIntegrity.overallValid) {
                return@withContext null
            }

            val client = createSecureHttpClient()

            // Read files
            val selfieData = selfieFile.readBytes()
            val idData = idFile.readBytes()

            // Compute HMAC and SHA256 for whole files
            val selfieHmac = computeHmac(selfieData)
            val selfieSha256 = computeSha256(selfieData)
            val idHmac = computeHmac(idData)
            val idSha256 = computeSha256(idData)

            // Create multipart body
            val multipartBody = okhttp3.MultipartBody.Builder()
                .setType(okhttp3.MultipartBody.FORM)
                .addFormDataPart(
                    "selfie",
                    selfieFile.name,
                    okhttp3.RequestBody.create(okhttp3.MediaType.parse("video/mp4"), selfieData)
                )
                .addFormDataPart("selfie_hmac", selfieHmac)
                .addFormDataPart("selfie_sha256", selfieSha256)
                .addFormDataPart(
                    "id_video",
                    idFile.name,
                    okhttp3.RequestBody.create(okhttp3.MediaType.parse("video/mp4"), idData)
                )
                .addFormDataPart("id_hmac", idHmac)
                .addFormDataPart("id_sha256", idSha256)
                .build()

            val request = Request.Builder()
                .url(url)
                .post(multipartBody)
                .build()

            val response: Response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val responseBody = response.body()?.string()
                response.close()
                responseBody
            } else {
                response.close()
                null
            }
        } catch (e: IOException) {
            null
        }
    }

    private fun chunkFile(file: File, chunkSize: Int): List<ByteArray> {
        val chunks = mutableListOf<ByteArray>()
        FileInputStream(file).use { fis ->
            val buffer = ByteArray(chunkSize)
            var bytesRead: Int
            while (fis.read(buffer).also { bytesRead = it } != -1) {
                chunks.add(buffer.copyOf(bytesRead))
            }
        }
        return chunks
    }
}