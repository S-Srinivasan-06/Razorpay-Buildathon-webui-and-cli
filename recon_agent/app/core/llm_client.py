"""LLM API Client for Gemma and Gemini Models.

Manages raw HTTP requests to Google's Generative Language API using standard
library urllib (zero external HTTP dependencies). Provides structured JSON tool calling
for semantic mapping/similarity and multi-turn conversational chat for the grounded assistant.
"""

import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Tuple

from app.config import DEFAULT_API_KEY
from app.core.constants import REG

# Default model configuration: Gemma 4 31B instruction-tuned
MODEL = os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemma-4-31b-it"))

# Internal telemetry state tracking token counts from the most recent LLM invocation
_last: Dict[str, Any] = {"in": 0, "out": 0, "estimated": False}


def resolve_model_slug(model_name: str) -> str:
    """Normalize model slug for Google Generative Language API endpoints.
    
    Translates common shorthand names to official API endpoint identifiers
    (e.g., 'gemma-4-31b' -> 'gemma-4-31b-it').
    
    Args:
        model_name: Raw model string or alias.
        
    Returns:
        Canonical Google model identifier.
    """
    m = model_name.strip()
    if m in ("gemma-4-31b", "gemma-31b"):
        return "gemma-4-31b-it"
    if m in ("gemma-4b", "gemma-4b-it", "gemma-4-26b"):
        return "gemma-4-26b-a4b-it"
    return m


def get_api_key() -> str:
    """Resolve active API key checking LLM_API_KEY, GEMINI_API_KEY, and .env defaults.
    
    Returns:
        The resolved API key string, or empty string if not configured.
    """
    return os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or DEFAULT_API_KEY


def _extract_json(text: str) -> Dict[str, Any]:
    """Robustly extract a JSON dictionary from raw LLM text output.
    
    Handles raw JSON, markdown-fenced code blocks (```json ... ```), and JSON
    embedded within surrounding text by locating outermost brace boundaries.
    
    Args:
        text: Raw response string from the model.
        
    Returns:
        Parsed JSON dictionary.
        
    Raises:
        json.JSONDecodeError: If no valid JSON object could be parsed.
    """
    text = text.strip()

    # 1. Search inside Markdown code blocks
    if "```" in text:
        blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        for b in blocks:
            b = b.strip()
            if b.startswith("{") and b.endswith("}"):
                try:
                    return json.loads(b)
                except Exception:
                    pass

    # 2. Search for outermost matching curly braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # 3. Direct parse fallback
    return json.loads(text)


def json_chat(tool_name: str, args: Dict[str, Any], timeout: float = 25.0) -> Dict[str, Any]:
    """Invoke an LLM tool with temperature=0.0 and enforce a strict JSON output contract.
    
    Sends a structured prompt requesting only raw JSON without preamble or markdown,
    records token counts and metered USD cost, and parses the extracted JSON.
    
    Args:
        tool_name: Identifier of the tool (e.g., 'mapping_semantic', 'semantic_similarity').
        args: Input arguments dictionary passed to the tool.
        timeout: HTTP request timeout in seconds.
        
    Returns:
        Parsed dictionary output matching the tool's expected schema.
        
    Raises:
        RuntimeError: If no API key is configured.
        Exception: On HTTP errors, network timeouts, or unparseable output.
    """
    key = get_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set — deterministic fallback will be used")

    actual_model = resolve_model_slug(MODEL)

    if tool_name == "mapping_semantic":
        schema_hint = (
            'JSON with keys: {"left_table": str, "right_table": str, "left_key": str, '
            '"right_key": str, "left_amount": str, "right_amount": str, "left_date": str, "right_date": str}'
        )
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
            "temperature": 0.0,
        },
    }

    print(f"  [LLM] Invoking {actual_model} for tool '{tool_name}' ...", flush=True)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())

    raw_msg = d["candidates"][0]["content"]["parts"][0]["text"]
    u = d.get("usageMetadata", {})
    _last["estimated"] = "usageMetadata" not in d
    _last["in"] = u.get("promptTokenCount", len(prompt) // 4)
    _last["out"] = u.get("candidatesTokenCount", len(raw_msg) // 4)
    print(
        f"  [LLM] Received response from {actual_model} "
        f"({_last['in']} in / {_last['out']} out tokens | cost: ${last_cost_usd():.6f})",
        flush=True,
    )

    return _extract_json(raw_msg)


def conversational_chat(
    messages: List[Dict[str, str]],
    system_instruction: str,
    timeout: float = 25.0,
) -> Tuple[str, float]:
    """Execute multi-turn conversation grounded strictly in current session dataset context.
    
    Transmits conversation history and dataset grounding instructions to Gemma/Gemini,
    computes call cost using configured per-1k-token rates, and returns the reply.
    
    Args:
        messages: List of message dicts with 'role' ('user'/'assistant') and 'content'.
        system_instruction: Grounded reconciliation context and factual constraints.
        timeout: HTTP request timeout in seconds.
        
    Returns:
        Tuple of (assistant_reply_text, call_cost_usd).
        
    Raises:
        RuntimeError: If API key is not configured.
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
            "parts": [{"text": msg.get("content", "")}],
        })

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{actual_model}:generateContent?key={key}"
    payload = {
        "system_instruction": {
            "parts": [{
                "text": (
                    system_instruction
                    + "\n\nCRITICAL INSTRUCTION: Reply directly to the user as the assistant. "
                    "Do NOT output internal thoughts, reasoning steps, or notes analyzing the prompt. "
                    "Provide ONLY the final, polished response directly to the user."
                )
            }]
        },
        "contents": formatted_contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())

    raw_reply = d["candidates"][0]["content"]["parts"][0]["text"].strip()
    u = d.get("usageMetadata", {})
    t_in = u.get("promptTokenCount", sum(len(m.get("content", "")) for m in messages) // 4)
    t_out = u.get("candidatesTokenCount", len(raw_reply) // 4)
    call_cost = (t_in / 1000 * REG["cost_llm_in_per_1k_usd"]) + (t_out / 1000 * REG["cost_llm_out_per_1k_usd"])

    return raw_reply, call_cost


def last_cost_usd() -> float:
    """Calculate the USD cost of the most recent tool invocation based on metered token counts."""
    return (
        _last["in"] / 1000 * REG["cost_llm_in_per_1k_usd"]
        + _last["out"] / 1000 * REG["cost_llm_out_per_1k_usd"]
    )


def last_estimated() -> bool:
    """Return True if the last invocation's token counts were estimated rather than API-reported."""
    return _last["estimated"]

