# Perfis Google Acadêmico (autores)

Sidecars com **citações, h-index e lista de publicações** por docente, extraídos de HTML salvo manualmente (não depende de scraping em produção).

## Estrutura

```
data/scholar_profiles/
  html/   # export completo (FireShot, Ctrl+S, etc.)
  json/   # gerado pelo parser
  xml/    # opcional, mesmo conteúdo em XML
```

Nome sugerido do HTML: `{scholar_user_id}.html` (ex.: `Q61X3XUAAAAJ.html`).

## Como gerar JSON/XML

Na raiz do monorepo ou em `apps/api`:

```bash
python -m app.parse_scholar_profile --html "C:\caminho\perfil.html" --json --xml --copy-html
```

## Requisitos do HTML

- Página do perfil já **totalmente carregada** (todas as publicações visíveis ou o máximo que o Scholar mostrar sem rolar infinito).
- URL no comentário `saved from url` ou parâmetro `user=...` no HTML.
- Tabela `#gsc_rsb_st` com citações / h / i10 presente.

## Integrar citações por artigo no banco

1. Rode a migração: `alembic upgrade head`
2. Aplique (o sistema tenta **vincular pelo nome** do perfil Scholar ao `nome_completo` / `nome_citacao` do docente):

```bash
python -m app.apply_scholar_profiles --scholar-user Q61X3XUAAAAJ
```

O sistema cruza **título + ano** (com tolerância para pequenas diferenças de texto) e grava `scholar_citations` em cada `Producao` correspondente. No docente, grava totais (`scholar_citations_total`, `h-index`, etc.).

## Vínculo com docente

Ordem automática:

1. `linkage.json` (`professor_id` ou `id_lattes`) — opcional, para homônimos
2. `scholar_user_id` já salvo no docente (reimportações)
3. **Nome exato** (ignora acentos e maiúsculas)
4. **Nome muito parecido** — só se existir **um único** docente acima de 92% de similaridade

Se dois docentes tiverem nomes parecidos, use `linkage.json`. Para desligar o match por nome: `--no-name-match`.
