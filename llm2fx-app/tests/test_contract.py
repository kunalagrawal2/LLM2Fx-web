import asyncio
from app.prompts import build_messages
from app.llm import parse_json_safe

def test_parse_json_safe_ok():
    assert parse_json_safe('{"a":1}') == {"a":1}

def test_parse_json_safe_bad():
    assert parse_json_safe('not json') is None

def test_messages_shape():
    msgs = build_messages("reverb", "warm small room", "vocal")
    # system + 3 fewshots * 2 (user/assistant) + final user = 1 + 6 + 1 = 8
    assert len(msgs) == 8
    assert msgs[0]["role"] == "system"
    assert msgs[-1]["role"] == "user"
