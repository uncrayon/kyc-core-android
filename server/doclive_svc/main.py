from fastapi import FastAPI, HTTPException
import random
import json

app = FastAPI(title="Document Liveness Service", version="1.0.0")

@app.post("/analyze")
async def analyze_document_liveness(payload: dict):
    """
    Analyze document liveness to detect photocopies, screens, etc.
    """
    try:
        session_id = payload.get("session_id")
        frames = payload.get("frames", [])

        if not session_id or not frames:
            raise HTTPException(status_code=400, detail="session_id and frames are required")

        # Mock document liveness analysis - in real implementation this would
        # analyze frames for signs of document tampering, photocopies, digital screens, etc.
        score = random.uniform(0.5, 1.0)  # Mock score between 0.5 and 1.0

        result = {
            "session_id": session_id,
            "score": round(score, 3),
            "threshold": 0.6,
            "passed": score >= 0.6,
            "analysis": {
                "frames_analyzed": len(frames),
                "method": "document_liveness_detection",
                "confidence": round(score, 3),
                "detected_artifacts": random.randint(0, 2),  # Number of suspicious artifacts
                "liveness_indicators": {
                    "texture_analysis": random.choice([True, True, False]),
                    "edge_analysis": random.choice([True, True, False]),
                    "reflection_check": random.choice([True, True, False])
                }
            }
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document liveness analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "doclive_svc"}