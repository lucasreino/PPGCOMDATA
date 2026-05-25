"""
Sincroniza linhas de pesquisa e docentes do PPGCOM com o cadastro oficial.
Execute: python -m app.utils_fix_linhas
"""

import os
import sys
from typing import Optional

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.core import Professor, LinhaPesquisa
from app.models.enums import TipoDocente
from app.services.professor_lookup import find_professor
from app.services.professor_dedupe import merge_duplicate_professors
from app.services.professor_oficial import get_official_professor_data

LINE1_NAME = "Tecnologias, Audiovisual e Processos Regionais de Comunicação"
LINE2_NAME = "Processos Comunicacionais, Cidadania e Identidades"

LINE1_DESC = (
    "As pesquisas desta linha tem como foco explorar as implicações das tecnologias de comunicação "
    "e do audiovisual nos processos comunicacionais em diversos contextos. A investigação abrange "
    "o impacto das novas tecnologias, como a internet e plataformas digitais, na transformação da "
    "produção e distribuição de conteúdo, além de analisar as práticas de consumo e as novas formas "
    "de interação que surgem com esses avanços. Por outro lado, a linha também examina os processos "
    "comunicacionais em nível regional, investigando como as dinâmicas locais influenciam a construção "
    "de narrativas e a representação cultural."
)

LINE2_DESC = (
    "Esta linha contempla pesquisas que se dedicam a investigar as relações entre os fluxos "
    "de comunicação e a formação das identidades sociais e culturais, com especial atenção aos "
    "processos de construção e negociação da cidadania em contextos contemporâneos."
)

# Cadastro oficial PPGCOM — vínculo no PPGCOM Imperatriz (conforme texto institucional)
# PERMANENTE: texto cita "professor(a) permanente do Programa" ou "docente permanente do PPGCOM"
# COLABORADOR: texto cita "colaborador(a)" ou docente sem vínculo permanente no PPGCOM Imperatriz
PROFESSOR_DATA = [
    {
        "nome_completo": "Izani Pibernat Mustafá",
        "email": "izani.mustafa@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/9088752631596667",
        "id_lattes": "9088752631596667",
        "linha": "linha1",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Rádio, Podcast e Mídia Sonora no Maranhão (RPM)",
        "tematicas": "Rádio; Rádio e Gênero; Rádio e Política; Radiojornalismo; Rádios Universitárias; Podcast",
    },
    {
        "nome_completo": "José Carlos Messias Santos Franco",
        "email": "jose.cmsf@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/8042448829229400",
        "id_lattes": "8042448829229400",
        "linha": "linha1",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Laboratório de Pesquisa em Games, Gambiarras e Mediações em Rede (GamerLab)",
        "tematicas": "TIC, games, cultura hacker, pirataria, consumo participativo",
    },
    {
        "nome_completo": "Larissa Leda Fonseca Rocha",
        "email": "larissa.leda@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/5812508596685080",
        "id_lattes": "5812508596685080",
        "linha": "linha1",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Observatório de Experiências Expandidas em Comunicação (ObEEC)",
        "tematicas": "Experiências expandidas em comunicação",
    },
    {
        "nome_completo": "Marcelli Alves da Silva",
        "email": "marcelli.alves@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/8985071802390376",
        "id_lattes": "8985071802390376",
        "linha": "linha1",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Grupo de Pesquisa em Jornalismo e Cibercultura (GCiber) / G Mídia",
        "tematicas": "Telejornalismo, audiovisual, cibermeio, telerreportagem, jornalismo na web",
    },
    {
        "nome_completo": "Domingos Alves de Almeida",
        "email": "domingos.almeida@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/1919610825042640",
        "id_lattes": "1919610825042640",
        "linha": "linha1",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Grupo de Pesquisa e Criação em Comunicação Audiovisual, Culturas e Artes (GPCOM)",
        "tematicas": "Comunicação e Política, Televisão, História do Jornalismo, América Latina",
    },
    {
        "nome_completo": "Odlinari Ramon Nascimento da Silva",
        "email": "odlinari.silva@ufma.br",
        "link_lattes": "https://lattes.cnpq.br/4303555424897191",
        "id_lattes": "4303555424897191",
        "linha": "linha1",
        "tipo_docente": TipoDocente.COLABORADOR,
        "grupo_pesquisa": "Comunicação e Religiões e Teorias da Comunicação / GMIC",
        "tematicas": "Midiatização da religião; mídia e política; plataformização; epistemologia da Comunicação",
    },
    {
        "nome_completo": "Camilla Quesada Tavares",
        "email": "camilla.tavares@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/1766143822703684",
        "id_lattes": "1766143822703684",
        "linha": "linha2",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Grupo de Pesquisa em Comunicação, Política e Sociedade (COPS)",
        "tematicas": "Comunicação política, jornalismo e desinformação",
    },
    {
        "nome_completo": "Leila Lima de Sousa",
        "email": "sousa.leila@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/9312604992263679",
        "id_lattes": "9312604992263679",
        "linha": "linha2",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Grupo Interdisciplinar Maria Firmina Dos Reis",
        "tematicas": "Gênero, raça e cidadania comunicativa",
    },
    {
        "nome_completo": "Letícia Conceição Martins Cardoso",
        "email": "leticia.cardoso@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/6186532880175192",
        "id_lattes": "6186532880175192",
        "linha": "linha2",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Grupo de Estudos Cultura e Identidade na Contemporaneidade (GECI)",
        "tematicas": "Cultura popular; mediações; identidades; gênero",
    },
    {
        "nome_completo": "Thaisa Cristina Bueno",
        "email": "thaisa.bueno@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/4123207392983951",
        "id_lattes": "4123207392983951",
        "linha": "linha2",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Espelho – Jornalismo, Gênero e Moda",
        "tematicas": "Identidade e trabalho em jornalismo; gênero; jornalismo de moda",
    },
    {
        "nome_completo": "Maria Gislene Carvalho Fonseca",
        "email": "maria.gcf@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/4061348210902950",
        "id_lattes": "4061348210902950",
        "linha": "linha2",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "EsTreMa / Laborejo",
        "tematicas": "Gêneros, sexualidades, corpos, Epistemologias da Comunicação",
    },
    {
        "nome_completo": "Thays Assunção Reis",
        "email": "thays.assuncao@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/7896667981420340",
        "id_lattes": "7896667981420340",
        "linha": "linha2",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Grupo de Pesquisa Jornalismo, Mídia e Memória (JOIMP)",
        "tematicas": "Jornalismo local e regional; plataformas digitais; desinformação",
    },
    {
        "nome_completo": "Michelly Santos de Carvalho",
        "email": "michelly.carvalho@ufma.br",
        "link_lattes": "https://lattes.cnpq.br/0079215403799516",
        "id_lattes": "0079215403799516",
        "linha": "linha2",
        "tipo_docente": TipoDocente.PERMANENTE,
        "grupo_pesquisa": "Grupo Interdisciplinar Maria Firmina Dos Reis",
        "tematicas": "Comunicação, educação, gênero, relações raciais e decolonialidade",
    },
]


def _apply_data(prof: Professor, data: dict, linha_id) -> None:
    prof.nome_completo = data["nome_completo"]
    prof.email = data["email"]
    prof.link_lattes = data["link_lattes"]
    prof.id_lattes = data["id_lattes"]
    prof.linha_pesquisa_id = linha_id
    prof.tipo_docente = data["tipo_docente"]
    prof.status = True
    prof.observacoes = (
        f"Grupo de pesquisa: {data['grupo_pesquisa']}\n"
        f"Temáticas: {data['tematicas']}"
    )


def run_precision_seeding():
    with Session(engine) as session:
        print("=" * 60)
        print("PPGCOMDATA — Sincronização de Linhas e Docentes")
        print("=" * 60)

        stmt1 = select(LinhaPesquisa).where(LinhaPesquisa.nome == LINE1_NAME)
        l1 = session.exec(stmt1).first()
        if not l1:
            l1 = LinhaPesquisa(nome=LINE1_NAME, descricao=LINE1_DESC)
            session.add(l1)
        else:
            l1.descricao = LINE1_DESC
            session.add(l1)

        stmt2 = select(LinhaPesquisa).where(LinhaPesquisa.nome == LINE2_NAME)
        l2 = session.exec(stmt2).first()
        if not l2:
            l2 = LinhaPesquisa(nome=LINE2_NAME, descricao=LINE2_DESC)
            session.add(l2)
        else:
            l2.descricao = LINE2_DESC
            session.add(l2)

        session.commit()
        session.refresh(l1)
        session.refresh(l2)
        official_data = get_official_professor_data()
        print(f"Linha 1: {l1.nome} ({len([d for d in official_data if d['linha'] == 'linha1'])} docentes)")
        print(f"Linha 2: {l2.nome} ({len([d for d in official_data if d['linha'] == 'linha2'])} docentes)")

        profs = list(session.exec(select(Professor)).all())
        official_emails = {d["email"].lower() for d in official_data if d.get("email")}

        print("\n--- Atualizando / criando docentes ---")
        for data in official_data:
            linha_id = l1.id if data["linha"] == "linha1" else l2.id
            prof = find_professor(
                session,
                nome_completo=data["nome_completo"],
                email=data["email"],
                id_lattes=data.get("id_lattes"),
                candidates=profs,
            )

            if prof:
                print(f"  Atualizado: {data['nome_completo']}")
                _apply_data(prof, data, linha_id)
                session.add(prof)
            else:
                print(f"  Criado: {data['nome_completo']}")
                prof = Professor(
                    nome_completo=data["nome_completo"],
                    email=data["email"],
                    status=True,
                )
                _apply_data(prof, data, linha_id)
                session.add(prof)
                profs.append(prof)

        session.commit()

        print("\n--- Mesclando docentes duplicados ---")
        stats = merge_duplicate_professors(session)
        if stats["records_deleted"]:
            print(
                f"  Removidos {stats['records_deleted']} cadastro(s) duplicado(s) "
                f"({stats['groups_merged']} mesclagem(ns))."
            )
        else:
            print("  Nenhuma duplicata encontrada.")

        unmatched = [
            p
            for p in session.exec(select(Professor)).all()
            if (p.email or "").lower() not in official_emails
        ]
        if unmatched:
            print("\n--- Docentes no banco sem correspondência no cadastro oficial ---")
            for p in unmatched:
                print(f"  ⚠️ {p.nome_completo} ({p.email or 'sem e-mail'})")

        cleanup_stmt = select(LinhaPesquisa).where(
            LinhaPesquisa.nome == "Comunicação e Cultura Digital"
        )
        old_l = session.exec(cleanup_stmt).first()
        if old_l:
            session.delete(old_l)
            session.commit()
            print("\nLinha antiga 'Comunicação e Cultura Digital' removida.")

        print("\n--- Sincronização concluída! ---")


if __name__ == "__main__":
    run_precision_seeding()
