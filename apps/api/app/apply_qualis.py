"""
Aplica estrato Qualis às produções (artigos) a partir da planilha Capes.

Execute:
  python -m app.apply_qualis --dry-run
  python -m app.apply_qualis
  python -m app.apply_qualis --xlsx /caminho/planilha.xlsx
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.data import Producao
from app.services.qualis_catalog import (
    default_qualis_xlsx_path,
    load_manual_overrides,
    load_qualis_catalog,
    lookup_qualis,
    normalize_estrato,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aplica Qualis às produções tipo artigo")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem gravar no banco")
    parser.add_argument("--xlsx", type=str, default="", help="Caminho da planilha Qualis")
    parser.add_argument(
        "--tipos",
        type=str,
        default="artigo,anais",
        help="Tipos de produção separados por vírgula (padrão: artigo,anais)",
    )
    args = parser.parse_args()

    xlsx_path = default_qualis_xlsx_path()
    if args.xlsx:
        from pathlib import Path

        xlsx_path = Path(args.xlsx)

    if not xlsx_path.is_file():
        print(f"Planilha não encontrada: {xlsx_path}")
        sys.exit(1)

    entries, by_issn, by_titulo = load_qualis_catalog(xlsx_path)
    manual_issn, manual_veiculo = load_manual_overrides()
    print(f"Catálogo: {xlsx_path.name}")
    print(f"  Revistas no catálogo: {len(entries)}")
    print(f"  Índice ISSN: {len(by_issn)} | Índice título: {len(by_titulo)}")
    if manual_issn or manual_veiculo:
        print(
            f"  Overrides manuais: {len(manual_issn)} ISSN, "
            f"{len(manual_veiculo)} veículo"
        )

    tipos = {t.strip().lower() for t in args.tipos.split(",") if t.strip()}
    stats = Counter()
    samples: list[str] = []
    unmatched_samples: list[str] = []

    with Session(engine) as session:
        producoes = [
            p
            for p in session.exec(select(Producao)).all()
            if (p.tipo or "").lower() in tipos
        ]
        print(f"\nProduções a avaliar ({', '.join(sorted(tipos))}): {len(producoes)}")

        for prod in producoes:
            estrato, metodo = lookup_qualis(
                prod.issn,
                prod.veiculo,
                by_issn,
                by_titulo,
                manual_issn,
                manual_veiculo,
            )
            if not estrato:
                stats["sem_match"] += 1
                if len(unmatched_samples) < 15:
                    unmatched_samples.append(
                        f"  - {prod.veiculo or '(sem veículo)'} | ISSN={prod.issn or '—'} | {prod.titulo[:60]}"
                    )
                continue

            stats[metodo] += 1
            atual = normalize_estrato(prod.qualis)
            if atual == estrato:
                stats["ja_ok"] += 1
                continue

            stats["atualizado"] += 1
            if len(samples) < 20:
                samples.append(
                    f"  [{metodo}] {estrato} ← {prod.veiculo or prod.titulo[:40]} "
                    f"(antes: {atual or '—'})"
                )

            if not args.dry_run:
                prod.qualis = estrato
                session.add(prod)

        if not args.dry_run:
            session.commit()

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
        print("\nQualis aplicado e salvo no banco.")


if __name__ == "__main__":
    main()
