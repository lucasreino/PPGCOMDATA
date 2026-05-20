from app.services.upload_assignment import (
    normalize_filename,
    resolve_email_from_filename,
)


def test_resolve_domingos_pdf():
    assert resolve_email_from_filename("domingos alves de almeida.pdf") == "domingos.almeida@ufma.br"


def test_resolve_gislene_pdf():
    assert resolve_email_from_filename("gisa carvalho.pdf") == "maria.gcf@ufma.br"


def test_resolve_messias_pdf():
    email = resolve_email_from_filename("Zé Messias.pdf")
    assert email == "jose.cmsf@ufma.br"
    assert "messias" in normalize_filename("Zé Messias.pdf")
