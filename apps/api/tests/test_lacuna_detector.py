from app.schemas.ai import AIOrientacaoSchema
from app.models.enums import StatusOrientacao
from app.services.lacuna_detector import detect_orientacao_lacunas


def test_orientacao_em_andamento_sem_previsao():
    items = [
        AIOrientacaoSchema(
            tipo="mestrado",
            status=StatusOrientacao.EM_ANDAMENTO,
            ano_inicio=2022,
            trecho_original="orientação em andamento",
        )
    ]
    lacunas = detect_orientacao_lacunas(items)
    tipos = {l.tipo_lacuna for l in lacunas}
    assert "orientacao_sem_previsao" in tipos
