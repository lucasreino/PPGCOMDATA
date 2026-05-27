"""
Extrai métricas e publicações de HTML exportado do Google Acadêmico.

Execute:
  python -m app.parse_scholar_profile --html "caminho/perfil.html"
  python -m app.parse_scholar_profile --html perfil.html --json --xml
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scholar_profile_parser import (
    default_scholar_profiles_dir,
    parse_scholar_profile_file,
    write_scholar_profile_json,
    write_scholar_profile_xml,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parseia HTML do Google Acadêmico e grava sidecar JSON/XML"
    )
    parser.add_argument(
        "--html",
        type=str,
        required=True,
        help="Caminho do HTML (ex.: export FireShot ou 'Salvar como' completo)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="",
        help="Diretório base (padrão: data/scholar_profiles)",
    )
    parser.add_argument("--json", action="store_true", help="Grava json/{user_id}.json")
    parser.add_argument("--xml", action="store_true", help="Grava xml/{user_id}.xml")
    parser.add_argument(
        "--copy-html",
        action="store_true",
        help="Copia o HTML para html/{user_id}.html no out-dir",
    )
    args = parser.parse_args()

    html_path = Path(args.html).expanduser().resolve()
    if not html_path.is_file():
        print(f"Arquivo não encontrado: {html_path}", file=sys.stderr)
        sys.exit(1)

    base = Path(args.out_dir).expanduser().resolve() if args.out_dir else default_scholar_profiles_dir()
    data = parse_scholar_profile_file(html_path)

    write_json = args.json or not args.xml
    write_xml = args.xml

    if args.copy_html:
        dest = base / "html" / f"{data.scholar_user_id}.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        print(f"HTML copiado: {dest}")

    if write_json:
        json_path = base / "json" / f"{data.scholar_user_id}.json"
        write_scholar_profile_json(data, json_path)
        print(f"JSON: {json_path}")

    if write_xml:
        xml_path = base / "xml" / f"{data.scholar_user_id}.xml"
        write_scholar_profile_xml(data, xml_path)
        print(f"XML:  {xml_path}")

    m = data.metrics
    print()
    print(f"{data.name} ({data.scholar_user_id})")
    if data.affiliation:
        print(f"  Afiliação: {data.affiliation}")
    print(
        f"  Citações: {m.citations_all} (desde {m.since_year or '?'}: {m.citations_since})"
    )
    print(f"  h-index: {m.h_index_all} / i10: {m.i10_index_all}")
    print(f"  Publicações no HTML: {len(data.publications)}")


if __name__ == "__main__":
    main()
