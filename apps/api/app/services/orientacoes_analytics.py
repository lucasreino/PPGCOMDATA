"""Painel de orientações: tipo, status, ano, docente."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from sqlmodel import Session, select

from app.models.core import Professor
from app.models.data import Orientacao
from app.models.enums import StatusOrientacao, TipoOrientacao

TIPO_ORDER = (
    TipoOrientacao.DOUTORADO,
    TipoOrientacao.MESTRADO,
    TipoOrientacao.POS_DOUTORADO,
    TipoOrientacao.IC,
    TipoOrientacao.TCC,
    TipoOrientacao.OUTRA,
)

TIPO_LABELS: Dict[str, str] = {
    "doutorado": "Doutorado",
    "mestrado": "Mestrado",
    "pos_doutorado": "Pós-doutorado",
    "ic": "Iniciação científica",
    "tcc": "TCC / Graduação",
    "outra": "Outras orientações",
}

STATUS_LABELS: Dict[str, str] = {
    "concluida": "Concluídas",
    "em_andamento": "Em andamento",
}


def _enum_val(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _label_tipo(tipo: str) -> str:
    return TIPO_LABELS.get(tipo, tipo.replace("_", " ").title())


def _sort_key_orientacao(o: Orientacao) -> tuple:
    conclusao = int(o.ano_conclusao or 0)
    inicio = int(o.ano_inicio or 0)
    primary = max(conclusao, inicio)
    if conclusao == 0 and _enum_val(o.status) == StatusOrientacao.EM_ANDAMENTO.value:
        from datetime import datetime

        primary = max(primary, inicio or datetime.now().year)
    return (-primary, -(inicio or 0))


def _in_year_range(
    o: Orientacao,
    ano_inicio: Optional[int],
    ano_fim: Optional[int],
) -> bool:
    if ano_inicio is None and ano_fim is None:
        return True
    years = [y for y in (o.ano_inicio, o.ano_conclusao) if y is not None]
    if not years:
        return _enum_val(o.status) == StatusOrientacao.EM_ANDAMENTO.value
    for y in years:
        if ano_inicio is not None and y < ano_inicio:
            continue
        if ano_fim is not None and y > ano_fim:
            continue
        return True
    return False


def _serialize(
    o: Orientacao,
    prof_nomes: Dict[str, str],
) -> Dict[str, Any]:
    pid = str(o.professor_id)
    tipo = _enum_val(o.tipo)
    status = _enum_val(o.status)
    ano_ref = o.ano_conclusao or o.ano_inicio
    return {
        "id": str(o.id),
        "professor_id": pid,
        "professor_nome": prof_nomes.get(pid, "Docente"),
        "tipo": tipo,
        "tipo_label": _label_tipo(tipo),
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "nome_orientando": o.nome_orientando,
        "titulo_trabalho": o.titulo_trabalho,
        "instituicao": o.instituicao,
        "ano_inicio": o.ano_inicio,
        "ano_conclusao": o.ano_conclusao,
        "ano_referencia": ano_ref,
        "papel": _enum_val(o.papel),
    }


def _group_items(
    items: List[Dict[str, Any]],
    key_fn: Callable[[Dict[str, Any]], str],
    label_fn: Callable[[str], str],
    order: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in items:
        buckets[key_fn(item)].append(item)

    def sort_items(lst: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            lst,
            key=lambda x: (-(x.get("ano_referencia") or 0), x.get("nome_orientando") or ""),
        )

    groups: List[Dict[str, Any]] = []
    seen = set()

    if order:
        for key in order:
            if key in buckets:
                lst = sort_items(buckets[key])
                groups.append(
                    {
                        "key": key,
                        "label": label_fn(key),
                        "count": len(lst),
                        "items": lst,
                    }
                )
                seen.add(key)

    for key, lst in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if key in seen:
            continue
        lst = sort_items(lst)
        groups.append({"key": key, "label": label_fn(key), "count": len(lst), "items": lst})

    return groups


def build_orientacoes_insights(
    session: Session,
    apply_prof: Callable,
    apply_validacao: Callable,
    ano_inicio: Optional[int],
    ano_fim: Optional[int],
) -> Dict[str, Any]:
    stmt = select(Orientacao)
    stmt = apply_prof(stmt, Orientacao)
    stmt = apply_validacao(stmt, Orientacao)
    rows = session.exec(stmt).all()
    rows = [o for o in rows if _in_year_range(o, ano_inicio, ano_fim)]

    prof_cache: Dict[str, str] = {
        str(p.id): p.nome_completo or "Docente"
        for p in session.exec(select(Professor)).all()
    }

    items = [_serialize(o, prof_cache) for o in sorted(rows, key=_sort_key_orientacao)]
    total = len(items)
    concluidas = sum(1 for i in items if i["status"] == StatusOrientacao.CONCLUIDA.value)
    em_andamento = total - concluidas

    por_tipo_count: Dict[str, int] = defaultdict(int)
    por_status_count: Dict[str, int] = defaultdict(int)
    por_ano_count: Dict[int, int] = defaultdict(int)
    prof_tipo: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    prof_meta: Dict[str, str] = {}

    for it in items:
        por_tipo_count[it["tipo"]] += 1
        por_status_count[it["status"]] += 1
        ano = it.get("ano_referencia")
        if ano:
            por_ano_count[int(ano)] += 1
        pid = it["professor_id"]
        prof_meta[pid] = it["professor_nome"]
        prof_tipo[pid][it["tipo"]] += 1

    tipo_order = [_enum_val(t) for t in TIPO_ORDER]
    por_tipo = [
        {
            "tipo": t,
            "label": _label_tipo(t),
            "count": por_tipo_count[t],
            "percent": round((por_tipo_count[t] / total) * 100, 1) if total else 0.0,
        }
        for t in tipo_order
        if por_tipo_count.get(t)
    ]
    for t, c in sorted(por_tipo_count.items(), key=lambda x: (-x[1], x[0])):
        if t not in tipo_order:
            por_tipo.append(
                {
                    "tipo": t,
                    "label": _label_tipo(t),
                    "count": c,
                    "percent": round((c / total) * 100, 1) if total else 0.0,
                }
            )

    por_status = [
        {
            "status": s,
            "label": STATUS_LABELS[s],
            "count": por_status_count[s],
            "percent": round((por_status_count[s] / total) * 100, 1) if total else 0.0,
        }
        for s in (StatusOrientacao.CONCLUIDA.value, StatusOrientacao.EM_ANDAMENTO.value)
        if por_status_count.get(s)
    ]

    por_ano = [
        {
            "ano": ano,
            "count": cnt,
            "percent": round((cnt / total) * 100, 1) if total else 0.0,
        }
        for ano, cnt in sorted(por_ano_count.items(), key=lambda x: -x[0])
    ]

    professor_por_tipo: Dict[str, Dict[str, int]] = {}
    for pid, counts in prof_tipo.items():
        nome = prof_meta.get(pid, pid)
        professor_por_tipo[nome] = {t: counts.get(t, 0) for t in tipo_order if counts.get(t, 0)}

    por_tipo_grupos = _group_items(
        items,
        lambda x: x["tipo"],
        _label_tipo,
        tipo_order,
    )
    por_status_grupos = _group_items(
        items,
        lambda x: x["status"],
        lambda k: STATUS_LABELS.get(k, k),
        [StatusOrientacao.CONCLUIDA.value, StatusOrientacao.EM_ANDAMENTO.value],
    )
    por_ano_grupos = _group_items(
        items,
        lambda x: str(x.get("ano_referencia") or "Sem ano"),
        lambda k: k if k == "Sem ano" else f"Ano {k}",
    )
    por_professor_grupos = _group_items(
        items,
        lambda x: x["professor_id"],
        lambda pid: prof_meta.get(pid, "Docente"),
    )

    return {
        "total": total,
        "concluidas": concluidas,
        "em_andamento": em_andamento,
        "tipos": [p["tipo"] for p in por_tipo],
        "por_tipo": por_tipo,
        "por_status": por_status,
        "por_ano": por_ano,
        "professor_por_tipo": professor_por_tipo,
        "por_tipo_grupos": por_tipo_grupos,
        "por_status_grupos": por_status_grupos,
        "por_ano_grupos": por_ano_grupos,
        "por_professor_grupos": por_professor_grupos,
        "orientacoes": items[:150],
    }
