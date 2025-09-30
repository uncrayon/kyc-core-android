from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import random
import json

app = FastAPI(title="MRZ Parsing Service", version="1.0.0")

@app.post("/parse")
async def parse_mrz(payload: dict):
    """
    Parse MRZ data from OCR text using PassportEye
    """
    try:
        session_id = payload.get("session_id")
        ocr_text = payload.get("ocr_text", "")

        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")

        # Mock MRZ parsing - in real implementation this would use PassportEye
        # to parse MRZ data from the OCR text
        mock_mrz_data = {
            "type": "P",
            "country": "USA",
            "number": "P123456789",
            "check_number": "8",
            "nationality": "USA",
            "birth_date": "900101",
            "check_birth": "7",
            "sex": "M",
            "expiration_date": "300101",
            "check_expiration": "1",
            "personal_number": "<<<<<<<<<<<<<<",
            "check_personal": "<",
            "check_composite": "8"
        }

        mock_parsed_fields = {
            "document_type": "passport",
            "issuing_country": "United States",
            "document_number": "P123456789",
            "surname": "DOE",
            "given_names": "JOHN",
            "nationality": "American",
            "date_of_birth": "1990-01-01",
            "sex": "Male",
            "expiration_date": "2030-01-01"
        }

        valid = random.choice([True, True, False])  # Mostly valid

        result = {
            "session_id": session_id,
            "mrz_data": mock_mrz_data,
            "parsed_fields": mock_parsed_fields,
            "valid": valid,
            "analysis": {
                "method": "passporteye_mrz_parser",
                "text_length": len(ocr_text),
                "mrz_found": valid,
                "confidence": round(random.uniform(0.8, 0.99), 3) if valid else 0.0
            }
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MRZ parsing failed: {str(e)}")



@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return "# Metrics not implemented yet\n"
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mrz_svc"}
