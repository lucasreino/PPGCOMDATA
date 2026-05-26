import pytest

from app.services.lattes_curriculo_import import validate_lattes_file


def test_validate_html_file():
    validate_lattes_file("curriculo.html", "html")
    validate_lattes_file("curriculo.htm", "html")


def test_validate_xml_file():
    validate_lattes_file("5487269670962081.xml", "xml")


def test_reject_pdf():
    with pytest.raises(ValueError, match="HTML"):
        validate_lattes_file("lattes.pdf", "html")
    with pytest.raises(ValueError, match="XML"):
        validate_lattes_file("lattes.pdf", "xml")
