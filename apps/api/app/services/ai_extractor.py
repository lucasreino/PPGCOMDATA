import httpx
import json
import logging
from datetime import date, datetime
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import settings
from app.schemas.ai import (
    LattesExtractionResultSchema,
    FormacaoExtractionSchema,
    OrientacaoExtractionSchema,
    BancaExtractionSchema,
    PerfilExtractionSchema,
    EventosExtractionSchema,
    ProducaoTecnicaExtractionSchema,
    PremiosExtractionSchema,
    GruposPesquisaExtractionSchema,
    AIEventoSchema,
)
from app.models.data import (
    PdfSection,
    Projeto,
    Evento,
    Producao,
    Financiamento,
    AlertaLacuna,
    FormacaoAcademica,
    Orientacao,
    Banca,
    PerfilLattes,
    ProducaoTecnica,
    PremioTitulo,
    GrupoPesquisaDocente,
)
from app.models.core import Professor
from app.models.enums import StatusValidacao, FonteDado, NivelFormacao, EscopoEvento
from app.services.extraction_registry import (
    resolve_extraction_profile,
    profile_extra_prompt,
    should_extract_producoes,
    should_extract_eventos_padrao,
    is_bibliographic_parent_section,
    ExtractionProfile,
)
from app.services.dedupe import (
    producao_already_exists,
    projeto_already_exists,
    orientacao_already_exists,
    evento_already_exists,
)
from app.services.lacuna_detector import detect_orientacao_lacunas, detect_producao_lacunas

logger = logging.getLogger("ppgcomdata.ai_extractor")

SYSTEM_PROMPT_BASE = """
Você é um extrator de dados acadêmicos especializado em analisar Currículos Lattes em PDF.
Regras:
- NÃO invente dados. Campos sem evidência explícita devem ficar vazios/nulos.
- Inclua trecho_original que comprove cada item extraído.
- Use confiança alta, media ou baixa conforme a clareza do texto.
- Responda RIGOROSAMENTE no JSON do esquema fornecido.
"""

_PROFILE_SCHEMA: Dict[ExtractionProfile, Type[BaseModel]] = {
    "padrao": LattesExtractionResultSchema,
    "formacao": FormacaoExtractionSchema,
    "orientacoes": OrientacaoExtractionSchema,
    "bancas": BancaExtractionSchema,
    "perfil": PerfilExtractionSchema,
    "eventos_participacao": EventosExtractionSchema,
    "eventos_organizacao": EventosExtractionSchema,
    "producao_tecnica": ProducaoTecnicaExtractionSchema,
    "premios": PremiosExtractionSchema,
    "grupos_pesquisa": GruposPesquisaExtractionSchema,
}

_NIVEL_RANK = {
    NivelFormacao.GRADUACAO: 1,
    NivelFormacao.ESPECIALIZACAO: 2,
    NivelFormacao.MESTRADO: 3,
    NivelFormacao.DOUTORADO: 4,
    NivelFormacao.POS_DOUTORADO: 5,
    NivelFormacao.OUTRA: 0,
}


def inline_refs(schema: Any, defs: Dict[str, Any]) -> Any:
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref_key = schema["$ref"].split("/")[-1]
            return inline_refs(defs[ref_key], defs)
        return {k: inline_refs(v, defs) for k, v in schema.items() if k != "$defs"}
    if isinstance(schema, list):
        return [inline_refs(item, defs) for item in schema]
    return schema


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip()[:10], fmt).date()
        except ValueError:
            continue
    return None


def get_gemini_structured_output(
    section_name: str,
    section_text: str,
    profile: ExtractionProfile,
) -> Dict[str, Any]:
    schema_model = _PROFILE_SCHEMA[profile]
    if not settings.AI_API_KEY:
        logger.warning("AI_API_KEY não configurada. Usando mock generator.")
        return generate_mock_extraction(section_name, section_text, profile)

    extra = profile_extra_prompt(profile) or ""
    producao_hint = ""
    if profile == "padrao" and is_bibliographic_parent_section(section_name):
        producao_hint = (
            "\nIMPORTANTE: Esta seção é apenas o cabeçalho 'Produção bibliográfica'. "
            "NÃO liste artigos, livros ou capítulos aqui (eles estão em subseções). "
            "Retorne producoes como lista vazia.\n"
        )
    prompt = f"""
Analise a seção do Currículo Lattes:

Nome da Seção: {section_name}
{extra}{producao_hint}

Texto da Seção:
{section_text}
"""
    schema_dict = schema_model.model_json_schema()
    schema_dict = inline_refs(schema_dict, schema_dict.get("$defs", {}))
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.AI_MODEL}:generateContent?key={settings.AI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": SYSTEM_PROMPT_BASE}, {"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema_dict,
        },
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            content_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(content_text)
    except Exception as e:
        logger.error(f"Falha na API de IA: {e}")
        return generate_mock_extraction(section_name, section_text, profile)


def generate_mock_extraction(
    section_name: str,
    section_text: str,
    profile: ExtractionProfile,
) -> Dict[str, Any]:
    section_lower = section_name.lower()
    snippet = (section_text or "")[:200].strip() or section_name

    if profile == "formacao":
        return {
            "formacoes": [
                {
                    "nivel": "doutorado",
                    "curso": "Comunicação",
                    "instituicao": "Universidade Federal de Exemplo",
                    "ano_inicio": 2018,
                    "ano_fim": 2022,
                    "area_conhecimento": "Comunicação",
                    "pais": "Brasil",
                    "periodo_sanduiche": False,
                    "instituicao_exterior": None,
                    "confianca_ia": "media",
                    "trecho_original": snippet,
                }
            ],
            "lacunas": [],
        }

    if profile == "orientacoes":
        return {
            "orientacoes": [
                {
                    "tipo": "mestrado",
                    "status": "concluida",
                    "nome_orientando": "Aluno Exemplo",
                    "titulo_trabalho": "Tese de mestrado em comunicação",
                    "instituicao": "UFMA",
                    "ano_inicio": 2020,
                    "ano_conclusao": 2022,
                    "papel": "orientador",
                    "confianca_ia": "media",
                    "trecho_original": snippet,
                    "observacoes": "Mock local",
                }
            ],
            "lacunas": [],
        }

    if profile == "bancas":
        return {
            "bancas": [
                {
                    "tipo": "defesa",
                    "nivel": "mestrado",
                    "nome_candidato": "Candidato Exemplo",
                    "titulo_trabalho": "Dissertação em jornalismo",
                    "instituicao": "UFMA",
                    "ano": 2023,
                    "papel": "presidente",
                    "confianca_ia": "media",
                    "trecho_original": snippet,
                    "observacoes": "Mock local",
                }
            ],
            "lacunas": [],
        }

    if profile == "perfil":
        return {
            "perfil": {
                "data_ultima_atualizacao": "2025-01-15",
                "resumo_cv": None,
                "palavras_chave": ["comunicação", "jornalismo"],
                "nome_citacao": "EXEMPLO, A.",
                "link_orcid": None,
                "confianca_ia": "baixa",
                "trecho_original": snippet,
            },
            "lacunas": [],
        }

    result: Dict[str, Any] = {
        "projetos": [],
        "eventos": [],
        "producoes": [],
        "financiamentos": [],
        "lacunas": [],
    }
    if "projeto" in section_lower:
        result["projetos"].append({
            "titulo": "Pesquisa em Comunicação Digital e Algoritmos no PPGCOM",
            "tipo": "pesquisa",
            "situacao": "em andamento",
            "ano_inicio": 2024,
            "ano_fim": None,
            "descricao": "Análise da recepção em redes sociais.",
            "papel_docente": "coordenador",
            "instituicoes": ["UFMA", "PPGCOM"],
            "financiamento_mencionado": True,
            "agencia_fomento": "FAPEMA",
            "confianca_ia": "alta",
            "trecho_original": snippet,
            "observacoes": "Mock local",
        })
    if profile in ("eventos_participacao", "eventos_organizacao"):
        result = {
            "eventos": [{
                "nome_evento": "Encontro da Compós 2025",
                "ano": 2025,
                "cidade": "São Luís",
                "pais": "Brasil",
                "tipo_participacao": "organizador" if profile == "eventos_organizacao" else "apresentacao",
                "titulo_trabalho": "Comunicação e algoritmos",
                "eh_organizacao": profile == "eventos_organizacao",
                "escopo": "nacional",
                "financiamento_mencionado": False,
                "confianca_ia": "alta",
                "trecho_original": snippet,
            }],
            "lacunas": [],
        }
        return result

    if profile == "producao_tecnica":
        return {
            "producoes_tecnicas": [{
                "tipo": "audiovisual",
                "titulo": "Documentário regional de comunicação",
                "ano": 2024,
                "instituicao": "UFMA",
                "descricao": "Produção audiovisual acadêmica",
                "confianca_ia": "media",
                "trecho_original": snippet,
            }],
            "lacunas": [],
        }

    if profile == "premios":
        return {
            "premios": [{
                "tipo": "premio",
                "nome": "Prêmio de Artigo Científico",
                "ano": 2023,
                "instituicao_concedente": "INTERCOM",
                "confianca_ia": "media",
                "trecho_original": snippet,
            }],
            "lacunas": [],
        }

    if profile == "grupos_pesquisa":
        return {
            "grupos": [{
                "nome_grupo": "Grupo de Pesquisa em Comunicação e Sociedade",
                "papel": "membro",
                "linha_tematica": "Comunicação política",
                "instituicao": "UFMA",
                "confianca_ia": "media",
                "trecho_original": snippet,
            }],
            "lacunas": [],
        }

    if "evento" in section_lower or "participação" in section_lower:
        result["eventos"].append({
            "nome_evento": "Encontro da Compós 2025",
            "ano": 2025,
            "cidade": "São Luís",
            "pais": "Brasil",
            "tipo_participacao": "apresentacao",
            "titulo_trabalho": "Comunicação e algoritmos",
            "financiamento_mencionado": False,
            "fonte_financiamento": None,
            "confianca_ia": "alta",
            "trecho_original": snippet,
            "observacoes": "Mock local",
        })
    if should_extract_producoes(section_name):
        result["producoes"].append({
            "tipo": "artigo",
            "titulo": "Jornalismo digital no Nordeste",
            "ano": 2024,
            "veiculo": "Revista Brasileira de Ciências da Comunicação",
            "doi": None,
            "isbn": None,
            "issn": None,
            "evento_relacionado": None,
            "autores": "Autor Exemplo; Docente do Currículo",
            "qualis": "A2",
            "idioma": "pt",
            "indexadores": None,
            "volume": "47",
            "paginas": "12-28",
            "eh_primeiro_autor": True,
            "confianca_ia": "alta",
            "trecho_original": snippet,
            "observacoes": "Mock local",
        })
    return result


def _save_lacunas(session: Session, section: PdfSection, lacunas: list) -> int:
    count = 0
    for gap in lacunas:
        session.add(
            AlertaLacuna(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                tipo_lacuna=gap.tipo_lacuna,
                descricao=gap.descricao,
                gravidade=gap.gravidade,
                acao_recomendada=gap.acao_recomendada,
                resolvido=False,
            )
        )
        count += 1
    return count


def _update_professor_titulacao(session: Session, professor_id: str) -> None:
    prof = session.get(Professor, professor_id)
    if not prof:
        return
    formacoes = session.exec(
        select(FormacaoAcademica).where(FormacaoAcademica.professor_id == professor_id)
    ).all()
    best: NivelFormacao | None = None
    for f in formacoes:
        if best is None or _NIVEL_RANK.get(f.nivel, 0) > _NIVEL_RANK.get(best, 0):
            best = f.nivel
    if best:
        prof.titulacao_maxima = best.value
        session.add(prof)


def _filter_padrao_producoes(section: PdfSection, data: LattesExtractionResultSchema) -> LattesExtractionResultSchema:
    updates: dict = {}
    if not should_extract_producoes(section.nome_secao):
        updates["producoes"] = []
    if not should_extract_eventos_padrao(section.nome_secao):
        updates["eventos"] = []
    if is_bibliographic_parent_section(section.nome_secao):
        updates["producoes"] = []
    if updates:
        return data.model_copy(update=updates)
    return data


def _save_evento(
    session: Session,
    section: PdfSection,
    ev: AIEventoSchema,
    force_organizacao: Optional[bool] = None,
) -> bool:
    eh_org = force_organizacao if force_organizacao is not None else ev.eh_organizacao
    if evento_already_exists(
        session,
        section.professor_id,
        section.curriculo_upload_id,
        ev.nome_evento,
        ev.ano,
        eh_org,
    ):
        return False
    session.add(
        Evento(
            professor_id=section.professor_id,
            curriculo_upload_id=section.curriculo_upload_id,
            nome_evento=ev.nome_evento,
            ano=ev.ano,
            cidade=ev.cidade,
            pais=ev.pais,
            tipo_participacao=ev.tipo_participacao,
            titulo_trabalho=ev.titulo_trabalho,
            eh_organizacao=eh_org,
            escopo=ev.escopo,
            instituicao_promotora=ev.instituicao_promotora,
            financiamento_mencionado=ev.financiamento_mencionado,
            fonte_financiamento=ev.fonte_financiamento,
            fonte_dado=FonteDado.PDF_LATTES,
            confianca_ia=ev.confianca_ia,
            trecho_original=ev.trecho_original,
            status_validacao=StatusValidacao.PENDENTE,
        )
    )
    return True


def _persist_padrao(session: Session, section: PdfSection, data: LattesExtractionResultSchema) -> Dict[str, int]:
    data = _filter_padrao_producoes(section, data)
    metrics = {
        "projetos_extraidos": 0,
        "eventos_extraidos": 0,
        "producoes_extraidas": 0,
        "producoes_ignoradas_duplicata": 0,
        "financiamentos_extraidos": 0,
        "lacunas_extraidas": 0,
    }
    seen_titles: set[str] = set()

    for proj in data.projetos:
        if projeto_already_exists(
            session,
            section.professor_id,
            section.curriculo_upload_id,
            proj.titulo,
            proj.ano_inicio,
        ):
            continue
        session.add(
            Projeto(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                titulo=proj.titulo,
                tipo=proj.tipo,
                situacao=proj.situacao,
                ano_inicio=proj.ano_inicio,
                ano_fim=proj.ano_fim,
                descricao=proj.descricao,
                papel_docente=proj.papel_docente,
                instituicoes=", ".join(proj.instituicoes) if proj.instituicoes else None,
                financiamento_mencionado=proj.financiamento_mencionado,
                agencia_fomento=proj.agencia_fomento,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca_ia=proj.confianca_ia,
                trecho_original=proj.trecho_original,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        metrics["projetos_extraidos"] += 1

    for ev in data.eventos:
        if _save_evento(session, section, ev, force_organizacao=False):
            metrics["eventos_extraidos"] += 1

    for prod in data.producoes:
        title_key = (prod.titulo or "").strip().lower()
        batch_key = f"{title_key}|{prod.ano}|{prod.tipo}"
        if batch_key in seen_titles:
            metrics["producoes_ignoradas_duplicata"] += 1
            continue
        if producao_already_exists(
            session,
            section.professor_id,
            section.curriculo_upload_id,
            prod.titulo,
            prod.ano,
            prod.tipo,
        ):
            metrics["producoes_ignoradas_duplicata"] += 1
            continue
        seen_titles.add(batch_key)
        session.add(
            Producao(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                tipo=prod.tipo,
                titulo=prod.titulo,
                ano=prod.ano,
                veiculo=prod.veiculo,
                doi=prod.doi,
                isbn=prod.isbn,
                issn=prod.issn,
                evento_relacionado=prod.evento_relacionado,
                autores=prod.autores,
                qualis=prod.qualis,
                idioma=prod.idioma,
                indexadores=prod.indexadores,
                volume=prod.volume,
                paginas=prod.paginas,
                eh_primeiro_autor=prod.eh_primeiro_autor,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca_ia=prod.confianca_ia,
                trecho_original=prod.trecho_original,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        metrics["producoes_extraidas"] += 1

    prod_lacunas = detect_producao_lacunas(data.producoes)
    metrics["lacunas_extraidas"] += _save_lacunas(session, section, prod_lacunas)

    for fin in data.financiamentos:
        session.add(
            Financiamento(
                professor_id=section.professor_id,
                tipo=fin.tipo,
                fonte=fin.fonte,
                agencia=fin.agencia,
                edital=fin.edital,
                numero_processo=fin.numero_processo,
                ano=fin.ano,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca=fin.confianca,
                trecho_original=fin.trecho_original,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        metrics["financiamentos_extraidos"] += 1

    metrics["lacunas_extraidas"] += _save_lacunas(session, section, data.lacunas)
    return metrics


def _persist_formacao(session: Session, section: PdfSection, data: FormacaoExtractionSchema) -> Dict[str, int]:
    count = 0
    for item in data.formacoes:
        session.add(
            FormacaoAcademica(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                nivel=item.nivel,
                curso=item.curso,
                instituicao=item.instituicao,
                ano_inicio=item.ano_inicio,
                ano_fim=item.ano_fim,
                area_conhecimento=item.area_conhecimento,
                pais=item.pais,
                periodo_sanduiche=item.periodo_sanduiche,
                instituicao_exterior=item.instituicao_exterior,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca_ia=item.confianca_ia,
                trecho_original=item.trecho_original,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    _update_professor_titulacao(session, section.professor_id)
    lacunas = _save_lacunas(session, section, data.lacunas)
    return {"formacoes_extraidas": count, "lacunas_extraidas": lacunas}


def _persist_orientacoes(session: Session, section: PdfSection, data: OrientacaoExtractionSchema) -> Dict[str, int]:
    count = 0
    for item in data.orientacoes:
        if orientacao_already_exists(
            session,
            section.professor_id,
            section.curriculo_upload_id,
            item.nome_orientando,
            item.titulo_trabalho,
            item.ano_inicio,
        ):
            continue
        session.add(
            Orientacao(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                tipo=item.tipo,
                status=item.status,
                nome_orientando=item.nome_orientando,
                titulo_trabalho=item.titulo_trabalho,
                instituicao=item.instituicao,
                ano_inicio=item.ano_inicio,
                ano_conclusao=item.ano_conclusao,
                papel=item.papel,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca_ia=item.confianca_ia,
                trecho_original=item.trecho_original,
                observacoes=item.observacoes,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    lacunas = _save_lacunas(session, section, data.lacunas)
    rule_lacunas = detect_orientacao_lacunas(data.orientacoes)
    lacunas += _save_lacunas(session, section, rule_lacunas)
    return {"orientacoes_extraidas": count, "lacunas_extraidas": lacunas}


def _persist_bancas(session: Session, section: PdfSection, data: BancaExtractionSchema) -> Dict[str, int]:
    count = 0
    for item in data.bancas:
        session.add(
            Banca(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                tipo=item.tipo,
                nivel=item.nivel,
                nome_candidato=item.nome_candidato,
                titulo_trabalho=item.titulo_trabalho,
                instituicao=item.instituicao,
                ano=item.ano,
                papel=item.papel,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca_ia=item.confianca_ia,
                trecho_original=item.trecho_original,
                observacoes=item.observacoes,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    lacunas = _save_lacunas(session, section, data.lacunas)
    return {"bancas_extraidas": count, "lacunas_extraidas": lacunas}


def _persist_perfil(session: Session, section: PdfSection, data: PerfilExtractionSchema) -> Dict[str, int]:
    count = 0
    if data.perfil:
        p = data.perfil
        kw = ", ".join(p.palavras_chave) if p.palavras_chave else None
        parsed_date = _parse_optional_date(p.data_ultima_atualizacao)
        session.add(
            PerfilLattes(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                data_ultima_atualizacao=parsed_date,
                resumo_cv=p.resumo_cv,
                palavras_chave=kw,
                nome_citacao=p.nome_citacao,
                link_orcid=p.link_orcid,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca_ia=p.confianca_ia,
                trecho_original=p.trecho_original,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count = 1
        prof = session.get(Professor, section.professor_id)
        if prof and parsed_date:
            prof.data_ultima_atualizacao_lattes = parsed_date
            if p.nome_citacao:
                prof.nome_citacao = p.nome_citacao
            session.add(prof)
    lacunas = _save_lacunas(session, section, data.lacunas)
    return {"perfis_extraidos": count, "lacunas_extraidas": lacunas}


def _persist_eventos(
    session: Session,
    section: PdfSection,
    data: EventosExtractionSchema,
    force_organizacao: bool,
) -> Dict[str, int]:
    count = 0
    for ev in data.eventos:
        if _save_evento(session, section, ev, force_organizacao=force_organizacao):
            count += 1
    lacunas = _save_lacunas(session, section, data.lacunas)
    return {"eventos_extraidos": count, "lacunas_extraidas": lacunas}


def _persist_producao_tecnica(
    session: Session, section: PdfSection, data: ProducaoTecnicaExtractionSchema
) -> Dict[str, int]:
    count = 0
    for item in data.producoes_tecnicas:
        session.add(
            ProducaoTecnica(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                tipo=item.tipo,
                titulo=item.titulo,
                ano=item.ano,
                instituicao=item.instituicao,
                descricao=item.descricao,
                url=item.url,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca_ia=item.confianca_ia,
                trecho_original=item.trecho_original,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    lacunas = _save_lacunas(session, section, data.lacunas)
    return {"producoes_tecnicas_extraidas": count, "lacunas_extraidas": lacunas}


def _persist_premios(session: Session, section: PdfSection, data: PremiosExtractionSchema) -> Dict[str, int]:
    count = 0
    for item in data.premios:
        session.add(
            PremioTitulo(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                tipo=item.tipo,
                nome=item.nome,
                ano=item.ano,
                instituicao_concedente=item.instituicao_concedente,
                descricao=item.descricao,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca_ia=item.confianca_ia,
                trecho_original=item.trecho_original,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    lacunas = _save_lacunas(session, section, data.lacunas)
    return {"premios_extraidos": count, "lacunas_extraidas": lacunas}


def _persist_grupos(session: Session, section: PdfSection, data: GruposPesquisaExtractionSchema) -> Dict[str, int]:
    count = 0
    for item in data.grupos:
        session.add(
            GrupoPesquisaDocente(
                professor_id=section.professor_id,
                curriculo_upload_id=section.curriculo_upload_id,
                nome_grupo=item.nome_grupo,
                codigo_dgp=item.codigo_dgp,
                papel=item.papel,
                linha_tematica=item.linha_tematica,
                instituicao=item.instituicao,
                fonte_dado=FonteDado.PDF_LATTES,
                confianca_ia=item.confianca_ia,
                trecho_original=item.trecho_original,
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    lacunas = _save_lacunas(session, section, data.lacunas)
    return {"grupos_extraidos": count, "lacunas_extraidas": lacunas}


def extract_and_save_section_data(session: Session, pdf_section_id: str) -> Dict[str, Any]:
    section = session.get(PdfSection, pdf_section_id)
    if not section:
        raise ValueError(f"Seção ID {pdf_section_id} não encontrada.")

    profile = resolve_extraction_profile(section.nome_secao)
    logger.info(
        f"Extração IA — seção '{section.nome_secao}' perfil={profile} upload={section.curriculo_upload_id}"
    )

    raw = get_gemini_structured_output(section.nome_secao, section.texto_secao, profile)
    schema_model = _PROFILE_SCHEMA[profile]
    validated = schema_model(**raw)

    if profile == "padrao":
        metrics = _persist_padrao(session, section, validated)
    elif profile == "formacao":
        metrics = _persist_formacao(session, section, validated)
    elif profile == "orientacoes":
        metrics = _persist_orientacoes(session, section, validated)
    elif profile == "bancas":
        metrics = _persist_bancas(session, section, validated)
    elif profile == "eventos_participacao":
        metrics = _persist_eventos(session, section, validated, force_organizacao=False)
    elif profile == "eventos_organizacao":
        metrics = _persist_eventos(session, section, validated, force_organizacao=True)
    elif profile == "producao_tecnica":
        metrics = _persist_producao_tecnica(session, section, validated)
    elif profile == "premios":
        metrics = _persist_premios(session, section, validated)
    elif profile == "grupos_pesquisa":
        metrics = _persist_grupos(session, section, validated)
    else:
        metrics = _persist_perfil(session, section, validated)

    section.status_extracao = True
    session.add(section)
    session.commit()
    logger.info(f"Extração concluída seção {pdf_section_id}: {metrics}")
    return metrics
