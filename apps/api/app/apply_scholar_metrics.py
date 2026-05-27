"""
Aplica métricas Google Scholar (h5-index / h5-median) às produções a partir do JSON local.

Execute:
  python -m app.apply_scholar_metrics --dry-run
  python -m app.apply_scholar_metrics
  python -m app.apply_scholar_metrics --json /caminho/snapshot.json
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.data import Producao
from app.services.scholar_metrics_catalog import (
    apply_scholar_metrics_to_producoes,
    default_scholar_metrics_json_path,
    load_scholar_manual_overrides,
    load_scholar_metrics_catalog,
    lookup_scholar_metrics,
)


def _hits_equal(prod: Producao, hit) -> bool:
    return (
        prod.scholar_h5_index == hit.h5_index
        and prod.scholar_h5_median == hit.h5_median
        and prod.scholar_metrics_year == hit.metrics_year
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aplica snapshot Google Scholar Metrics (h5) às produções"
    )
    parser.add_argument("--dry-run", action="store_true", help="Simula sem gravar no banco")
    parser.add_argument(
        "--json",
        type=str,
        default="",
        dest="json_path",
        help="Caminho do JSON de métricas (padrão: data/scholar_metrics/scholar-metrics-comunicacao.json)",
    )
    parser.add_argument(
        "--tipos",
        type=str,
        default="artigo,anais",
        help="Tipos de produção separados por vírgula (padrão: artigo,anais)",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path) if args.json_path else default_scholar_metrics_json_path()
    if not json_path.is_file():
        print(f"Arquivo JSON não encontrado: {json_path}")
        sys.exit(1)

    by_issn, by_titulo, file_year = load_scholar_metrics_catalog(json_path)
    manual_issn, manual_veiculo = load_scholar_manual_overrides(
        fallback_metrics_year=file_year,
    )
    print(f"Catálogo: {json_path.name}")
    print(f"  Ano de referência (raiz): {file_year or '—'}")
    print(f"  Índice ISSN: {len(by_issn)} | Índice título: {len(by_titulo)}")
    if manual_issn or manual_veiculo:
        print(
            f"  Overrides manuais: {len(manual_issn)} ISSN, {len(manual_veiculo)} veículo"
        )

    tipos = frozenset(t.strip().lower() for t in args.tipos.split(",") if t.strip())

    with Session(engine) as session:
        producoes = [
            p
            for p in session.exec(select(Producao)).all()
            if (p.tipo or "").lower() in tipos
        ]
        print(f"\nProduções a avaliar ({', '.join(sorted(tipos))}): {len(producoes)}")

        if args.dry_run:
            stats: Counter = Counter()
            samples: list[str] = []
            unmatched_samples: list[str] = []
            for prod in producoes:
                hit, metodo = lookup_scholar_metrics(
                    prod.issn,
                    prod.veiculo,
                    by_issn,
                    by_titulo,
                    manual_issn,
                    manual_veiculo,
                )
                if not hit:
                    stats["sem_match"] += 1
                    if len(unmatched_samples) < 15:
                        unmatched_samples.append(
                            f"  - {prod.veiculo or '(sem veículo)'} | ISSN={prod.issn or '—'} | {prod.titulo[:60]}"
                        )
                    continue
                stats[metodo] += 1
                if _hits_equal(prod, hit):
                    stats["ja_ok"] += 1
                    continue
                stats["atualizado"] += 1
                if len(samples) < 20:
                    samples.append(
                        f"  [{metodo}] h5={hit.h5_index} (mediana {hit.h5_median}) "
                        f"{hit.metrics_year} ← {prod.veiculo or prod.titulo[:40]}"
                    )
        else:
            result = apply_scholar_metrics_to_producoes(session, tipos=tipos, json_path=json_path)
            stats = Counter(result)
            samples = []
            unmatched_samples = []

    print("\n--- Resultado ---")
    print(f"  Atualizados: {stats['atualizado']}")
    print(f"  Já corretos: {stats['ja_ok']}")
    print(f"  Sem match no catálogo: {stats['sem_match']}")
    for k in ("issn", "titulo_exato", "titulo_parcial", "manual_issn", "manual_veiculo"):
        if stats[k]:
            print(f"  Via {k}: {stats[k]}")

    if samples:
        print("\nExemplos de atualização:")
        print("\n".join(samples))

    if unmatched_samples:
        print("\nExemplos sem match (revisar manualmente):")
        print("\n".join(unmatched_samples))

    if args.dry_run:
        print("\n(dry-run — nenhuma alteração gravada)")
    else:
        print("\nMétricas Scholar aplicadas e salvas no banco.")


if __name__ == "__main__":
    main()
