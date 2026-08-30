import json
import os
import re
import urllib.request
from typing import List, Dict, Tuple

from app.config import DEFAULT_API_KEY
from app.core.constants import REG

# Model configuration: Gemma 4 31B
MODEL = os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemma-4-31b-it"))

_last = {"in": 0, "out": 0, "estimated": False}


def resolve_model_slug(model_name: str) -> str:
    """Normalize model slug for Google Generative Language API endpoints."""
    m = model_name.strip()
    if m in ("gemma-4-31b", "gemma-31b"):
        return "gemma-4-31b-it"
    if m in ("gemma-4b", "gemma-4b-it", "gemma-4-26b"):
        return "gemma-4-26b-a4b-it"
    return m


def get_api_key() -> str:
    return os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or DEFAULT_API_KEY


def _extract_json(text: str) -> dict:
    text = text.strip()
    if "```" in text:
        blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        for b in blocks:
            b = b.strip()
            if b.startswith("{") and b.endswith("}"):
                try:
                    return json.loads(b)
                except Exception:
                    pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    return json.loads(text)


def json_chat(tool_name: str, args: dict, timeout: float = 25.0) -> dict:
    key = get_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set — deterministic fallback will be used")

    actual_model = resolve_model_slug(MODEL)

    if tool_name == "mapping_semantic":
        schema_hint = 'JSON with keys: {"left_table": str, "right_table": str, "left_key": str, "right_key": str, "left_amount": str, "right_amount": str, "left_date": str, "right_date": str}'
    elif tool_name == "semantic_similarity":
        schema_hint = 'JSON with keys: {"score": float (0.0 to 1.0)}'
    else:
        schema_hint = "a valid JSON object matching the tool parameters"

    prompt = (
        f"You are the financial reconciliation system tool '{tool_name}'.\n"
        f"Strict Requirement: Output ONLY a single raw JSON object ({schema_hint}).\n"
        f"Do NOT include explanations, markdown wrappers, preamble, or thoughts.\n\n"
        f"Input Data:\n{json.dumps(args, default=str)}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{actual_model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0
        }
    }

    print(f"  [LLM] Invoking {actual_model} for tool '{tool_name}' ...", flush=True)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())

    raw_msg = d["candidates"][0]["content"]["parts"][0]["text"]
    u = d.get("usageMetadata", {})
    _last["estimated"] = "usageMetadata" not in d
    _last["in"] = u.get("promptTokenCount", len(prompt) // 4)
    _last["out"] = u.get("candidatesTokenCount", len(raw_msg) // 4)
    print(f"  [LLM] Received response from {actual_model} ({_last['in']} in / {_last['out']} out tokens | cost: ${last_cost_usd():.6f})", flush=True)

    return _extract_json(raw_msg)


def conversational_chat(messages: List[Dict[str, str]], system_instruction: str, timeout: float = 25.0) -> Tuple[str, float]:
    """
    Multi-turn conversation with Gemma 4 31B grounded strictly in current active session context.
    Returns (assistant_reply, cost_usd).
    """
    key = get_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")

    actual_model = resolve_model_slug(MODEL)

    formatted_contents = []
    for msg in messages:
        role = "user" if msg.get("role") in ("user", "human") else "model"
        formatted_contents.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}]
        })

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{actual_model}:generateContent?key={key}"
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction + "\n\nCRITICAL INSTRUCTION: Reply directly to the user as the assistant. Do NOT output internal thoughts, reasoning steps, or notes analyzing the prompt. Provide ONLY the final, polished response directly to the user."}]
        },
        "contents": formatted_contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())

    raw_reply = d["candidates"][0]["content"]["parts"][0]["text"].strip()
    u = d.get("usageMetadata", {})
    t_in = u.get("promptTokenCount", sum(len(m.get('content', '')) for m in messages) // 4)
    t_out = u.get("candidatesTokenCount", len(raw_reply) // 4)
    call_cost = (t_in / 1000 * REG["cost_llm_in_per_1k_usd"]) + (t_out / 1000 * REG["cost_llm_out_per_1k_usd"])
    
    return raw_reply, call_cost


def last_cost_usd() -> float:
    return (_last["in"] / 1000 * REG["cost_llm_in_per_1k_usd"]
            + _last["out"] / 1000 * REG["cost_llm_out_per_1k_usd"])


def last_estimated() -> bool:
    return _last["estimated"]
