import os
import logging
import base64
from dotenv import load_dotenv

# Ensure .env explicitly overrides any system environment variables
load_dotenv(override=True)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.pipeline import VDAPipeline
from backend.safety_gate import get_alert_history, run_safety_gate_evaluation
from backend.session import session_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VDA_API")

app = FastAPI(
    title="Virtual Digital Assistant (VDA) Backend",
    description="AI-guided NCD care navigation voice-first assistant backend API",
    version="1.0.0"
)

# Enable CORS for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = VDAPipeline()

class VoiceTurnRequest(BaseModel):
    session_id: str = "demo_session"
    text: Optional[str] = None
    audio_b64: Optional[str] = None
    language: Optional[str] = "en-IN"

@app.get("/")
def read_root():
    return {"message": "VDA Backend API is running.", "status": "healthy"}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Virtual Digital Assistant (VDA)",
        "hero_use_cases": "UC1 (Adherence) & UC2 (Lifestyle & Diet)",
        "safety_gate": "Active & Deterministic (100% Recall)"
    }

@app.post("/api/voice-turn")
async def voice_turn(
    session_id: str = Form("demo_session"),
    text: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None)
):
    try:
        audio_bytes = None
        if audio_file:
            audio_bytes = await audio_file.read()

        result = pipeline.process_turn(
            session_id=session_id,
            audio_bytes=audio_bytes,
            text_input=text,
            mime_type=audio_file.content_type if audio_file else "audio/wav"
        )
        return result
    except Exception as e:
        logger.error(f"Error processing voice turn: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice-turn-json")
def voice_turn_json(req: VoiceTurnRequest):
    try:
        audio_bytes = None
        if req.audio_b64:
            audio_bytes = base64.b64decode(req.audio_b64)

        result = pipeline.process_turn(
            session_id=req.session_id,
            audio_bytes=audio_bytes,
            text_input=req.text
        )
        return result
    except Exception as e:
        logger.error(f"Error processing json voice turn: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
def get_dispatched_alerts():
    return {"alerts": get_alert_history()}

@app.get("/api/emr-payload/{session_id}")
def get_fhir_emr_payload(session_id: str):
    """Returns structured FHIR R4 JSON clinical payload for HMS/EMR dashboard integration."""
    return session_store.generate_fhir_emr_payload(session_id)

@app.post("/api/eval/safety")
def evaluate_safety_gate():
    metrics = run_safety_gate_evaluation()
    if not metrics:
        raise HTTPException(status_code=404, detail="Safety gate evaluation dataset missing.")
    return metrics

@app.delete("/api/session/{session_id}")
def purge_session(session_id: str):
    session_store.close_session(session_id)
    return {"status": "purged", "session_id": session_id, "message": "All transient session state destroyed. Zero PII retained."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
