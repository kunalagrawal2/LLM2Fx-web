# LLM2Fx App (FastAPI + OpenAI)

**Goal:** Modular, scalable API that converts text mix instructions → reverb JSON parameters (12 gains, 12 decays, mix). Easy to extend to full LLM2Fx with multiple providers and effects.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your OPENAI_API_KEY
./start.sh
# open: http://localhost:8000
```

## Frontend Features
- 🎵 **Audio File Upload** - Drag & drop or click to upload
- 🎛️ **Instrument Selection** - Choose from vocals, guitar, bass, drums, etc.
- 🎚️ **Effect Types** - Reverb, EQ, Compression, Delay, Chorus
- 📝 **Natural Language Instructions** - Describe the sound you want
- 📊 **Real-time Effects Preview** - See AI-generated parameters
- 📥 **Download Processed Audio** - Get your processed file

## API Endpoints
POST /text2fx - Generate effects parameters from text
POST /process-audio - Upload and process audio files
GET / - Frontend interface
GET /healthz - Health check

Design

JSON-only model replies (OpenAI JSON mode).

Strict validation & clamping via Pydantic.

Structured logging (JSON) for easy debugging.

Small prompt, few-shot, schema inline → low tokens, low errors.

Extend

Add EQ schema to schemas.py, expand prompts in prompts.py.

Add /features endpoint to compute DSP stats for the prompt.

Swap model provider by editing llm.py (keep function signature).
