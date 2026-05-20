from app.schemas.ai import AIProducaoSchema
from app.services.lacuna_detector import detect_producao_lacunas


def test_artigo_recente_sem_doi():
    items = [
        AIProducaoSchema(
            tipo="artigo",
            titulo="Artigo recente sem identificador",
            ano=2025,
            trecho_original="trecho",
        )
    ]
    lacunas = detect_producao_lacunas(items)
    assert any(l.tipo_lacuna == "artigo_sem_doi" for l in lacunas)
