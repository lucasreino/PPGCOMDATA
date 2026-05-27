# Google Scholar Metrics (h5) — snapshot local

Este diretório guarda um **snapshot versionado** dos indicadores **h5-index** e **h5-median** de periódicos conforme publicados no [Google Scholar Metrics](https://scholar.google.com/citations?view_op=top_venues) (por área, ex.: *Communication*).

Não há API oficial; o fluxo espelha o Qualis: arquivo no repositório + cruzamento por ISSN / título na importação e via CLI.

## Formato do arquivo principal

Arquivo padrão: `scholar-metrics-comunicacao.json` (nome configurável no código).

```json
{
  "metrics_year": 2024,
  "source_note": "Substitua por referência à lista/área e data de captura.",
  "journals": [
    {
      "titulo": "Nome do periódico como no Scholar",
      "issn": "12345678",
      "h5_index": 42,
      "h5_median": 55
    }
  ]
}
```

- **issn**: apenas dígitos (com ou sem hífen no JSON; a normalização remove não-dígitos).
- **h5_median**: opcional; pode ser omitido ou `null`.
- **metrics_year**: ano de referência do ranking (ex.: ano em que o Scholar publicou aquela edição).

## Atualização anual (manual)

1. Abra o Google Scholar Metrics na categoria desejada (ex.: Communication).
2. Transcreva ou exporte os periódicos relevantes para o JSON (mantendo `metrics_year` coerente).
3. Commit do arquivo atualizado.
4. Rode a aplicação no servidor:

```bash
docker compose exec -T api python -m app.apply_scholar_metrics --dry-run
docker compose exec -T api python -m app.apply_scholar_metrics
```

Outro arquivo:

```bash
docker compose exec -T api python -m app.apply_scholar_metrics --json /workspace/data/scholar_metrics/outro.json
```

## Overrides manuais

Edite `manual_overrides.json` quando o título no Lattes não bater com o catálogo:

```json
{
  "by_issn": {
    "23185694": { "h5_index": 12, "h5_median": 14, "metrics_year": 2024 }
  },
  "by_veiculo": {
    "COMUNICACAO E SOCIEDADE": { "h5_index": 10, "metrics_year": 2024 }
  }
}
```

Chaves de `by_veiculo` usam a mesma normalização que o Qualis (`normalize_title` em `qualis_catalog.py`).

## Aplicar nas publicações

Ordem de match: overrides (ISSN, veículo) → ISSN no catálogo → título exato → título parcial (mesma heurística do Qualis).

Tipos padrão cruzados: `artigo`, `anais`.
