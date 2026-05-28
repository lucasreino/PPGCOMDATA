# h-index de revistas

Snapshot com **h-index da revista** (métrica do periódico no Google Scholar via lista COMPÓS, ou CSV/OpenAlex legado). Não confundir com índice h do autor no Google Acadêmico.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `revistas-hindex-comunicacao.json` | Catálogo usado pelo app (ISSN/título → `h_index`) |
| `compos-revistas-area.json` | Lista COMPÓS com H e mediana h5 para 2021 e 2022 |
| `revistas-compos-hindex.csv` | Cruzamento das revistas do PPG com a lista COMPÓS |
| `manual_overrides.json` | Ajustes manuais por ISSN ou nome do veículo |

## Atualizar a partir da página COMPÓS

Salve a página [Revistas da Área](https://compos.org.br/publicacoes/revistas-da-area/) como HTML e execute na raiz do repositório:

```bash
python scripts/parse_compos_hindex.py
```

O script lê o bloco `rawJournalsData` do HTML (fonte correta; a tabela estática no arquivo salvo pode estar desatualizada), gera os JSON/CSV acima e atualiza `revistas-hindex-comunicacao.json`. Por padrão usa o **Índice H de 2022** quando disponível.

## Aplicar no banco

```bash
alembic upgrade head
python -m app.apply_journal_hindex
```

## Atualizar a partir de outro CSV

```bash
python -m app.apply_journal_hindex --import-csv "caminho/revistas.csv" --write-json
python -m app.apply_journal_hindex --apply
```

Só revistas presentes no catálogo recebem `journal_h_index` nas produções (`artigo`, `anais`).
