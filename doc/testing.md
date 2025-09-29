# Testing Guidelines

This document outlines testing procedures for the Android KYC Video PoC.

## 5.1 Local Android Testing

- **Installation**: Use `adb` to install the PoC APK on device/emulator.
- **Developer Panel**: Run with `--dev-panel` flag or triple tap version to expose parameter sliders for on-device tuning.
- **Edge Cases**: Test under various lighting (bright, dim), devices (different cameras), and conditions (motion, blur).
- **Localization**: Verify all UI messages are in Mexican Spanish; no English strings in final UI.

## 5.2 Server Testing

- **Startup**: Run `make run` to start Docker Compose stack.
- **Red Team Injection**: Use `scripts/seed_red_team.py` to inject test sessions.
- **Parameter Adjustment**: Modify `config.yaml`, then `make reload-config` to apply without restart.
- **Dashboard**: View metrics at `http://localhost:3000` (Grafana).

## 5.3 Metrics Dashboard

Monitor these key metrics:
- PAD score distribution
- Replay score distribution
- Face match ROC curve
- MRZ success rate
- Latency percentiles (p50/p95)
- Session error rates

## Parameter Adjustment Philosophy

- **On-device Prechecks**: Use debug panel for quick tuning.
- **Server Thresholds**: Edit `config.yaml` and reload.
- **Red Team Tuning**: Run `scripts/benchmark_red_team.py` to evaluate changes.

## Success Criteria

Ensure KPIs are met:
- Crash-free sessions ≥ 99.5%
- End-to-end latency ≤ 8s on Wi-Fi
- PAD TPR@FPR=1e-2 ≥ 0.95
- Face match ROC-AUC ≥ 0.98
- MRZ checksum pass ≥ 95%
- Red-team rejection ≥ 85-90%

## Red Team Dataset

Create and test with 60-80 videos:
- Print attacks
- Screen replays
- Mask attempts
- Fake documents (on-screen/printed)
- Re-encoded media

Label the dataset for evaluation.