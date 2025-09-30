from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import random
import json

app = FastAPI(title="Face Matching Service", version="1.0.0")

@app.post("/match")
async def match_faces(payload: dict):
    """
    Match faces between video frames and ID photo using InsightFace
    Returns cosine similarity score
    """
    try:
        session_id = payload.get("session_id")
        face_frames = payload.get("face_frames", [])
        id_photo_path = payload.get("id_photo_path")

        if not session_id or not face_frames or not id_photo_path:
            raise HTTPException(status_code=400, detail="session_id, face_frames, and id_photo_path are required")

        # Mock face matching - in real implementation this would use InsightFace
        # to extract embeddings from face_frames and id_photo, then compute similarity
        cosine_similarity = random.uniform(0.3, 1.0)  # Mock similarity between 0.3 and 1.0

        result = {
            "session_id": session_id,
            "cosine_similarity": round(cosine_similarity, 3),
            "threshold": 0.35,
            "passed": cosine_similarity >= 0.35,
            "analysis": {
                "face_frames_count": len(face_frames),
                "id_photo_path": id_photo_path,
                "method": "insightface_cosine_similarity",
                "face_detected": random.choice([True, True, True, False]),  # Mostly successful
                "face_image_path": face_frames[:2] if cosine_similarity >= 0.35 else []
            }
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face matching failed: {str(e)}")



@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return "# Metrics not implemented yet\n"
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "facematch_svc"}
