package com.example.pockyc.precheck

import android.graphics.Bitmap
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.facedetector.FaceDetector
import com.google.mediapipe.tasks.vision.facedetector.FaceDetectorResult
import org.opencv.android.Utils
import org.opencv.core.Core
import org.opencv.core.CvType
import org.opencv.core.Mat
import org.opencv.core.MatOfPoint
import org.opencv.core.MatOfPoint2f
import org.opencv.core.Point
import org.opencv.core.Rect
import org.opencv.core.Scalar
import org.opencv.core.Size
import org.opencv.imgproc.Imgproc
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

class PrecheckManager {

    private val faceDetector: FaceDetector
    private var previousFrame: Mat? = null
    private val frameResults = mutableListOf<FrameResult>()

    init {
        val baseOptions = BaseOptions.builder()
            .setModelAssetPath("face_detection_short_range.tflite") // Assuming model is in assets
            .build()
        val options = FaceDetector.FaceDetectorOptions.builder()
            .setBaseOptions(baseOptions)
            .setRunningMode(RunningMode.IMAGE)
            .build()
        faceDetector = FaceDetector.createFromOptions(options)
    }

    data class FrameResult(
        val blur: Double,
        val exposure: Double,
        val motion: Double,
        val compression: Double,
        val faces: List<FaceInfo>
    )

    data class FaceInfo(
        val landmarks: List<Point>,
        val eyeAspectRatio: Double
    )

    fun processFrame(bitmap: Bitmap): FrameResult {
        val mat = Mat()
        Utils.bitmapToMat(bitmap, mat)

        val blur = calculateBlur(mat)
        val exposure = calculateExposure(mat)
        val motion = calculateMotion(mat)
        val compression = calculateCompression(mat)
        val faces = detectFaces(bitmap)

        val result = FrameResult(blur, exposure, motion, compression, faces)
        frameResults.add(result)

        previousFrame = mat.clone()
        return result
    }

    private fun calculateBlur(mat: Mat): Double {
        val gray = Mat()
        Imgproc.cvtColor(mat, gray, Imgproc.COLOR_BGR2GRAY)
        val laplacian = Mat()
        Imgproc.Laplacian(gray, laplacian, CvType.CV_64F)
        val variance = Core.mean(Core.absdiff(laplacian, Scalar(0.0))).`val`[0]
        return variance
    }

    private fun calculateExposure(mat: Mat): Double {
        val hsv = Mat()
        Imgproc.cvtColor(mat, hsv, Imgproc.COLOR_BGR2HSV)
        val mean = Core.mean(hsv)
        return mean.`val`[2] // V channel
    }

    private fun calculateMotion(mat: Mat): Double {
        if (previousFrame == null) return 0.0
        val flow = Mat()
        Imgproc.calcOpticalFlowFarneback(previousFrame, mat, flow, 0.5, 3, 15, 3, 5, 1.2, 0)
        val meanFlow = Core.mean(flow)
        return meanFlow.`val`[0] + meanFlow.`val`[1] // Sum of x and y
    }

    private fun calculateCompression(mat: Mat): Double {
        // Simple heuristic: check for block artifacts by looking at variance in small blocks
        val blockSize = 8
        var totalVariance = 0.0
        val rows = mat.rows() / blockSize
        val cols = mat.cols() / blockSize
        for (i in 0 until rows) {
            for (j in 0 until cols) {
                val roi = Rect(j * blockSize, i * blockSize, blockSize, blockSize)
                val block = Mat(mat, roi)
                val mean = Core.mean(block)
                val variance = Core.mean(Core.absdiff(block, Scalar(mean.`val`[0], mean.`val`[1], mean.`val`[2]))).`val`[0]
                totalVariance += variance
            }
        }
        return totalVariance / (rows * cols)
    }

    private fun detectFaces(bitmap: Bitmap): List<FaceInfo> {
        val image = BitmapImageBuilder(bitmap).build()
        val result = faceDetector.detect(image)
        return result.detections().map { detection ->
            val landmarks = detection.landmarks().map { Point(it.x().toDouble(), it.y().toDouble()) }
            val eyeAspectRatio = calculateEyeAspectRatio(landmarks)
            FaceInfo(landmarks, eyeAspectRatio)
        }
    }

    private fun calculateEyeAspectRatio(landmarks: List<Point>): Double {
        if (landmarks.size < 6) return 0.0 // Assuming standard face landmarks
        val leftEye = listOf(landmarks[0], landmarks[1], landmarks[2])
        val rightEye = listOf(landmarks[3], landmarks[4], landmarks[5])
        val leftRatio = eyeAspectRatio(leftEye)
        val rightRatio = eyeAspectRatio(rightEye)
        return (leftRatio + rightRatio) / 2.0
    }

    private fun eyeAspectRatio(eye: List<Point>): Double {
        val a = distance(eye[1], eye[5])
        val b = distance(eye[2], eye[4])
        val c = distance(eye[0], eye[3])
        return (a + b) / (2.0 * c)
    }

    private fun distance(p1: Point, p2: Point): Double {
        return kotlin.math.sqrt((p1.x - p2.x) * (p1.x - p2.x) + (p1.y - p2.y) * (p1.y - p2.y))
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
        val framesWithSingleFace = frameResults.count { it.faces.size == 1 }
        val facePresenceRatio = framesWithSingleFace.toDouble() / totalFrames
        val avgStability = frameResults.flatMap { it.faces }.map { it.eyeAspectRatio }.average()
        val stabilityPass = avgStability > 0.18

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
        previousFrame = null
    }
}