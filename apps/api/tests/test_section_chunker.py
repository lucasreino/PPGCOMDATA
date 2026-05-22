from app.services.section_chunker import chunk_section_text


def test_small_section_not_chunked():
    text = "1. Item único\nTítulo do artigo"
    chunks = chunk_section_text("Artigos completos publicados em periódicos", text)
    assert chunks == [text]


def test_large_numbered_section_splits():
    items = [f"{i}. Artigo número {i} com título longo " + ("x" * 200) for i in range(1, 16)]
    text = "\n\n".join(items)
    chunks = chunk_section_text(
        "Artigos completos publicados em periódicos",
        text,
        max_chars=2500,
        max_items=4,
    )
    assert len(chunks) >= 3
    assert all(len(c) <= 2600 for c in chunks)


def test_non_chunkable_section_stays_single():
    text = "x" * 20000
    chunks = chunk_section_text("Dados gerais", text)
    assert len(chunks) == 1
