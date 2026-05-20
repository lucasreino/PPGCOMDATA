"""Diagnóstico OpenAI — imprime código e tipo de erro (sem vazar a chave)."""
import httpx
from app.config import settings


def main() -> None:
    url = f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.AI_MODEL,
        "messages": [{"role": "user", "content": "ok"}],
        "max_tokens": 3,
    }
    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json=payload, headers=headers)
    print("status:", r.status_code)
    print("body:", (r.text or "")[:500])


if __name__ == "__main__":
    main()
