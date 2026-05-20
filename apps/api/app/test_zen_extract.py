"""Teste extração estruturada via OpenCode Zen."""
from app.schemas.ai import OrientacaoExtractionSchema
from app.services.llm_client import get_structured_output


def main() -> None:
    schema = OrientacaoExtractionSchema.model_json_schema()
    result = get_structured_output(
        "Você extrai dados de Lattes em JSON.",
        "Seção: Orientações\nTexto: Orientou João Silva em mestrado, 2018-2020, concluído.",
        schema,
    )
    print("keys:", list(result.keys()))
    print("orientacoes:", len(result.get("orientacoes") or []))


if __name__ == "__main__":
    main()
