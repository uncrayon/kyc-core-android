package com.example.pockyc

import android.app.Application
import android.util.Log
import org.opencv.android.OpenCVLoader

class PockycApp : Application() {

    override fun onCreate() {
        super.onCreate()
        if (!OpenCVLoader.initDebug()) {
            Log.e(TAG, "Unable to initialize OpenCV")
        } else {
            Log.i(TAG, "OpenCV initialized successfully")
        }
    }

    companion object {
        private const val TAG = "PockycApp"
    }
}
