"""Teste rápido da chave OpenAI (uso: python -m app.test_openai_key)."""
from app.config import settings
from app.services.llm_client import generate_text


def main() -> None:
    print("provider:", settings.AI_PROVIDER)
    print("model:", settings.AI_MODEL)
    if not settings.AI_API_KEY:
        print("ERRO: AI_API_KEY vazia")
        return
    try:
        out = generate_text("Você é um assistente.", "Responda apenas: ok")
        print("OK:", out[:100])
    except Exception as exc:
        print("FALHA:", exc)


if __name__ == "__main__":
    main()
