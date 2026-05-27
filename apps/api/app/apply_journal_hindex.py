"""
Aplica h-index de revistas às produções a partir do JSON local (somente entradas do catálogo).

Execute:
  python -m app.apply_journal_hindex --dry-run
  python -m app.apply_journal_hindex
  python -m app.apply_journal_hindex --json /caminho/snapshot.json
  python -m app.apply_journal_hindex --import-csv /caminho/revistas.csv --write-json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.data import Producao
from app.services.journal_hindex_catalog import (
    apply_journal_hindex_to_producoes,
    default_journal_hindex_json_path,
    load_journal_hindex_catalog,
    load_journal_hindex_from_csv,
    load_journal_hindex_manual_overrides,
    lookup_journal_hindex,
)


def _hits_equal(prod: Producao, hit) -> bool:
    if prod.journal_h_index is None:
        return False
    return abs(prod.journal_h_index - hit.h_index) < 1e-9


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aplica h-index de revistas (snapshot CSV/OpenAlex) às produções"
    )
    parser.add_argument("--dry-run", action="store_true", help="Simula sem gravar no banco")
    parser.add_argument(
        "--json",
        type=str,
        default="",
        dest="json_path",
        help="Caminho do JSON (padrão: data/journal_hindex/revistas-hindex-comunicacao.json)",
    )
    parser.add_argument(
        "--import-csv",
        type=str,
        default="",
        help="Importa CSV e opcionalmente grava JSON (--write-json)",
    )
    parser.add_argument(
        "--write-json",
        action="store_true",
        help="Grava snapshot JSON a partir de --import-csv no caminho padrão",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Após --import-csv --write-json, também aplica ao banco (senão só gera JSON)",
    )
    parser.add_argument(
        "--tipos",
        type=str,
        default="artigo,anais",
        help="Tipos de produção separados por vírgula (padrão: artigo,anais)",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path) if args.json_path else default_journal_hindex_json_path()

    if args.import_csv:
        csv_path = Path(args.import_csv)
        if not csv_path.is_file():
            print(f"Arquivo CSV não encontrado: {csv_path}")
            sys.exit(1)
        data = load_journal_hindex_from_csv(csv_path)
        print(f"CSV importado: {len(data['journals'])} revistas com h-index")
        if args.write_json:
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Snapshot gravado em: {json_path}")
            if not args.apply:
                return
        elif not args.dry_run and not args.json_path:
            print("Use --write-json para persistir o snapshot ou --json para apontar destino.")
            sys.exit(1)

    if not json_path.is_file():
        print(f"Arquivo JSON não encontrado: {json_path}")
        sys.exit(1)

    by_issn, by_titulo = load_journal_hindex_catalog(json_path)
    manual_issn, manual_veiculo = load_journal_hindex_manual_overrides()
    print(f"Catálogo: {json_path.name}")
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
                hit, metodo = lookup_journal_hindex(
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
                        f"  [{metodo}] h={hit.h_index} ← {prod.veiculo or prod.titulo[:40]}"
                    )
        else:
            result = apply_journal_hindex_to_producoes(
                session, tipos=tipos, json_path=json_path
            )
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
        print("\nH-index de revistas aplicado e salvo no banco.")


if __name__ == "__main__":
    main()
