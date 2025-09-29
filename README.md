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
1. Open the `android/` directory in Android Studio.
2. Ensure Gradle wrapper is executable: `chmod +x gradlew`.
3. Build and run the app on an Android device or emulator.

### Server Backend Setup
1. Navigate to the `server/` directory.
2. Run `docker-compose up` to start all services.
3. Access the API at `http://localhost:8000` (default port).
4. Monitoring dashboards available at `http://localhost:3000` (Grafana).

### Configuration
- Server configuration is managed via `server/config.yaml`.
- Adjust environment variables in `docker-compose.yml` as needed for production deployment.

## Contributing

This is a POC project. For contributions, refer to the documentation in the `doc/` directory, including architecture details, project plans, and testing guidelines.

## License

This project is licensed under the PolyForm Noncommercial v1.0.0 license. See the [LICENSE](LICENSE:1) file for the full text. Commercial use requires obtaining a separate paid license; see [COMMERCIAL_LICENSE_TEMPLATE.md](COMMERCIAL_LICENSE_TEMPLATE.md:1) or contact <your-email@example.com>.