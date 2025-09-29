# Quickstart Guide

This guide provides setup and run instructions for the Android KYC Video PoC.

## Prerequisites

- Android Studio for Android development
- Docker and Docker Compose for server
- adb for Android testing
- Git for cloning repositories

## Android Setup

1. Clone the repository and open in Android Studio.
2. Ensure target SDK 29+ (Android 10+).
3. Build the debug APK:

```bash
./gradlew assembleDebug
```

4. Install on device/emulator:

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

5. For developer panel: Triple tap the version number in the app to access parameter sliders.

## Server Setup

1. Ensure Docker and Docker Compose are installed.
2. Run the server stack:

```bash
make run
```

3. Seed red team data for testing:

```bash
make seed-red-team
```

4. Access Grafana dashboard at `http://localhost:3000`.

## Testing

- Run the app and follow the capture flow.
- Check server logs for processing.
- Adjust parameters as needed and reload config with `make reload-config`.

## Localization

User messages are in Mexican Spanish. Ensure `app/src/main/res/values-es-rMX/strings.xml` is populated.

## Monitoring

- Prometheus metrics
- Sentry for errors
- Grafana for dashboards

For detailed testing, see [testing.md](testing.md).