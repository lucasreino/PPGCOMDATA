"""
Aplica perfis Google Acadêmico (JSON em data/scholar_profiles/json) às produções.

Execute:
  python -m app.parse_scholar_profile --html perfil.html --json --copy-html
  python -m app.apply_scholar_profiles --dry-run
  python -m app.apply_scholar_profiles --scholar-user Q61X3XUAAAAJ
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from sqlmodel import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.services.scholar_profile_apply import (
    apply_scholar_profiles_from_dir,
    default_linkage_path,
    default_scholar_profiles_dir,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cruza JSON de perfil Scholar com produções Lattes do docente"
    )
    parser.add_argument("--dry-run", action="store_true", help="Não grava no banco")
    parser.add_argument(
        "--scholar-user",
        type=str,
        default="",
        help="Processa só este scholar_user_id (nome do arquivo em json/)",
    )
    parser.add_argument(
        "--profiles-dir",
        type=str,
        default="",
        help="Diretório data/scholar_profiles (padrão: auto)",
    )
    parser.add_argument(
        "--linkage",
        type=str,
        default="",
        help="Caminho para linkage.json (professor_id ou id_lattes por user)",
    )
    parser.add_argument(
        "--clear-unmatched",
        action="store_true",
        help="Remove scholar_citations de produções que não casaram com o perfil",
    )
    parser.add_argument(
        "--no-name-match",
        action="store_true",
        help="Não tenta vincular pelo nome do perfil Scholar (só linkage / scholar_user_id)",
    )
    args = parser.parse_args()

    base = (
        Path(args.profiles_dir).expanduser().resolve()
        if args.profiles_dir
        else default_scholar_profiles_dir()
    )
    linkage = Path(args.linkage).expanduser().resolve() if args.linkage else default_linkage_path()

    with Session(engine) as session:
        if args.dry_run:
            print("Dry-run: use sem --dry-run para gravar.")
            print(f"Perfis em: {base / 'json'}")
            print(f"Ligação: {linkage} ({'existe' if linkage.is_file() else 'ausente'})")
            return

        summary = apply_scholar_profiles_from_dir(
            session,
            profiles_dir=base,
            linkage_path=linkage if linkage.is_file() else None,
            scholar_user_id=args.scholar_user or None,
            clear_unmatched=args.clear_unmatched,
            allow_name_match=not args.no_name_match,
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
