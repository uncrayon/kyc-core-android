package com.example.pockyc.security

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import android.provider.Settings
import androidx.annotation.RequiresApi
import com.google.android.gms.tasks.Task
import com.google.android.play.core.integrity.IntegrityManagerFactory
import com.google.android.play.core.integrity.IntegrityTokenRequest
import com.google.android.play.core.integrity.IntegrityTokenResponse
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import java.net.InetAddress
import java.net.NetworkInterface
import java.time.Instant
import java.time.temporal.ChronoUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

class DeviceBindingManager(private val context: Context) {

    private val rateLimiter = mutableMapOf<String, MutableList<Long>>()
    private val maxRequestsPerMinute = 10
    private val sessionStartTime = Instant.now()

    data class DeviceBindingResult(
        val installId: String?,
        val playIntegrityToken: String?,
        val networkAsn: String?,
        val sessionTimeSkew: Long,
        val rateLimitPassed: Boolean,
        val overallPassed: Boolean
    )

    fun getInstallId(): String? {
        return try {
            Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
        } catch (e: Exception) {
            null
        }
    }

    @RequiresApi(Build.VERSION_CODES.M)
    suspend fun checkPlayIntegrity(nonce: String): String? {
        return try {
            val integrityManager = IntegrityManagerFactory.create(context)
            val integrityTokenResponse = suspendCancellableCoroutine<IntegrityTokenResponse> { continuation ->
                val integrityTokenRequest = IntegrityTokenRequest.builder()
                    .setNonce(nonce)
                    .build()

                integrityManager.requestIntegrityToken(integrityTokenRequest)
                    .addOnSuccessListener { response ->
                        continuation.resume(response)
                    }
                    .addOnFailureListener { exception ->
                        continuation.resumeWithException(exception)
                    }
            }

            integrityTokenResponse.token()
        } catch (e: Exception) {
            null
        }
    }

    fun getNetworkAsn(): String? {
        return try {
            val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                val network = connectivityManager.activeNetwork
                val capabilities = connectivityManager.getNetworkCapabilities(network)
                if (capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true ||
                    capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) == true) {
                    // In a real implementation, you'd query an ASN lookup service
                    // For now, return a mock ASN based on network type
                    return if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) "WIFI_ASN_12345" else "CELL_ASN_67890"
                }
            }
            null
        } catch (e: Exception) {
            null
        }
    }

    fun checkSessionTimeSkew(): Long {
        val currentTime = Instant.now()
        return ChronoUnit.MINUTES.between(sessionStartTime, currentTime)
    }

    fun checkRateLimit(identifier: String): Boolean {
        val now = System.currentTimeMillis()
        val windowStart = now - 60000 // 1 minute window

        val requests = rateLimiter.getOrPut(identifier) { mutableListOf() }
        requests.removeAll { it < windowStart }
        requests.add(now)

        return requests.size <= maxRequestsPerMinute
    }

    @RequiresApi(Build.VERSION_CODES.M)
    suspend fun performDeviceBinding(nonce: String, identifier: String): DeviceBindingResult {
        val installId = getInstallId()
        val playIntegrityToken = withTimeoutOrNull(10000) { checkPlayIntegrity(nonce) }
        val networkAsn = getNetworkAsn()
        val sessionTimeSkew = checkSessionTimeSkew()
        val rateLimitPassed = checkRateLimit(identifier)

        val overallPassed = installId != null &&
                           playIntegrityToken != null &&
                           networkAsn != null &&
                           sessionTimeSkew < 2 &&
                           rateLimitPassed

        return DeviceBindingResult(
            installId = installId,
            playIntegrityToken = playIntegrityToken,
            networkAsn = networkAsn,
            sessionTimeSkew = sessionTimeSkew,
            rateLimitPassed = rateLimitPassed,
            overallPassed = overallPassed
        )
    }
}