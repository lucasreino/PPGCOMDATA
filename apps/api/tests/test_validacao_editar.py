import json
import uuid

from app.models.data import Projeto
from app.models.enums import StatusValidacao, TipoProjeto
from app.routes.validacao import _snapshot_entity


def test_snapshot_entity_serializes_uuid_fields():
    proj = Projeto(
        id=uuid.uuid4(),
        professor_id=uuid.uuid4(),
        curriculo_upload_id=uuid.uuid4(),
        titulo="Projeto teste",
        tipo=TipoProjeto.PESQUISA,
        status_validacao=StatusValidacao.PENDENTE,
    )

    payload = json.loads(_snapshot_entity(proj))

    assert isinstance(payload["id"], str)
    assert isinstance(payload["professor_id"], str)
    assert isinstance(payload["curriculo_upload_id"], str)
    assert payload["status_validacao"] == "pendente"
