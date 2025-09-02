REVERB_JSON_SCHEMA_SNIPPET = """
{
  "schema_version": "reverb_v1",
  "reverb": {
    "gains_db": [number, ... 12 items total, each between -12 and 12],
    "decays_s": [number, ... 12 items total, each between 0.2 and 6.0],
    "mix": number between 0 and 1
  },
  "reason": "optional string up to 280 chars"
}
""".strip()

SYSTEM_TEMPLATE = """You convert natural-language mixing instructions into JSON parameters for {FX_TYPE}.
Return a single JSON object exactly matching this schema:

{SCHEMA}

No text outside JSON. No comments. No trailing commas.
"""

FEWSHOTS = [
    # Keep tiny to save tokens
    ('intimate vocal, small room',
     '{"schema_version":"reverb_v1","reverb":{"gains_db":[0,0,0,0,-1,-2,-2,-1,0,0,0,0],"decays_s":[0.8,0.8,0.8,0.8,0.9,1.0,1.0,1.0,0.9,0.9,0.8,0.8],"mix":0.20},"reason":"Small room, slight HF damp."}'),
    ('large hall pad, airy',
     '{"schema_version":"reverb_v1","reverb":{"gains_db":[1,1,1,1,0,0,0,0,1,1,2,2],"decays_s":[2.2,2.2,2.4,2.5,2.6,2.8,3.0,3.2,3.3,3.4,3.6,3.8],"mix":0.45},"reason":"Long tail, bright top."}'),
    ('tight drum room',
     '{"schema_version":"reverb_v1","reverb":{"gains_db":[0,0,0,0,0,0,0,-1,-2,-2,-2,-2],"decays_s":[0.4,0.4,0.45,0.5,0.55,0.6,0.6,0.55,0.5,0.45,0.4,0.35],"mix":0.15},"reason":"Short decay, rolled highs."}')
]

def build_messages(fx_type: str, instruction: str, instrument: str) -> list[dict]:
    system = SYSTEM_TEMPLATE.format(FX_TYPE=fx_type, SCHEMA=REVERB_JSON_SCHEMA_SNIPPET)
    messages: list[dict] = [{"role": "system", "content": system}]
    for text, json_example in FEWSHOTS:
        messages.append({"role": "user", "content": text})
        messages.append({"role": "assistant", "content": json_example})
    messages.append({
        "role": "user",
        "content": f'Instruction: "{instruction}"\nInstrument: "{instrument}"\nOutput JSON only.'
    })
    return messages
