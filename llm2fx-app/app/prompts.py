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
     '{"schema_version":"reverb_v1","reverb":{"gains_db":[2,2,1,1,0,-1,-1,0,1,1,2,2],"decays_s":[1.2,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0,2.1,2.2],"mix":0.6},"reason":"Small room, pronounced effect."}'),
    ('large hall pad, airy',
     '{"schema_version":"reverb_v1","reverb":{"gains_db":[3,3,2,2,1,1,1,1,2,2,3,3],"decays_s":[3.2,3.2,3.4,3.5,3.6,3.8,4.0,4.2,4.3,4.4,4.6,4.8],"mix":0.75},"reason":"Long tail, bright top, very airy."}'),
    ('tight drum room',
     '{"schema_version":"reverb_v1","reverb":{"gains_db":[1,1,1,0,0,0,-1,-2,-2,-2,-2,-2],"decays_s":[0.8,0.8,0.85,0.9,0.95,1.0,1.0,0.95,0.9,0.85,0.8,0.75],"mix":0.5},"reason":"Short decay, rolled highs, tight."}')
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
