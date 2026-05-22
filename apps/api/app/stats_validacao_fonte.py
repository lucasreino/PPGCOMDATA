"""Totais de validação por fonte (xml_lattes vs pdf_lattes)."""
from sqlmodel import Session, select, func

from app.database import engine
from app.models.data import (
    Banca,
    Evento,
    FormacaoAcademica,
    Orientacao,
    PerfilLattes,
    Producao,
    Projeto,
)
from app.models.enums import FonteDado, StatusValidacao

MODELS = [
    ("producoes", Producao),
    ("projetos", Projeto),
    ("orientacoes", Orientacao),
    ("bancas", Banca),
    ("eventos", Evento),
    ("formacoes", FormacaoAcademica),
    ("perfis", PerfilLattes),
]


def row_count(session, model, fonte, status=None):
    stmt = select(func.count()).select_from(model).where(model.fonte_dado == fonte)
    if status is not None:
        stmt = stmt.where(model.status_validacao == status)
    return session.exec(stmt).one()


def main() -> None:
    with Session(engine) as s:
        sep = "=" * 72
        print(sep)
        print(
            f"{'ENTIDADE':<14} {'FONTE':<12} {'CONF':>6} {'PEND':>6} "
            f"{'DESC':>6} {'EDIT':>6} {'OUTR':>6} {'TOTAL':>6}"
        )
        print("-" * 72)
        grand = {k: 0 for k in ("confirmado", "pendente", "descartado", "editado", "outro", "total")}
        for label, model in MODELS:
            for fonte in (FonteDado.XML_LATTES, FonteDado.PDF_LATTES):
                conf = row_count(s, model, fonte, StatusValidacao.CONFIRMADO)
                pend = row_count(s, model, fonte, StatusValidacao.PENDENTE)
                desc = row_count(s, model, fonte, StatusValidacao.DESCARTADO)
                edit = row_count(s, model, fonte, StatusValidacao.EDITADO)
                total = row_count(s, model, fonte)
                outro = total - conf - pend - desc - edit
                if total == 0:
                    continue
                print(
                    f"{label:<14} {fonte.value:<12} {conf:>6} {pend:>6} "
                    f"{desc:>6} {edit:>6} {outro:>6} {total:>6}"
                )
                for key, val in [
                    ("confirmado", conf),
                    ("pendente", pend),
                    ("descartado", desc),
                    ("editado", edit),
                    ("outro", outro),
                    ("total", total),
                ]:
                    grand[key] += val
        print("-" * 72)
        print(
            f"{'TOTAL GERAL':<14} {'':<12} {grand['confirmado']:>6} {grand['pendente']:>6} "
            f"{grand['descartado']:>6} {grand['editado']:>6} {grand['outro']:>6} {grand['total']:>6}"
        )
        print()
        print("=== RESUMO POR FONTE ===")
        for fonte in (FonteDado.XML_LATTES, FonteDado.PDF_LATTES):
            conf = pend = desc = total = 0
            for _, model in MODELS:
                conf += row_count(s, model, fonte, StatusValidacao.CONFIRMADO)
                pend += row_count(s, model, fonte, StatusValidacao.PENDENTE)
                desc += row_count(s, model, fonte, StatusValidacao.DESCARTADO)
                total += row_count(s, model, fonte)
            print(
                f"{fonte.value}: total={total} | confirmado={conf} | "
                f"pendente={pend} | descartado={desc}"
            )


if __name__ == "__main__":
    main()
