"""Remove duplicatas exatas (mantém o registro mais antigo)."""

import argparse
import os
import sys

from sqlmodel import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.enums import FonteDado
from app.services.record_dedupe import remove_exact_duplicates


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove duplicatas exatas no banco")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--all-fontes",
        action="store_true",
        help="Inclui pdf_lattes (padrão: só xml_lattes)",
    )
    args = parser.parse_args()

    fonte = None if args.all_fontes else FonteDado.XML_LATTES
    with Session(engine) as session:
        removed = remove_exact_duplicates(session, fonte=fonte, dry_run=args.dry_run)

    if not removed:
        print("Nenhuma duplicata exata encontrada.")
        return

    print("Removidos (dry-run)" if args.dry_run else "Removidos:")
    for label, n in removed.items():
        print(f"  {label}: {n}")
    print(f"Total: {sum(removed.values())}")


if __name__ == "__main__":
    main()
