"""Cliente unificado para extração estruturada e texto (Gemini ou OpenAI-compatible)."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger("ppgcomdata.llm_client")

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class QuotaExhaustedError(Exception):
    """Cota do provedor/modelo esgotada — tentar próximo modelo na cadeia."""


def _provider() -> str:
    return (settings.AI_PROVIDER or "openai").strip().lower()


def _is_openai_family() -> bool:
    return _provider() in ("openai", "openai_compatible", "gpt")


def _openai_base_url() -> str:
    base = (settings.AI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
    return base


def _is_opencode_go() -> bool:
    base = _openai_base_url()
    return "opencode.ai" in base and "/go" in base


def _is_opencode_zen() -> bool:
    return "opencode.ai" in _openai_base_url()


def _go_uses_messages_api(model: str) -> bool:
    """MiniMax no OpenCode Go usa /messages (formato Anthropic), não chat/completions."""
    return _is_opencode_go() and (model or "").lower().startswith("minimax")


def _model_chain() -> List[str]:
    """Modelo principal + fallbacks (ex.: deepseek-v4-pro, deepseek-v4-flash)."""
    primary = (settings.AI_MODEL or "").strip()
    fallbacks = [
        m.strip()
        for m in (getattr(settings, "AI_FALLBACK_MODELS", "") or "").split(",")
        if m.strip()
    ]
    chain: List[str] = []
    seen: set[str] = set()
    for model in [primary, *fallbacks]:
        key = model.lower()
        if model and key not in seen:
            seen.add(key)
            chain.append(model)
    return chain or [primary or "gpt-4o-mini"]


def _is_quota_exhausted_response(response: httpx.Response) -> bool:
    if response.status_code not in (402, 429):
        return False
    body = (response.text or "").lower()
    markers = (
        "insufficient_quota",
        "quota",
        "exceeded",
        "rate limit",
        "usage limit",
        "billing",
    )
    return any(m in body for m in markers)


def _extract_message_text(message: Dict[str, Any]) -> str:
    content = message.get("content")
    if content and str(content).strip():
        return str(content).strip()
    reasoning = message.get("reasoning")
    if reasoning and str(reasoning).strip():
        return str(reasoning).strip()
    return ""


def _repair_json_text(raw: str) -> str:
    """Correções leves para JSON malformado retornado por alguns modelos."""
    fixed = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw)
    fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
    fixed = re.sub(r"(\{|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1 "\2":', fixed)
    return fixed


def _parse_json_text(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Resposta vazia do modelo")
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    decoder = json.JSONDecoder()

    def _as_dict(obj: Any) -> Dict[str, Any]:
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list):
            return {"__array__": obj}
        raise ValueError(f"JSON esperado como objeto, recebido {type(obj).__name__}")

    def _try_load(candidate: str) -> Dict[str, Any] | None:
        try:
            return _as_dict(json.loads(candidate))
        except json.JSONDecodeError as exc:
            if "Extra data" in str(exc):
                obj, _ = decoder.raw_decode(candidate)
                return _as_dict(obj)
            start = candidate.find("{")
            if start >= 0:
                try:
                    obj, _ = decoder.raw_decode(candidate, start)
                    return _as_dict(obj)
                except json.JSONDecodeError:
                    return None
            return None

    for candidate in (raw, _repair_json_text(raw)):
        parsed = _try_load(candidate)
        if parsed is not None:
            return parsed
    raise ValueError("JSON inválido na resposta do modelo")


def _schema_summary_for_prompt(schema_dict: Dict[str, Any]) -> str:
    """Resumo curto do schema — evita o modelo ecoar o JSON Schema inteiro."""
    props = schema_dict.get("properties") or {}
    lines: List[str] = []
    for key, spec in props.items():
        if not isinstance(spec, dict):
            lines.append(f"- {key}")
            continue
        if key == "lacunas":
            lines.append(
                "- lacunas: lista (pode ser []); cada item: "
                "{tipo_lacuna, descricao, gravidade?, acao_recomendada?}"
            )
            continue
        if spec.get("type") == "array":
            lines.append(f"- {key}: lista de objetos extraídos do texto")
        else:
            lines.append(f"- {key}: {spec.get('type', 'valor')}")
    return "\n".join(lines) if lines else "- objeto JSON com os campos do schema"


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
                if _is_quota_exhausted_response(response):
                    err_body = (response.text or "")[:400]
                    logger.warning(
                        "Cota esgotada (%s) modelo=%s: %s",
                        response.status_code,
                        payload.get("model"),
                        err_body,
                    )
                    raise QuotaExhaustedError(err_body)
                if response.status_code in _RETRYABLE_STATUS and attempt < max_attempts - 1:
                    wait = min(90, 8 * (2**attempt))
                    err_body = (response.text or "")[:400]
                    logger.warning(
                        "Rate limit/erro %s em %s. Aguardando %ss... %s",
                        response.status_code,
                        _provider(),
                        wait,
                        err_body,
                    )
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response
        except QuotaExhaustedError:
            raise
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if _is_quota_exhausted_response(exc.response):
                raise QuotaExhaustedError((exc.response.text or "")[:400]) from exc
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


def _extract_anthropic_text(data: Dict[str, Any]) -> str:
    parts: List[str] = []
    for block in data.get("content") or []:
        if isinstance(block, dict):
            if block.get("type") == "text" and block.get("text"):
                parts.append(str(block["text"]))
            elif block.get("text"):
                parts.append(str(block["text"]))
    return "\n".join(parts).strip()


def _opencode_go_messages_structured(
    system_prompt: str,
    user_prompt: str,
    schema_dict: Dict[str, Any],
    *,
    model: str,
) -> Dict[str, Any]:
    schema_hint = _schema_summary_for_prompt(schema_dict)
    sys_prompt = (
        f"{system_prompt}\n\n"
        "Responda APENAS com JSON válido (sem markdown, sem explicações).\n"
        "NÃO retorne o JSON Schema; retorne somente dados extraídos do currículo.\n"
        f"Campos esperados:\n{schema_hint}"
    )
    url = f"{_openai_base_url()}/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.AI_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": model,
        "max_tokens": 16384,
        "system": sys_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    response = _request_with_retry(url=url, headers=headers, payload=payload)
    content_text = _extract_anthropic_text(response.json())
    if not content_text:
        raise ValueError(f"Resposta Anthropic vazia: {str(response.json())[:400]}")
    return _parse_json_text(content_text)


def _openai_structured(
    system_prompt: str,
    user_prompt: str,
    schema_dict: Dict[str, Any],
    *,
    model: str,
) -> Dict[str, Any]:
    if _go_uses_messages_api(model):
        return _opencode_go_messages_structured(
            system_prompt, user_prompt, schema_dict, model=model
        )

    url = f"{_openai_base_url()}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.AI_API_KEY}",
    }
    schema_hint = _schema_summary_for_prompt(schema_dict)
    sys_prompt = (
        f"{system_prompt}\n\n"
        "Responda APENAS com JSON válido (sem markdown, sem explicações).\n"
        "NÃO retorne o JSON Schema; retorne somente dados extraídos do currículo.\n"
        f"Campos esperados:\n{schema_hint}"
    )

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 16384,
    }

    prepared = _prepare_openai_schema(schema_dict)

    if _is_opencode_zen() or _is_opencode_go():
        payload["response_format"] = {"type": "json_object"}
        response = _request_with_retry(url=url, headers=headers, payload=payload)
    else:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "lattes_extraction",
                "strict": True,
                "schema": prepared,
            },
        }
        try:
            response = _request_with_retry(url=url, headers=headers, payload=payload)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 400:
                logger.warning(
                    "json_schema strict falhou; tentando json_object: %s",
                    exc.response.text[:300],
                )
                payload["response_format"] = {"type": "json_object"}
                payload["messages"][0]["content"] = sys_prompt
                response = _request_with_retry(url=url, headers=headers, payload=payload)
            else:
                raise

    message = response.json()["choices"][0]["message"]
    content_text = _extract_message_text(message)
    if not content_text:
        raise ValueError(f"Resposta sem conteúdo: {str(message)[:400]}")
    return _parse_json_text(content_text)


def get_structured_output(
    system_prompt: str,
    user_prompt: str,
    schema_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """Chama o provedor configurado; em cota esgotada tenta fallbacks (DeepSeek pro/flash)."""
    if not settings.AI_API_KEY:
        raise ValueError("AI_API_KEY não configurada")

    last_error: Exception | None = None
    chain = _model_chain()

    for model in chain:
        try:
            if _is_openai_family():
                result = _openai_structured(
                    system_prompt, user_prompt, schema_dict, model=model
                )
            elif _provider() == "gemini":
                result = _gemini_structured(system_prompt, user_prompt, schema_dict)
            else:
                raise ValueError(f"AI_PROVIDER desconhecido: {settings.AI_PROVIDER}")

            if model != chain[0]:
                logger.info("Extração OK com modelo fallback: %s", model)
            delay = float(getattr(settings, "AI_REQUEST_DELAY_SECONDS", 0) or 0)
            if delay > 0:
                time.sleep(delay)
            return result
        except QuotaExhaustedError as exc:
            last_error = exc
            logger.warning(
                "Cota esgotada em %s — tentando próximo modelo na cadeia", model
            )
            continue
        except httpx.HTTPStatusError as exc:
            if _is_quota_exhausted_response(exc.response):
                last_error = exc
                logger.warning(
                    "Cota/rate limit em %s — tentando próximo modelo", model
                )
                continue
            raise

    raise RuntimeError(
        f"Todos os modelos falharam ({', '.join(chain)}): {last_error}"
    )


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
        last_error: Exception | None = None
        for model in _model_chain():
            try:
                if _go_uses_messages_api(model):
                    url = f"{_openai_base_url()}/messages"
                    headers = {
                        "Content-Type": "application/json",
                        "x-api-key": settings.AI_API_KEY,
                        "anthropic-version": "2023-06-01",
                    }
                    payload = {
                        "model": model,
                        "max_tokens": 8192,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                    }
                    response = _request_with_retry(
                        url=url, headers=headers, payload=payload, timeout=120.0
                    )
                    return _extract_anthropic_text(response.json())

                url = f"{_openai_base_url()}/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.AI_API_KEY}",
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                }
                response = _request_with_retry(
                    url=url, headers=headers, payload=payload, timeout=120.0
                )
                msg = response.json()["choices"][0]["message"]
                return _extract_message_text(msg) or str(msg.get("content") or "")
            except QuotaExhaustedError as exc:
                last_error = exc
                continue
            except httpx.HTTPStatusError as exc:
                if _is_quota_exhausted_response(exc.response):
                    last_error = exc
                    continue
                raise
        raise RuntimeError(f"Todos os modelos falharam: {last_error}")

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
    if _is_opencode_go():
        return f"opencode-go/{settings.AI_MODEL}"
    if _is_openai_family():
        return f"openai/{settings.AI_MODEL}"
    if _provider() == "gemini":
        return f"gemini/{settings.AI_MODEL}"
    return settings.AI_MODEL
