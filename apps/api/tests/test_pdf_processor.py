from app.services.pdf_processor import detect_pdf_quality, extract_full_text


def test_detect_pdf_quality_accepts_text_rich_pdf():
    pages = [{"numero_pagina": 1, "texto": "x" * 1200}]
    is_good, total = detect_pdf_quality(pages)
    assert is_good is True
    assert total >= 1000


def test_detect_pdf_quality_rejects_scanned_like_pdf():
    pages = [{"numero_pagina": 1, "texto": "curto"}]
    is_good, total = detect_pdf_quality(pages)
    assert is_good is False
    assert total < 1000


def test_extract_full_text_joins_pages():
    pages = [
        {"numero_pagina": 1, "texto": "Linha A"},
        {"numero_pagina": 2, "texto": "Linha B"},
    ]
    full = extract_full_text(pages)
    assert "Linha A" in full
    assert "Linha B" in full
