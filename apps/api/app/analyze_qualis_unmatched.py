"""Lista produções sem Qualis e sugere matches próximos no catálogo."""

from __future__ import annotations

import os
import sys

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.data import Producao, Professor
from app.services.qualis_catalog import (
    default_qualis_xlsx_path,
    load_manual_overrides,
    load_qualis_catalog,
    lookup_qualis,
    normalize_issn,
    normalize_title,
)


def fuzzy_issn(key: str, by_issn: dict[str, str]) -> list[tuple[str, str]]:
    if not key:
        return []
    out = []
    for k, estrato in by_issn.items():
        if key in k or k in key:
            out.append((k, estrato))
    return out[:5]


def fuzzy_title(key: str, by_titulo: dict[str, str]) -> list[tuple[int, str, str]]:
    if not key or len(key) < 5:
        return []
    words = [w for w in key.split() if len(w) >= 4]
    out: list[tuple[int, str, str]] = []
    for cat_key, estrato in by_titulo.items():
        hits = sum(1 for w in words if w in cat_key)
        if hits >= 2 or (len(key) >= 10 and (key in cat_key or cat_key in key)):
            out.append((hits, cat_key, estrato))
    out.sort(reverse=True)
    return out[:3]


def main() -> None:
    entries, by_issn, by_titulo = load_qualis_catalog(default_qualis_xlsx_path())
    manual_issn, manual_veiculo = load_manual_overrides()
    titulo_orig = {e.titulo_key: e.titulo for e in entries}
    tipos = {"artigo", "anais"}

    with Session(engine) as session:
        prof_names = {
            p.id: p.nome_completo for p in session.exec(select(Professor)).all()
        }
        unmatched: list[Producao] = []
        for prod in session.exec(select(Producao)).all():
            if (prod.tipo or "").lower() not in tipos:
                continue
            estrato, _ = lookup_qualis(
                prod.issn,
                prod.veiculo,
                by_issn,
                by_titulo,
                manual_issn,
                manual_veiculo,
            )
            if not estrato:
                unmatched.append(prod)

    print(f"TOTAL SEM MATCH: {len(unmatched)}\n")
    print(f"{'Professor':28} | {'Veículo':42} | ISSN")
    print("-" * 90)
    for prod in unmatched:
        nome = (prof_names.get(prod.professor_id) or "?")[:28]
        veic = (prod.veiculo or "(vazio)")[:42]
        print(f"{nome:28} | {veic:42} | {prod.issn or '—'}")
    print("\n--- Detalhe por produção ---\n")
    for prod in unmatched:
        ik = normalize_issn(prod.issn)
        vk = normalize_title(prod.veiculo)
        print("=" * 70)
        print(f"id={prod.id} professor_id={prod.professor_id}")
        print(f"veiculo: {prod.veiculo}")
        print(f"issn: {prod.issn} -> {ik}")
        print(f"titulo: {(prod.titulo or '')[:60]}")

        if ik and ik in by_issn:
            print(f"  ISSN catálogo: {by_issn[ik]}")
        else:
            fi = fuzzy_issn(ik, by_issn)
            print(f"  ISSN catálogo: não" + (f" | próximo: {fi}" if fi else ""))

        if vk and vk in by_titulo:
            print(f"  Título catálogo: {by_titulo[vk]}")
        else:
            ft = fuzzy_title(vk, by_titulo)
            if ft:
                print("  Título próximo:")
                for hits, ck, est in ft:
                    orig = titulo_orig.get(ck, ck[:55])
                    print(f"    [{est}] ({hits} palavras) {orig}")
            else:
                print("  Título catálogo: não")


if __name__ == "__main__":
    main()
