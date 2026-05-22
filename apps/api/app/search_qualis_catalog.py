"""Busca ISSNs/títulos no catálogo Qualis."""

from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qualis_catalog import (
    default_qualis_xlsx_path,
    load_qualis_catalog,
    normalize_issn,
)

SEARCH_ISSNS = [
    "18518931",
    "23785394",
    "21794529",
    "2237339X",
    "14156938",
    "0101305X",
    "24475777",
    "1521804X",
    "14479516",
    "19849109",
    "07184018",
    "15179257",
    "29543843",
    "23183640",
    "23578289",
    "19845227",
    "16469372",
    "15189775",
    "19824416",
    "23176750",
    "2718658X",
    "21736588",
    "07192096",
]

SEARCH_WORDS = [
    "PAPEIS",
    "FARO",
    "REBELA",
    "COMUM",
    "RHETORIKE",
    "Rhetorike",
    "LEITURAS",
    "TECCOM",
    "RECIAL",
    "TRIADE",
    "LIS LETRA",
    "ESTUDOS DA COMUNICACAO",
    "INTERCOM",
    "JORNALISMO",
]


def main() -> None:
    entries, by_issn, by_titulo = load_qualis_catalog(default_qualis_xlsx_path())

    print("=== ISSN no catálogo ===")
    for s in SEARCH_ISSNS:
        k = normalize_issn(s)
        print(f"{s} -> {k}: {by_issn.get(k, 'NAO')}")

    print("\n=== Título (palavras-chave) ===")
    for word in SEARCH_WORDS:
        w = word.upper()
        hits = [
            e
            for e in entries
            if w in e.titulo_key or w in e.titulo.upper()
        ]
        print(f"\n'{word}': {len(hits)}")
        for e in hits[:4]:
            print(f"  [{e.estrato}] {e.titulo} | {e.issn}")


if __name__ == "__main__":
    main()
