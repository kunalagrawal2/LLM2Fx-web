from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from .schemas import Text2FxRequest, Text2FxResponse, ReverbV1, BANDS
from .prompts import build_messages
from .llm import call_openai_chat, parse_json_safe
from .logger import logger

load_dotenv(override=True)

# Debug: Print the API key being used (first 10 chars for security)
import os
api_key = os.getenv("OPENAI_API_KEY", "")
if api_key:
    print(f"🔑 Using OpenAI API key: {api_key[:10]}...{api_key[-4:]}")
    print(f"🔑 API key length: {len(api_key)} characters")
else:
    print("❌ No OpenAI API key found in environment variables")

app = FastAPI(title="LLM2Fx App", version="0.1.0")

@app.get("/healthz")
async def healthz():
    return {"ok": True}

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
