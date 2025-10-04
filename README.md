# KYC Core Android

Note on licensing: This project is available under the PolyForm Noncommercial v1.0.0 license for non-commercial use. Commercial use requires a paid license — see the project's [LICENSE](LICENSE:1) and [COMMERCIAL_LICENSE_TEMPLATE.md](COMMERCIAL_LICENSE_TEMPLATE.md:1) for details.

## Overview

KYC Core Android is a Proof of Concept (POC) for a Know Your Customer (KYC) system designed to streamline identity verification processes. The project consists of an Android application for capturing documents and facial images, and a server-side backend built with microservices architecture. The backend handles advanced processing tasks such as Optical Character Recognition (OCR), Machine Readable Zone (MRZ) reading, face matching, deepfake detection, document liveness checks, and presentation attack detection.

This POC demonstrates a secure, scalable solution for KYC compliance, integrating mobile capture capabilities with robust server-side analytics to ensure authenticity and prevent fraud.

## Features

- **Document and Face Capture**: Android app with camera integration for capturing ID documents and facial images.
- **OCR Processing**: Extracts text from documents using dedicated OCR microservice.
- **MRZ Reading**: Parses Machine Readable Zones from passports and IDs.
- **Face Matching**: Compares captured faces with document photos for verification.
- **Deepfake Detection**: Identifies synthetic or manipulated facial images.
- **Document Liveness**: Verifies the authenticity of physical documents.
- **Presentation Attack Detection (PAD)**: Detects spoofing attempts using printed photos or masks.
- **Secure Transport**: Encrypted data transmission and device binding for enhanced security.
- **Monitoring and Logging**: Integrated Prometheus and Grafana for system monitoring.

## Architecture

The system is divided into two main components:

### Android Application
- Built with Kotlin and Android SDK.
- Includes modules for camera management, capture state handling, UI components, and secure transport.
- Features pre-check configurations, device binding, and background upload workers.

### Server Backend
- Microservices architecture deployed via Docker Compose.
- Services include:
  - **API Gateway**: Main entry point for client requests (Python/FastAPI).
  - **OCR Service**: Text extraction from images.
  - **MRZ Service**: MRZ data parsing.
  - **Face Match Service**: Facial comparison algorithms.
  - **Deepfake Service**: AI-based deepfake detection.
  - **Document Liveness Service**: Liveness verification for documents.
  - **PAD Service**: Presentation attack detection.
- Database: PostgreSQL for data persistence.
- Worker: Celery-based task queue for asynchronous processing.
- Monitoring: Prometheus for metrics and Grafana for dashboards.

## Setup

### Prerequisites
- Android Studio for building the Android app.
- Docker and Docker Compose for running the server backend.
- Python 3.8+ for local development (if needed).

### Android App Setup

This guide provides step-by-step instructions for setting up and running the Android application using Android Studio.

**Prerequisites**
- **Android Studio**: Make sure you have the latest version of Android Studio installed.
- **Android SDK**: Ensure you have Android SDK Platform 29 (Android 10) or higher installed through the Android Studio SDK Manager.
- **Emulator or Physical Device**: You will need an Android emulator set up in Android Studio or a physical Android device with developer mode enabled.

**Step-by-Step Guide**

1. **Open the Project in Android Studio**:
   - Launch Android Studio.
   - Select "Open an existing project".
   - Navigate to the `android/` directory in the cloned repository and select it.

2. **Sync Gradle**:
   - After opening the project, Android Studio will automatically start syncing the Gradle files. Wait for this process to complete. If you get a "Gradle sync failed" error, check the "Build" tab for more details.

3. **Ensure Gradle Wrapper is Executable** (For command-line builds):
   - If you plan to build from the command line, you need to ensure the Gradle wrapper script is executable. Open a terminal, navigate to the `android/` directory, and run:
     ```bash
     chmod +x gradlew
     ```

4. **Build and Run the App**:
   - **From Android Studio (Recommended)**:
     - Select your target device (emulator or physical device) from the dropdown menu in the toolbar.
     - Click the "Run" button (the green play icon) or use the shortcut `Shift + F10`. Android Studio will build and install the app on your selected device.
   - **From the Command Line (Alternative)**:
     - To build a debug APK, navigate to the `android/` directory and run:
       ```bash
       ./gradlew assembleDebug
       ```
     - To install the APK on a connected device, use `adb`:
       ```bash
       adb install app/build/outputs/apk/debug/app-debug.apk
       ```

### Server Backend Setup

This guide provides step-by-step instructions for setting up and running the server backend using Docker Compose.

**Prerequisites**
- **Docker**: Make sure you have Docker installed and running on your system.
- **Docker Compose**: Ensure you have Docker Compose installed.

**Step-by-Step Guide**

1. **Navigate to the Server Directory**:
   - Open a terminal and navigate to the `server/` directory in the cloned repository.

2. **Run the Server Stack**:
   - Use the `Makefile` for convenience. The `make run` command will build and start all the services in detached mode.
     ```bash
     make run
     ```
   - **Alternative (without Makefile)**: You can also use `docker-compose` directly.
     ```bash
     docker-compose up --build -d
     ```

3. **Verify the Services are Running**:
   - You can check the status of the running containers using:
     ```bash
     docker-compose ps
     ```
   - You should see all the services (api, db, worker, etc.) in the "Up" state.

4. **Access the API**:
   - The API gateway is exposed on port 8000. You can access the API documentation at `http://localhost:8000/docs`.

5. **Access the Monitoring Dashboards**:
   - The Grafana dashboard is available at `http://localhost:3000`. You can log in with the default credentials (admin/admin) to view the monitoring dashboards.

6. **Seed Red Team Data (Optional)**:
   - For testing purposes, you can seed the database with red team data using the following command:
     ```bash
     make seed-red-team
     ```

7. **Stopping the Services**:
   - To stop all the running services, you can use:
     ```bash
     make down
     ```
   - **Alternative (without Makefile)**:
     ```bash
     docker-compose down
     ```

### Configuration
- Server configuration is managed via `server/config.yaml`.
- Adjust environment variables in `docker-compose.yml` as needed for production deployment.

## Contributing

This is a POC project. For contributions, refer to the documentation in the `doc/` directory, including architecture details, project plans, and testing guidelines.

## License

This project is licensed under the PolyForm Noncommercial v1.0.0 license. See the [LICENSE](LICENSE:1) file for the full text. Commercial use requires obtaining a separate paid license; see [COMMERCIAL_LICENSE_TEMPLATE.md](COMMERCIAL_LICENSE_TEMPLATE.md:1) or contact uliarp15@gmail.com.