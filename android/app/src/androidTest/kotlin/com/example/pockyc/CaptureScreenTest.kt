package com.example.pockyc

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import androidx.test.uiautomator.UiSelector
import com.example.pockyc.ui.CaptureScreen
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class CaptureScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun whenCameraPermissionDenied_displaysPermissionDeniedText() {
        // Start the app
        composeTestRule.setContent {
            CaptureScreen()
        }

        // Deny the camera permission dialog
        val device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        val denyButton = device.findObject(UiSelector().text("Deny"))
        if (denyButton.exists() && denyButton.isEnabled) {
            denyButton.click()
        }

        // Check that the permission denied text is displayed
        composeTestRule.onNodeWithText("Camera permission denied. Please enable it in settings to continue.").assertExists()
    }
}