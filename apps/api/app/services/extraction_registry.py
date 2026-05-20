"""Maps Lattes PDF section names to extraction profile (schema + prompt focus)."""

from typing import Literal, Optional

ExtractionProfile = Literal[
    "padrao",
    "formacao",
    "orientacoes",
    "bancas",
    "perfil",
    "eventos_participacao",
    "eventos_organizacao",
    "producao_tecnica",
    "premios",
    "grupos_pesquisa",
]

_SECTION_PROFILE_RULES: list[tuple[str, ExtractionProfile]] = [
    ("organização de eventos", "eventos_organizacao"),
    ("organizacao de eventos", "eventos_organizacao"),
    ("participação em eventos", "eventos_participacao"),
    ("participacao em eventos", "eventos_participacao"),
    ("orientações e supervisões", "orientacoes"),
    ("orientacoes e supervisoes", "orientacoes"),
    ("bancas", "bancas"),
    ("formação acadêmica", "formacao"),
    ("formacao academica", "formacao"),
    ("produção técnica", "producao_tecnica"),
    ("producao tecnica", "producao_tecnica"),
    ("prêmios e títulos", "premios"),
    ("premios e titulos", "premios"),
    ("atuação profissional", "grupos_pesquisa"),
    ("atuacao profissional", "grupos_pesquisa"),
    ("dados gerais", "perfil"),
]

_BIBLIOGRAPHIC_LEAF_MARKERS = (
    "artigos completos",
    "livros publicados",
    "capítulos de livros",
    "capitulos de livros",
    "trabalhos completos publicados em anais",
)


def resolve_extraction_profile(section_name: str) -> ExtractionProfile:
    normalized = (section_name or "").strip().lower()
    for needle, profile in _SECTION_PROFILE_RULES:
        if needle in normalized:
            return profile
    return "padrao"


def is_bibliographic_parent_section(section_name: str) -> bool:
    normalized = (section_name or "").strip().lower()
    if "produção bibliográfica" not in normalized and "producao bibliografica" not in normalized:
        return False
    return not any(marker in normalized for marker in _BIBLIOGRAPHIC_LEAF_MARKERS)


def should_extract_producoes(section_name: str) -> bool:
    normalized = (section_name or "").strip().lower()
    if is_bibliographic_parent_section(section_name):
        return False
    if any(marker in normalized for marker in _BIBLIOGRAPHIC_LEAF_MARKERS):
        return True
    if "artigo" in normalized or "livro" in normalized or "capítulo" in normalized:
        return True
    return False


def should_extract_eventos_padrao(section_name: str) -> bool:
    normalized = (section_name or "").strip().lower()
    if "participação em eventos" in normalized or "participacao em eventos" in normalized:
        return False
    if "organização de eventos" in normalized or "organizacao de eventos" in normalized:
        return False
    return True


def profile_extra_prompt(profile: ExtractionProfile) -> Optional[str]:
    prompts = {
        "formacao": (
            "Extraia cada titulação (graduação, especialização, mestrado, doutorado, pós-doutorado) "
            "com curso, instituição, anos e área. Indique período sanduíche no exterior se houver."
        ),
        "orientacoes": (
            "Extraia cada orientação ou supervisão (mestrado, doutorado, IC, TCC, pós-doutorado). "
            "Classifique status como em_andamento ou concluida. Inclua nome do orientando e título do trabalho."
        ),
        "bancas": (
            "Extraia participações em bancas (qualificação, defesa, exame) com candidato, título, "
            "instituição, ano e papel (presidente, membro, suplente)."
        ),
        "perfil": (
            "Extraia data da última atualização do currículo, nome para citação, palavras-chave, "
            "resumo do CV e link ORCID se existirem."
        ),
        "eventos_participacao": (
            "Extraia participações em eventos (apresentações, palestras). eh_organizacao deve ser false. "
            "Identifique escopo nacional ou internacional quando possível."
        ),
        "eventos_organizacao": (
            "Extraia eventos que o docente organizou ou coordenou. eh_organizacao deve ser true para todos. "
            "tipo_participacao pode ser organizador ou coordenador."
        ),
        "producao_tecnica": (
            "Extraia produções técnicas: audiovisual, software, material didático, tradução, patente, etc."
        ),
        "premios": (
            "Extraia prêmios, bolsas de produtividade (PQ) e títulos honoríficos com ano e instituição."
        ),
        "grupos_pesquisa": (
            "Extraia grupos de pesquisa CNPq vinculados ao docente: nome, código DGP se houver, "
            "papel (lider, vice_lider, membro) e linha temática."
        ),
    }
    return prompts.get(profile)
