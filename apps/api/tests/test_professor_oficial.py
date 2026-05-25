"""Testes do cadastro oficial mesclado."""

import json
from pathlib import Path

import pytest

from app.services import professor_oficial as po


@pytest.fixture
def isolated_additions(tmp_path, monkeypatch):
    path = tmp_path / "adicionados.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(po, "ADDITIONS_FILE", path)
    monkeypatch.setattr(po, "_CADASTRO_DIR", tmp_path)
    return path


def test_register_and_merge_official(isolated_additions):
    class FakeSession:
        pass

    entry = po.register_official_professor(
        FakeSession(),
        nome_completo="Ana Teste Silva",
        email="ana.teste@ufma.br",
        link_lattes="http://lattes.cnpq.br/1111111111111111",
        id_lattes="1111111111111111",
        tipo_docente=po.TipoDocente.PERMANENTE,
        linha_pesquisa_id=None,
        grupo_pesquisa="Grupo Teste",
        tematicas="Comunicação digital",
    )
    assert entry["linha"] == "linha1"

    raw = json.loads(isolated_additions.read_text(encoding="utf-8"))
    assert len(raw) == 1
    assert raw[0]["email"] == "ana.teste@ufma.br"

    merged = po.get_official_professor_data()
    emails = [d.get("email", "").lower() for d in merged]
    assert "ana.teste@ufma.br" in emails
