from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from .schemas import Text2FxRequest, Text2FxResponse, ReverbV1, BANDS
from .prompts import build_messages
from .llm import call_openai_chat, parse_json_safe
from .logger import logger
from .audio_processor import process_audio_with_effects

load_dotenv(override=True)

# Setup upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Debug: Print the API key being used (first 10 chars for security)
import os
api_key = os.getenv("OPENAI_API_KEY", "")
if api_key:
    print(f"🔑 Using OpenAI API key: {api_key[:10]}...{api_key[-4:]}")
    print(f"🔑 API key length: {len(api_key)} characters")
else:
    print("❌ No OpenAI API key found in environment variables")

app = FastAPI(title="LLM2Fx App", version="0.1.0")

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
async def frontend():
    """Serve the frontend interface"""
    import os
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
    with open(frontend_path, "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/process-audio")
async def process_audio(
    file: UploadFile = File(...),
    instrument: str = Form(...),
    fx_type: str = Form(...),
    instruction: str = Form(...)
):
    """Process uploaded audio file with AI-generated effects"""
    try:
        # Save uploaded file
        file_location = UPLOAD_DIR / file.filename
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get effects parameters from LLM
        fx_request = Text2FxRequest(
            instrument=instrument,
            fx_type=fx_type,
            instruction=instruction
        )
        
        # Call the existing text2fx endpoint logic
        messages = build_messages(fx_request.fx_type, fx_request.instruction, fx_request.instrument)
        
        raw_text = await call_openai_chat(messages, force_json=True)
        raw = parse_json_safe(raw_text)
        
        if raw is None:
            raise HTTPException(status_code=502, detail="Failed to generate effects parameters")
        
        # Apply real audio processing with AI-generated effects
        processed_filename = f"processed_{file.filename}"
        processed_location = UPLOAD_DIR / processed_filename
        
        # Process the audio with real effects
        success = process_audio_with_effects(
            str(file_location),
            str(processed_location),
            raw
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Audio processing failed")
        
        logger.info("audio_processed", extra={
            "extra": {
                "original_file": file.filename,
                "processed_file": processed_filename,
                "effects": raw
            }
        })
        
        return FileResponse(
            processed_location,
            media_type='application/octet-stream',
            filename=processed_filename
        )
        
    except Exception as e:
        logger.exception("audio_processing_error")
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")

@app.post("/text2fx", response_model=Text2FxResponse)
async def text2fx(req: Text2FxRequest):
    if req.fx_type != "reverb":
        raise HTTPException(status_code=501, detail="MVP supports only fx_type='reverb'")

    messages = build_messages(req.fx_type, req.instruction, req.instrument)

    try:
        # 1st attempt
        raw_text = await call_openai_chat(messages, force_json=True)
        raw = parse_json_safe(raw_text)

        # retry once if not JSON
        if raw is None:
            logger.warning("invalid_json_first_try", extra={"extra": {"len": len(raw_text)}})
            messages[-1]["content"] += "\nRespond with JSON only."
            raw_text = await call_openai_chat(messages, force_json=True)
            raw = parse_json_safe(raw_text)
            if raw is None:
                logger.error("invalid_json_second_try", extra={"extra": {"len": len(raw_text)}})
                raise HTTPException(status_code=502, detail="Model returned non-JSON twice")

        # Normalize & validate to schema
        try:
            # fill missing keys with safe defaults
            reverb = raw.get("reverb", {})
            gains = list(reverb.get("gains_db", [0.0]*BANDS))
            decays = list(reverb.get("decays_s", [1.0]*BANDS))
            mix = float(reverb.get("mix", 0.25))

            # enforce exact length
            gains = (gains + [0.0]*BANDS)[:BANDS]
            decays = (decays + [1.0]*BANDS)[:BANDS]

            rv = ReverbV1(gains_db=gains, decays_s=decays, mix=mix)
            resp = Text2FxResponse(
                schema_version="reverb_v1",
                reverb=rv,
                reason=(raw.get("reason") or None)
            )
            logger.info("ok_response")
            return JSONResponse(status_code=200, content=resp.model_dump())
        except Exception as e:
            logger.exception("validation_error")
            raise HTTPException(status_code=502, detail=f"Validation failed: {e}")
            
    except ValueError as e:
        # Handle OpenAI-specific errors
        logger.error("openai_error", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("unexpected_error")
        raise HTTPException(status_code=500, detail="Internal server error")
