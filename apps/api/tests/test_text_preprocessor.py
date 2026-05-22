from app.services.text_preprocessor import normalize_lattes_text


def test_normalize_removes_lattes_footer_noise():
    raw = "Linha útil\nCurrículo Lattes\nhttp://lattes.cnpq.br/123\nMais conteúdo"
    out = normalize_lattes_text(raw)
    assert "Linha útil" in out
    assert "Mais conteúdo" in out
    assert "lattes.cnpq.br" not in out


def test_normalize_fixes_hyphenation_line_break():
    raw = "comunica-\nção social"
    out = normalize_lattes_text(raw)
    assert "comunicação social" in out


def test_normalize_puts_section_header_on_new_line():
    raw = "Intro Dados gerais\nNome: Fulano"
    out = normalize_lattes_text(raw)
    assert "\nDados gerais" in out or out.startswith("Dados gerais")
