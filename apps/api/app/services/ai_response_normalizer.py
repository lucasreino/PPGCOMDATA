"""Normalização de campos retornados pela IA antes da validação Pydantic."""

from __future__ import annotations

import logging
import re
import unicodedata
from enum import Enum
from typing import Any, Dict, Optional

from app.models.enums import (
    ConfiancaIA,
    EscopoEvento,
    GravidadeLacuna,
    NivelBanca,
    NivelFormacao,
    PapelBanca,
    PapelGrupoPesquisa,
    PapelOrientacao,
    StatusOrientacao,
    TipoBanca,
    TipoFinanciamento,
    TipoOrientacao,
    TipoPremio,
    TipoProducaoTecnica,
    TipoProjeto,
)

logger = logging.getLogger("ppgcomdata.ai_normalizer")

_YEAR_ONGOING = frozenset(
    {
        "atual",
        "presente",
        "em andamento",
        "andamento",
        "vigente",
        "até o momento",
        "ate o momento",
        "current",
        "ongoing",
        "-",
        "—",
        "n/a",
        "na",
    }
)

_TIPO_TO_NIVEL = {
    "mestrado": "mestrado",
    "doutorado": "doutorado",
    "graduação": "graduacao",
    "graduacao": "graduacao",
    "especialização": "especializacao",
    "especializacao": "especializacao",
    "pós-doutorado": "pos_doutorado",
    "pos-doutorado": "pos_doutorado",
    "ensino médio": "outra",
    "ensino medio": "outra",
    "ensino fundamental": "outra",
}


def _ascii_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.strip().lower())
    text = text.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def coerce_optional_year(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 1900 <= value <= 2100 else None
    if isinstance(value, float):
        y = int(value)
        return y if 1900 <= y <= 2100 else None
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered in _YEAR_ONGOING or "atual" in lowered or "presente" in lowered:
        return None
    match = re.search(r"\b(19|20)\d{2}\b", text)
    if match:
        year = int(match.group())
        return year if 1900 <= year <= 2100 else None
    digits = re.sub(r"\D", "", text)
    if len(digits) == 4:
        year = int(digits)
        return year if 1900 <= year <= 2100 else None
    return None


def coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in ("1", "true", "sim", "yes", "s"):
        return True
    if text in ("0", "false", "nao", "não", "no", "n"):
        return False
    return default


def coerce_autores(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        parts = [str(x).strip() for x in value if x is not None and str(x).strip()]
        return "; ".join(parts) if parts else None
    if isinstance(value, dict):
        parts = [str(v).strip() for v in value.values() if v]
        return "; ".join(parts) if parts else None
    text = str(value).strip()
    return text or None


def coerce_string_list(value: Any) -> Optional[list[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(x).strip() for x in value if x is not None and str(x).strip()]
    text = str(value).strip()
    if not text:
        return None
    if ";" in text:
        return [p.strip() for p in text.split(";") if p.strip()]
    if "," in text:
        return [p.strip() for p in text.split(",") if p.strip()]
    return [text]


def section_default_producao_tipo(section_name: Optional[str]) -> Optional[str]:
    if not section_name:
        return None
    normalized = section_name.strip().lower()
    if "artigo" in normalized:
        return "artigo"
    if "capítulo" in normalized or "capitulo" in normalized:
        return "capitulo"
    if "livro" in normalized:
        return "livro"
    if "anais" in normalized:
        return "anais"
    if "resumo" in normalized:
        return "resumo"
    return None


def normalize_producao_tipo(
    value: Any,
    *,
    section_name: Optional[str] = None,
) -> str:
    default = section_default_producao_tipo(section_name)
    if value is None or (isinstance(value, str) and not value.strip()):
        return default or "outra"
    text = str(value).strip().lower()
    key = _ascii_key(text)
    direct = {
        "artigo": "artigo",
        "artigos": "artigo",
        "article": "artigo",
        "livro": "livro",
        "livros": "livro",
        "book": "livro",
        "capitulo": "capitulo",
        "capitulos": "capitulo",
        "capitulo_de_livro": "capitulo",
        "anais": "anais",
        "trabalho_em_evento": "anais",
        "trabalhos_em_eventos": "anais",
        "resumo": "resumo",
        "resumo_expandido": "resumo",
        "tecnica": "tecnica",
        "producao_tecnica": "tecnica",
        "outra": "outra",
        "outro": "outra",
    }
    if key in direct:
        return direct[key]
    if "artigo" in text:
        return "artigo"
    if "capit" in text or "capít" in text:
        return "capitulo"
    if "livro" in text:
        return "livro"
    if "anais" in text or "evento" in text:
        return "anais"
    if "resumo" in text:
        return "resumo"
    return default or "outra"


def coerce_enum_value(
    value: Any,
    enum_cls: type[Enum],
    *,
    default: Enum | None = None,
    aliases: Optional[Dict[str, str]] = None,
) -> Any:
    if value is None:
        return (default or next(iter(enum_cls))).value
    if isinstance(value, enum_cls):
        return value.value
    key = _ascii_key(str(value))
    if aliases and key in aliases:
        key = aliases[key]
    for member in enum_cls:
        if member.value == key or _ascii_key(member.name) == key:
            return member.value
    for member in enum_cls:
        mv = member.value
        if key in mv or mv in key:
            return member.value
    return (default or next(iter(enum_cls))).value


def normalize_item_fields(
    item: Dict[str, Any],
    *,
    section_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Limpa um item de lista da resposta da IA para passar no schema Pydantic."""
    for alt_key in ("title", "Titulo", "titulo_obra", "titulo_trabalho", "nome_obra"):
        if alt_key in item and not item.get("titulo"):
            item["titulo"] = item.pop(alt_key) if alt_key != "titulo" else item[alt_key]
    if "nome" in item and "nome_grupo" not in item and not item.get("titulo"):
        item["titulo"] = item.pop("nome")
    elif "nome" in item and "nome_grupo" not in item:
        item["nome_grupo"] = item.pop("nome")
    if "confianca" in item and "confianca_ia" not in item:
        item["confianca_ia"] = item.pop("confianca")

    for year_field in (
        "ano",
        "ano_inicio",
        "ano_fim",
        "ano_conclusao",
    ):
        if year_field in item:
            item[year_field] = coerce_optional_year(item[year_field])

    if "autores" in item:
        item["autores"] = coerce_autores(item["autores"])

    if "instituicoes" in item:
        inst = item["instituicoes"]
        if isinstance(inst, str):
            item["instituicoes"] = coerce_string_list(inst)
        elif isinstance(inst, dict):
            item["instituicoes"] = list(inst.values())

    if "palavras_chave" in item:
        item["palavras_chave"] = coerce_string_list(item.get("palavras_chave"))

    for bool_field, default in (
        ("periodo_sanduiche", False),
        ("financiamento_mencionado", False),
        ("eh_organizacao", False),
        ("eh_primeiro_autor", None),
    ):
        if bool_field in item:
            if bool_field == "eh_primeiro_autor" and item[bool_field] is None:
                continue
            item[bool_field] = coerce_bool(item[bool_field], default=bool(default))

    is_producao_biblio = (
        "titulo" in item
        and not any(
            k in item
            for k in (
                "nome_evento",
                "nome_orientando",
                "nome_candidato",
                "nome_grupo",
                "situacao",
                "vinculo_com",
                "instituicao_concedente",
            )
        )
        and any(
            k in item
            for k in ("veiculo", "doi", "issn", "qualis", "autores", "paginas", "volume")
        )
    ) or (
        "titulo" in item
        and section_default_producao_tipo(section_name) is not None
        and "nome_evento" not in item
    )
    if is_producao_biblio and "tipo" in item:
        item["tipo"] = normalize_producao_tipo(item["tipo"], section_name=section_name)
    elif is_producao_biblio:
        item["tipo"] = normalize_producao_tipo(None, section_name=section_name)

    if "confianca_ia" in item:
        item["confianca_ia"] = coerce_enum_value(
            item["confianca_ia"], ConfiancaIA, default=ConfiancaIA.MEDIA
        )
    if "confianca" in item:
        item["confianca"] = coerce_enum_value(
            item["confianca"], ConfiancaIA, default=ConfiancaIA.MEDIA
        )

    if (
        "tipo" in item
        and "titulo" in item
        and "situacao" in item
        and not is_producao_biblio
    ):
        item["tipo"] = coerce_enum_value(
            item["tipo"],
            TipoProjeto,
            default=TipoProjeto.OUTRO,
            aliases={
                "pesquisa_cientifica": "pesquisa",
                "projeto_de_pesquisa": "pesquisa",
                "projeto_pesquisa": "pesquisa",
                "extensao_universitaria": "extensao",
                "desenvolvimento_tecnologico": "desenvolvimento",
            },
        )

    if "tipo" in item and "vinculo_com" in item:
        item["tipo"] = coerce_enum_value(
            item["tipo"],
            TipoFinanciamento,
            default=TipoFinanciamento.OUTRO,
        )

    if "gravidade" in item:
        item["gravidade"] = coerce_enum_value(
            item["gravidade"], GravidadeLacuna, default=GravidadeLacuna.MEDIA
        )

    if "escopo" in item and item["escopo"] is not None:
        item["escopo"] = coerce_enum_value(
            item["escopo"], EscopoEvento, default=EscopoEvento.OUTRO
        )

    if item.get("periodo_sanduiche") is None:
        item["periodo_sanduiche"] = False

    if "tipo" in item and "nivel" not in item and "curso" in item and "instituicao" in item:
        tipo = str(item.pop("tipo")).strip().lower()
        item["nivel"] = _TIPO_TO_NIVEL.get(tipo, "outra")

    if "nivel" in item and not isinstance(item["nivel"], NivelFormacao):
        item["nivel"] = coerce_enum_value(
            item["nivel"], NivelFormacao, default=NivelFormacao.OUTRA
        )

    if "tipo" in item and "status" in item and "nome_orientando" in item:
        item["tipo"] = coerce_enum_value(
            item["tipo"],
            TipoOrientacao,
            default=TipoOrientacao.OUTRA,
            aliases={
                "tcc": "tcc",
                "trabalho_de_conclusao_de_curso": "tcc",
                "monografia": "tcc",
                "iniciacao_cientifica": "ic",
                "iniciacao_cientifica_ic": "ic",
                "pos_graduacao": "pos_doutorado",
                "pos_doutorado": "pos_doutorado",
                "graduacao": "outra",
                "especializacao": "outra",
                "ensino_medio": "outra",
            },
        )
        item["status"] = coerce_enum_value(
            item["status"], StatusOrientacao, default=StatusOrientacao.CONCLUIDA
        )
        item["papel"] = coerce_enum_value(
            item.get("papel"), PapelOrientacao, default=PapelOrientacao.ORIENTADOR
        )

    if "tipo" in item and "nivel" in item and "nome_candidato" in item:
        item["tipo"] = coerce_enum_value(item["tipo"], TipoBanca, default=TipoBanca.OUTRA)
        item["nivel"] = coerce_enum_value(item["nivel"], NivelBanca, default=NivelBanca.OUTRO)
        item["papel"] = coerce_enum_value(
            item.get("papel"), PapelBanca, default=PapelBanca.MEMBRO
        )

    if (
        not is_producao_biblio
        and "tipo" in item
        and "titulo" in item
        and ("url" in item or "descricao" in item)
        and "nome_evento" not in item
        and "nome_orientando" not in item
    ):
        item["tipo"] = coerce_enum_value(
            item["tipo"],
            TipoProducaoTecnica,
            default=TipoProducaoTecnica.OUTRA,
            aliases={
                "parecer": "outra",
                "parecerista": "outra",
                "relatorio_tecnico": "outra",
                "relatorio": "outra",
                "correspondente": "outra",
                "revisao": "outra",
            },
        )

    if item.get("papel") in ("pesquisador_voluntario", "voluntario", "coordenador"):
        item["papel"] = "membro"
    if "papel" in item and "nome_grupo" in item:
        item["papel"] = coerce_enum_value(
            item["papel"], PapelGrupoPesquisa, default=PapelGrupoPesquisa.MEMBRO
        )

    if item.get("nivel") == "outra":
        item["nivel"] = "outro"

    if not item.get("trecho_original"):
        item["trecho_original"] = (
            item.get("titulo")
            or item.get("nome_grupo")
            or item.get("curso")
            or item.get("instituicao")
            or item.get("nome")
            or "Extraído do Lattes"
        )

    if not (item.get("titulo") or "").strip() and item.get("trecho_original"):
        snippet = str(item["trecho_original"]).strip().split("\n")[0]
        item["titulo"] = snippet[:300] if snippet else "Produção sem título"

    if "tipo" in item and "nome" in item and "instituicao_concedente" in item:
        item["tipo"] = coerce_enum_value(item["tipo"], TipoPremio, default=TipoPremio.PREMIO)

    return item
