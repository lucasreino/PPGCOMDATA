# h-index de revistas (OpenAlex / CSV)

Snapshot com **h-index da revista** (não confundir com índice h do autor no Google Acadêmico).

## Aplicar no banco

```bash
alembic upgrade head
python -m app.apply_journal_hindex
```

## Atualizar a partir do CSV

```bash
python -m app.apply_journal_hindex --import-csv "caminho/revistas_openalex_hindex.csv" --write-json
python -m app.apply_journal_hindex --apply
```

Só revistas presentes no catálogo recebem `journal_h_index` nas produções (`artigo`, `anais`).
