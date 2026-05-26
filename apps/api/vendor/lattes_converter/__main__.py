import argparse
import sys
from pathlib import Path

from .converter import convert_html_to_xml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Converte currículo Lattes (HTML salvo) para XML."
    )
    parser.add_argument("html", type=Path, help="Arquivo HTML do currículo")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Arquivo XML de saída (padrão: mesmo nome com .xml)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Converte todos os .html em assets/lattes em html/ para output/",
    )
    args = parser.parse_args(argv)

    if args.batch:
        import importlib.util
        from pathlib import Path as P

        script = P(__file__).resolve().parents[2] / "scripts" / "batch_convert.py"
        spec = importlib.util.spec_from_file_location("batch_convert", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.main()

    if not args.html.exists():
        print(f"Arquivo não encontrado: {args.html}", file=sys.stderr)
        return 1

    output = args.output
    if output is None:
        output = args.html.with_suffix(".xml")
        if output == args.html:
            output = args.html.parent / f"{args.html.stem}_lattes.xml"

    convert_html_to_xml(args.html, output)
    print(f"XML gerado: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
