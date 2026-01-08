import os
import sys
import json
import datetime
import requests
import shutil
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Zero-Touch Backend API")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory where sample images are stored/uploaded
SAMPLES_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'samples'))
os.makedirs(SAMPLES_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

AUDIO_API_URL = "http://127.0.0.1:8000"

def _allowed(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.get("/vision")
async def vision_endpoint():
    """Proxy to Zero-Touch Assistant Vision State"""
    try:
        res = requests.get(f"{AUDIO_API_URL}/vision/state", timeout=0.5)
        if res.ok:
            data = res.json()
            return {
                "object": data["gaze"]["eye"],
                "confidence": 0.98,
                "timestamp": data["timestamp"],
                "raw": data
            }
    except:
        pass
    return {"object": "None", "confidence": 0.0, "timestamp": datetime.datetime.now().timestamp()}

@app.get("/voice")
async def voice_endpoint():
    """Returns a simple status, actual logic is in main_audio.py"""
    return {"status": "LISTENING", "timestamp": datetime.datetime.now().timestamp()}

# --- Samples & Uploads ---

METADATA_PATH = os.path.join(SAMPLES_DIR, 'metadata.json')

def _read_metadata():
    if not os.path.exists(METADATA_PATH): return {}
    with open(METADATA_PATH, 'r') as f: return json.load(f)

def _write_metadata(md):
    with open(METADATA_PATH, 'w') as f: json.dump(md, f, indent=2)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")
    
    if not _allowed(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    filename = file.filename # In production, use a safe filename utility
    dest = os.path.join(SAMPLES_DIR, filename)
    
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"saved": filename}

@app.get("/samples")
async def list_samples():
    files = [f for f in os.listdir(SAMPLES_DIR) if _allowed(f)]
    return [{"filename": f, "uploaded_at": datetime.datetime.now().isoformat()} for f in files]

@app.get("/samples/{filename}")
async def serve_sample(filename: str):
    path = os.path.join(SAMPLES_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
