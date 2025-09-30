from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import random
import json

app = FastAPI(title="OCR Service", version="1.0.0")

@app.post("/extract")
async def extract_text(payload: dict):
    """
    Extract text from document images using docTR
    """
    try:
        session_id = payload.get("session_id")
        frames = payload.get("frames", [])

        if not session_id or not frames:
            raise HTTPException(status_code=400, detail="session_id and frames are required")

        # Mock OCR extraction - in real implementation this would use docTR
        # to extract text from document images
        mock_texts = [
            "JOHN DOE\nPASSPORT NO: P123456789\nNATIONALITY: UNITED STATES",
            "JANE SMITH\nID CARD\nDOB: 01/01/1990",
            "DRIVER LICENSE\nSTATE OF CALIFORNIA\nDL: A1234567"
        ]

        extracted_text = random.choice(mock_texts)
        confidence = random.uniform(0.7, 0.95)

        result = {
            "session_id": session_id,
            "text": extracted_text,
            "confidence": round(confidence, 3),
            "document_type": "passport" if "PASSPORT" in extracted_text.upper() else "id_card",
            "analysis": {
                "frames_processed": len(frames),
                "method": "docTR_ocr",
                "text_length": len(extracted_text),
                "language_detected": "en"
            }
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")



@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return "# Metrics not implemented yet\n"
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ocr_svc"}
