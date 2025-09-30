package com.example.pockyc.precheck

import android.content.Context
import android.graphics.Bitmap
import android.graphics.RectF
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.facedetector.FaceDetector
import org.opencv.android.Utils
import org.opencv.core.Core
import org.opencv.core.CvType
import org.opencv.core.Mat
import org.opencv.core.MatOfDouble
import org.opencv.core.MatOfPoint
import org.opencv.core.MatOfPoint2f
import org.opencv.core.Rect
import org.opencv.core.Size
import org.opencv.imgproc.Imgproc
import org.opencv.video.Video
import kotlin.math.max
import kotlin.math.min

class PrecheckManager {

    @Volatile
    private var faceDetector: FaceDetector? = null
    private var previousFrameGray: Mat? = null
    private val frameResults = mutableListOf<FrameResult>()

    data class FrameResult(
        val blur: Double,
        val exposure: Double,
        val motion: Double,
        val compression: Double,
        val faces: List<FaceInfo>
    )

    data class FaceInfo(
        val boundingBox: RectF,
        val confidence: Double
    )

    fun processFrame(context: Context, bitmap: Bitmap): FrameResult {
        val mat = Mat()
        Utils.bitmapToMat(bitmap, mat)

        val blur = calculateBlur(mat)
        val exposure = calculateExposure(mat)
        val motion = calculateMotion(mat)
        val compression = calculateCompression(mat)
        val faces = detectFaces(context, bitmap)

        val result = FrameResult(blur, exposure, motion, compression, faces)
        frameResults.add(result)
        if (frameResults.size > 120) {
            frameResults.removeAt(0)
        }

        return result
    }

    private fun calculateBlur(mat: Mat): Double {
        val gray = Mat()
        Imgproc.cvtColor(mat, gray, Imgproc.COLOR_BGR2GRAY)
        val laplacian = Mat()
        Imgproc.Laplacian(gray, laplacian, CvType.CV_64F)
        val mean = MatOfDouble()
        val stdDev = MatOfDouble()
        Core.meanStdDev(laplacian, mean, stdDev)
        val stdValue = stdDev.toArray().firstOrNull() ?: 0.0
        return stdValue * stdValue
    }

    private fun calculateExposure(mat: Mat): Double {
        val hsv = Mat()
        Imgproc.cvtColor(mat, hsv, Imgproc.COLOR_BGR2HSV)
        val mean = Core.mean(hsv)
        return mean.`val`[2] // V channel
    }

    private fun calculateMotion(mat: Mat): Double {
        val gray = Mat()
        Imgproc.cvtColor(mat, gray, Imgproc.COLOR_BGR2GRAY)
        val prevGray = previousFrameGray ?: run {
            previousFrameGray = gray
            return 0.0
        }
        val flow = Mat()
        Video.calcOpticalFlowFarneback(prevGray, gray, flow, 0.5, 3, 15, 3, 5, 1.2, 0)
        val flowChannels = mutableListOf<Mat>()
        Core.split(flow, flowChannels)
        val magnitude = Mat()
        Core.magnitude(flowChannels[0], flowChannels[1], magnitude)
        val meanMagnitude = Core.mean(magnitude)
        flowChannels.forEach { it.release() }
        magnitude.release()
        flow.release()
        prevGray.release()
        previousFrameGray = gray
        return meanMagnitude.`val`[0]
    }

    private fun calculateCompression(mat: Mat): Double {
        // Simple heuristic: check for block artifacts by looking at variance in small blocks
        val blockSize = 8
        var totalVariance = 0.0
        val gray = Mat()
        Imgproc.cvtColor(mat, gray, Imgproc.COLOR_BGR2GRAY)
        val rows = gray.rows() / blockSize
        val cols = gray.cols() / blockSize
        if (rows == 0 || cols == 0) return 0.0
        for (i in 0 until rows) {
            for (j in 0 until cols) {
                val roi = Rect(j * blockSize, i * blockSize, blockSize, blockSize)
                val block = Mat(gray, roi)
                val mean = MatOfDouble()
                val stdDev = MatOfDouble()
                Core.meanStdDev(block, mean, stdDev)
                val stdValue = stdDev.toArray().firstOrNull() ?: 0.0
                totalVariance += stdValue * stdValue
            }
        }
        return totalVariance / (rows * cols)
    }

    private fun detectFaces(context: Context, bitmap: Bitmap): List<FaceInfo> {
        val detector = ensureFaceDetector(context)
        val image = BitmapImageBuilder(bitmap).build()
        val result = detector.detect(image)
        return result.detections().map { detection ->
            val boundingBox = RectF(detection.boundingBox())
            val confidence = detection.categories().firstOrNull()?.score()?.toDouble() ?: 0.0
            FaceInfo(boundingBox, confidence)
        }
    }

    private fun ensureFaceDetector(context: Context): FaceDetector {
        val existing = faceDetector
        if (existing != null) {
            return existing
        }
        return synchronized(this) {
            faceDetector ?: run {
                val baseOptions = BaseOptions.builder()
                    .setModelAssetPath("face_detection_short_range.tflite")
                    .build()
                val options = FaceDetector.FaceDetectorOptions.builder()
                    .setBaseOptions(baseOptions)
                    .setRunningMode(RunningMode.IMAGE)
                    .build()
                FaceDetector.createFromOptions(context.applicationContext, options).also {
                    faceDetector = it
                }
            }
        }
    }

    fun checkQualityGates(): Boolean {
        if (frameResults.size < 10) return false // Need at least some frames

        val avgBlur = frameResults.map { it.blur }.average()
        val avgExposure = frameResults.map { it.exposure }.average()
        val maxMotion = frameResults.map { it.motion }.maxOrNull() ?: 0.0
        val avgCompression = frameResults.map { it.compression }.average()

        val blurPass = avgBlur >= Config.BLUR_MIN
        val exposurePass = avgExposure in Config.EXPOSURE_MIN.toDouble()..Config.EXPOSURE_MAX.toDouble()
        val motionPass = maxMotion <= Config.MOTION_MAX
        val compressionPass = avgCompression < 100.0 // Arbitrary threshold

        return blurPass && exposurePass && motionPass && compressionPass
    }

    fun checkFacePresence(): Boolean {
        val totalFrames = frameResults.size
        if (totalFrames == 0) return false
        val framesWithSingleFace = frameResults.count { it.faces.size == 1 }
        val facePresenceRatio = framesWithSingleFace.toDouble() / totalFrames
        val faceConfidences = frameResults.flatMap { it.faces }.map { it.confidence }
        val avgConfidence = if (faceConfidences.isNotEmpty()) faceConfidences.average() else 0.0
        val stabilityPass = avgConfidence >= Config.FACE_STABILITY

        return facePresenceRatio >= 0.9 && stabilityPass
    }

    fun checkIdDetection(mat: Mat): Boolean {
        // Detect quadrilateral (ID card)
        val gray = Mat()
        Imgproc.cvtColor(mat, gray, Imgproc.COLOR_BGR2GRAY)
        Imgproc.GaussianBlur(gray, gray, Size(5.0, 5.0), 0.0)
        val edges = Mat()
        Imgproc.Canny(gray, edges, 50.0, 150.0)
        val contours = mutableListOf<MatOfPoint>()
        Imgproc.findContours(edges, contours, Mat(), Imgproc.RETR_EXTERNAL, Imgproc.CHAIN_APPROX_SIMPLE)

        val quadrilaterals = contours.filter { isQuadrilateral(it) }
        if (quadrilaterals.isEmpty()) return false

        val bestQuad = quadrilaterals.maxByOrNull { Imgproc.contourArea(it) } ?: return false
        val aspectRatio = calculateAspectRatio(bestQuad)
        val aspectPass = aspectRatio in 1.35..1.6

        // Check for MRZ ROI (bottom part)
        val rect = Imgproc.boundingRect(bestQuad)
        val mrzHeight = rect.height / 3
        val mrzRoi = Rect(rect.x, rect.y + rect.height - mrzHeight, rect.width, mrzHeight)
        val mrzMat = Mat(mat, mrzRoi)
        val mrzGray = Mat()
        Imgproc.cvtColor(mrzMat, mrzGray, Imgproc.COLOR_BGR2GRAY)
        val mrzMean = Core.mean(mrzGray).`val`[0]
        val mrzPass = mrzMean < 100.0 // Darker area for MRZ

        return aspectPass && mrzPass
    }

    private fun isQuadrilateral(contour: MatOfPoint): Boolean {
        val approx = MatOfPoint2f()
        val curve = MatOfPoint2f(*contour.toArray())
        Imgproc.approxPolyDP(curve, approx, 0.02 * Imgproc.arcLength(curve, true), true)
        return approx.toArray().size == 4
    }

    private fun calculateAspectRatio(contour: MatOfPoint): Double {
        val rect = Imgproc.boundingRect(contour)
        return max(rect.width, rect.height).toDouble() / min(rect.width, rect.height)
    }

    fun reset() {
        frameResults.clear()
        previousFrameGray = null
    }
}