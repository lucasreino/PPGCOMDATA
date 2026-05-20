"""Cliente unificado para extração estruturada e texto (Gemini ou OpenAI-compatible)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger("ppgcomdata.llm_client")

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _provider() -> str:
    return (settings.AI_PROVIDER or "openai").strip().lower()


def _is_openai_family() -> bool:
    return _provider() in ("openai", "openai_compatible", "gpt")


def _openai_base_url() -> str:
    base = (settings.AI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
    return base


def _prepare_openai_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Ajusta JSON Schema do Pydantic para structured outputs (strict)."""

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            out = {k: walk(v) for k, v in node.items() if k not in ("$defs", "definitions")}
            if out.get("type") == "object" and "properties" in out:
                out["additionalProperties"] = False
                props = out["properties"]
                if props and "required" not in out:
                    out["required"] = list(props.keys())
            return out
        if isinstance(node, list):
            return [walk(item) for item in node]
        return node

    return walk(schema)


def _request_with_retry(
    *,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: float = 90.0,
    max_attempts: int = 5,
) -> httpx.Response:
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                if response.status_code in _RETRYABLE_STATUS and attempt < max_attempts - 1:
                    wait = min(90, 8 * (2**attempt))
                    logger.warning(
                        "Rate limit/erro %s em %s. Aguardando %ss...",
                        response.status_code,
                        _provider(),
                        wait,
                    )
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code in _RETRYABLE_STATUS and attempt < max_attempts - 1:
                wait = min(90, 8 * (2**attempt))
                time.sleep(wait)
                continue
            raise
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts - 1:
                time.sleep(min(30, 4 * (2**attempt)))
                continue
            raise last_error from exc
    raise RuntimeError(f"Falha após {max_attempts} tentativas: {last_error}")


def _gemini_structured(
    system_prompt: str,
    user_prompt: str,
    schema_dict: Dict[str, Any],
) -> Dict[str, Any]:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.AI_MODEL}:generateContent?key={settings.AI_API_KEY}"
    )
    payload = {
        "contents": [
            {"parts": [{"text": system_prompt}, {"text": user_prompt}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema_dict,
        },
    }
    response = _request_with_retry(
        url=url,
        headers={"Content-Type": "application/json"},
        payload=payload,
    )
    content_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(content_text)


def _openai_structured(
    system_prompt: str,
    user_prompt: str,
    schema_dict: Dict[str, Any],
) -> Dict[str, Any]:
    url = f"{_openai_base_url()}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.AI_API_KEY}",
    }
    prepared = _prepare_openai_schema(schema_dict)
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "lattes_extraction",
                "strict": True,
                "schema": prepared,
            },
        },
    }
    try:
        response = _request_with_retry(url=url, headers=headers, payload=payload)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 400:
            logger.warning(
                "OpenAI json_schema strict falhou; tentando json_object: %s",
                exc.response.text[:300],
            )
            payload.pop("response_format", None)
            payload["response_format"] = {"type": "json_object"}
            response = _request_with_retry(url=url, headers=headers, payload=payload)
        else:
            raise
    content_text = response.json()["choices"][0]["message"]["content"]
    return json.loads(content_text)


def get_structured_output(
    system_prompt: str,
    user_prompt: str,
    schema_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """Chama o provedor configurado e retorna dict parseado do JSON."""
    if not settings.AI_API_KEY:
        raise ValueError("AI_API_KEY não configurada")

    if _is_openai_family():
        result = _openai_structured(system_prompt, user_prompt, schema_dict)
    elif _provider() == "gemini":
        result = _gemini_structured(system_prompt, user_prompt, schema_dict)
    else:
        raise ValueError(f"AI_PROVIDER desconhecido: {settings.AI_PROVIDER}")

    delay = float(getattr(settings, "AI_REQUEST_DELAY_SECONDS", 0) or 0)
    if delay > 0:
        time.sleep(delay)
    return result


def generate_text(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.2,
) -> str:
    """Gera texto livre (relatórios executivos)."""
    if not settings.AI_API_KEY:
        raise ValueError("AI_API_KEY não configurada")

    if _is_openai_family():
        url = f"{_openai_base_url()}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.AI_API_KEY}",
        }
        payload = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        response = _request_with_retry(url=url, headers=headers, payload=payload, timeout=120.0)
        return response.json()["choices"][0]["message"]["content"]

    if _provider() == "gemini":
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.AI_MODEL}:generateContent?key={settings.AI_API_KEY}"
        )
        payload = {
            "contents": [{"parts": [{"text": system_prompt}, {"text": user_prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        response = _request_with_retry(
            url=url,
            headers={"Content-Type": "application/json"},
            payload=payload,
            timeout=120.0,
        )
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    raise ValueError(f"AI_PROVIDER desconhecido: {settings.AI_PROVIDER}")


def provider_label() -> str:
    if _is_openai_family():
        return f"openai/{settings.AI_MODEL}"
    if _provider() == "gemini":
        return f"gemini/{settings.AI_MODEL}"
    return settings.AI_MODEL
