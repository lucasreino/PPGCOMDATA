from app.services.llm_client import _prepare_openai_schema


def test_prepare_openai_schema_adds_additional_properties():
    schema = {
        "type": "object",
        "properties": {
            "projetos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"titulo": {"type": "string"}},
                },
            }
        },
    }
    prepared = _prepare_openai_schema(schema)
    assert prepared["additionalProperties"] is False
    assert "projetos" in prepared["required"]
