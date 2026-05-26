from __future__ import annotations

from pathlib import Path

from .html_parser import load_html
from .xml_builder import build_xml, tree_to_string


def convert_html_to_xml(html_path: str | Path, output_path: str | Path | None = None) -> str:
    """
    Converte um arquivo HTML salvo do Lattes em XML compatível.

    Campos omitidos de propósito: CPF, RG, data de nascimento, nomes dos pais,
    permissão de divulgação, metadados de export (hora, sistema-origem).
    """
    html_path = Path(html_path)
    cv = load_html(html_path)
    tree = build_xml(cv)
    xml_text = tree_to_string(tree)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(xml_text, encoding="iso-8859-1")

    return xml_text
