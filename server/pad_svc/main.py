from fastapi import FastAPI, HTTPException
import random
import json
import numpy as np
from typing import List, Dict, Optional
import cv2
from datetime import datetime

app = FastAPI(title="PAD Service", version="1.0.0")

class MultiSignalPAD:
    def __init__(self):
        # Initialize mock models - in real implementation these would be actual ML models
        self.texture_cnn = MockTextureCNN()
        self.temporal_analyzer = MockTemporalAnalyzer()
        self.rppg_analyzer = MockRPPGAnalyzer()

    def analyze_texture(self, frames: List[np.ndarray]) -> float:
        """Analyze facial texture using CNN for signs of spoofing"""
        return self.texture_cnn.predict(frames)

    def analyze_temporal(self, frames: List[np.ndarray]) -> Dict[str, float]:
        """Analyze temporal patterns (blinks, head movements)"""
        return self.temporal_analyzer.analyze(frames)

    def analyze_rppg(self, frames: List[np.ndarray]) -> Optional[float]:
        """Analyze remote photoplethysmography (optional)"""
        return self.rppg_analyzer.analyze(frames)

class MockTextureCNN:
    def predict(self, frames: List[np.ndarray]) -> float:
        """Mock texture analysis - returns liveness score based on texture consistency"""
        if not frames:
            return 0.0
        # Simulate texture analysis - real attacks have inconsistent textures
        base_score = random.uniform(0.3, 0.9)
        # Add some variance based on frame count
        variance = min(len(frames) / 100.0, 0.2)
        return max(0.0, min(1.0, base_score + random.uniform(-variance, variance)))

class MockTemporalAnalyzer:
    def analyze(self, frames: List[np.ndarray]) -> Dict[str, float]:
        """Mock temporal analysis for blinks and head movements"""
        blink_score = random.uniform(0.4, 0.95)  # Blink pattern consistency
        head_movement_score = random.uniform(0.5, 0.9)  # Natural head movements
        overall_temporal = (blink_score + head_movement_score) / 2.0

        return {
            "blink_consistency": blink_score,
            "head_movement_naturalness": head_movement_score,
            "overall_temporal": overall_temporal
        }

class MockRPPGAnalyzer:
    def analyze(self, frames: List[np.ndarray]) -> Optional[float]:
        """Mock rPPG analysis - detects blood flow patterns"""
        if len(frames) < 30:  # Need sufficient frames for rPPG
            return None

        # Simulate rPPG signal detection
        # Real attacks often lack proper blood flow signals
        rppg_score = random.uniform(0.2, 0.85)
        return rppg_score

@app.post("/analyze")
async def analyze_pad(payload: dict):
    """
    Enhanced Multi-Signal Presentation Attack Detection
    Analyzes texture, temporal patterns, and optional rPPG signals
    """
    try:
        session_id = payload.get("session_id")
        frames_data = payload.get("frames", [])
        enable_rppg = payload.get("enable_rppg", True)

        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")

        # Initialize multi-signal PAD analyzer
        pad_analyzer = MultiSignalPAD()

        # Convert frame data to numpy arrays (mock conversion)
        frames = []
        for frame_data in frames_data:
            if isinstance(frame_data, dict) and 'data' in frame_data:
                # Mock frame processing - in real implementation, decode base64 or process binary data
                frame = np.random.rand(480, 640, 3)  # Mock RGB frame
                frames.append(frame)

        if not frames:
            raise HTTPException(status_code=400, detail="No valid frames provided")

        # Perform multi-signal analysis
        texture_score = pad_analyzer.analyze_texture(frames)
        temporal_results = pad_analyzer.analyze_temporal(frames)
        rppg_score = pad_analyzer.analyze_rppg(frames) if enable_rppg else None

        # Combine scores with weights
        weights = {
            'texture': 0.4,
            'temporal': 0.4,
            'rppg': 0.2 if rppg_score is not None else 0.0
        }

        combined_score = (
            texture_score * weights['texture'] +
            temporal_results['overall_temporal'] * weights['temporal']
        )

        if rppg_score is not None:
            combined_score += rppg_score * weights['rppg']

        # Normalize score
        combined_score = max(0.0, min(1.0, combined_score))

        # Determine pass/fail with hysteresis
        threshold = 0.65  # Slightly higher threshold for multi-signal
        passed = combined_score >= threshold

        result = {
            "session_id": session_id,
            "score": round(combined_score, 3),
            "threshold": threshold,
            "passed": passed,
            "analysis": {
                "frame_count": len(frames),
                "method": "multi_signal_pad",
                "signals_analyzed": {
                    "texture_cnn": round(texture_score, 3),
                    "temporal_blink": round(temporal_results["blink_consistency"], 3),
                    "temporal_head": round(temporal_results["head_movement_naturalness"], 3),
                    "rppg": round(rppg_score, 3) if rppg_score else None
                },
                "weights": weights,
                "confidence": round(combined_score, 3),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PAD analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pad_svc"}