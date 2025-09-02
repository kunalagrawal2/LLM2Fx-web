# LLM2Fx App (FastAPI + OpenAI)

**Goal:** Modular, scalable API that converts text mix instructions → reverb JSON parameters (12 gains, 12 decays, mix). Easy to extend to full LLM2Fx with multiple providers and effects.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env  # add your OPENAI_API_KEY
bash run.sh
# open: http://localhost:8000/docs

API
POST /text2fx

Request:

{"fx_type":"reverb","instrument":"vocal","instruction":"warm small room"}


Response:

{
  "schema_version":"reverb_v1",
  "reverb":{"gains_db":[...12...],"decays_s":[...12...],"mix":0.25},
  "reason":"..."
}

Design

JSON-only model replies (OpenAI JSON mode).

Strict validation & clamping via Pydantic.

Structured logging (JSON) for easy debugging.

Small prompt, few-shot, schema inline → low tokens, low errors.

Extend

Add EQ schema to schemas.py, expand prompts in prompts.py.

Add /features endpoint to compute DSP stats for the prompt.

Swap model provider by editing llm.py (keep function signature).
