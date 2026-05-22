"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ExternalLink, Settings } from "lucide-react";
import type { ProfessorCatalog, ProfessorResumo, ProfileTab } from "@/lib/types";
import type { ProfessorDadosPayload } from "@/lib/map-professor-dados";
import { groupOrientacoesByTipo } from "@/lib/orientacao-groups";
import { groupProducoesByTipo } from "@/lib/producao-groups";
import { ProfessorAvatar } from "./ProfessorAvatar";
import { ResumoAcademicoCard } from "@/components/academic/ResumoAcademicoCard";

const TABS: { id: ProfileTab; label: string }[] = [
  { id: "resumo", label: "Resumo" },
  { id: "projetos", label: "Projetos" },
  { id: "producoes", label: "Produções" },
  { id: "eventos", label: "Eventos" },
  { id: "orientacoes", label: "Orientações" },
  { id: "financiamentos", label: "Financiamentos" },
  { id: "formacoes_academicas", label: "Formação" },
  { id: "bancas", label: "Bancas" },
  { id: "producoes_tecnicas", label: "Prod. técnica" },
  { id: "premios", label: "Prêmios" },
  { id: "grupos_pesquisa", label: "Grupos" },
];

function countFor(tab: ProfileTab, d: ProfessorDadosPayload): number {
  const map: Record<ProfileTab, number> = {
    resumo: 0,
    projetos: d.projetos.length,
    producoes: d.producoes.length,
    eventos: d.eventos.length,
    orientacoes: d.orientacoes.length,
    financiamentos: d.financiamentos.length,
    formacoes_academicas: d.formacoes_academicas.length,
    bancas: d.bancas.length,
    producoes_tecnicas: d.producoes_tecnicas.length,
    premios: d.premios.length,
    grupos_pesquisa: d.grupos_pesquisa.length,
  };
  return map[tab] ?? 0;
}

export function ProfessorProfileView({
  prof,
  dados,
  resumo,
}: {
  prof: ProfessorCatalog;
  dados: ProfessorDadosPayload;
  resumo: ProfessorResumo | null;
}) {
  const [tab, setTab] = useState<ProfileTab>("resumo");
  const orientacoesPorTipo = useMemo(
    () => groupOrientacoesByTipo(dados.orientacoes),
    [dados.orientacoes]
  );
  const producoesPorTipo = useMemo(
    () => groupProducoesByTipo(dados.producoes),
    [dados.producoes]
  );
  const linha = prof.linha_pesquisa?.nome ?? "—";
  const tipo =
    prof.tipo_docente.charAt(0).toUpperCase() + prof.tipo_docente.slice(1);

  return (
    <div className="space-y-6">
      <div className="glow-card rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row gap-6 items-start">
        <ProfessorAvatar
          nome={prof.nome_completo}
          id={prof.id}
          id_lattes={prof.id_lattes}
          foto_url={prof.foto_url}
          size="xl"
        />
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold text-white">{prof.nome_completo}</h1>
          <p className="text-sm text-slate-400 mt-1">{linha}</p>
          <div className="flex flex-wrap gap-2 mt-3 text-[10px]">
            <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-semibold uppercase">
              {tipo}
            </span>
            {prof.titulacao_maxima && (
              <span className="px-2 py-0.5 rounded-full bg-indigo-950/60 text-indigo-300 border border-indigo-900/50 capitalize">
                {prof.titulacao_maxima}
              </span>
            )}
          </div>
          {prof.email && (
            <p className="text-xs text-slate-500 mt-2">{prof.email}</p>
          )}
          <div className="flex flex-wrap gap-3 mt-4">
            {prof.link_lattes && (
              <a
                href={prof.link_lattes}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300"
              >
                Currículo Lattes
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
            <Link
              href={`/?view=validacao&professor_id=${prof.id}`}
              className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400 hover:text-slate-200"
            >
              <Settings className="w-3 h-3" />
              Validar e editar dados
            </Link>
          </div>
        </div>
      </div>

      {resumo && <ResumoAcademicoCard resumo={resumo} />}

      <div className="flex flex-wrap gap-1.5 pb-1 border-b border-slate-800">
        {TABS.map((t) => {
          const n = countFor(t.id, dados);
          if (t.id !== "resumo" && n === 0) return null;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`text-[11px] font-semibold px-3 py-1.5 rounded-lg transition-colors ${
                tab === t.id
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              {t.label}
              {t.id !== "resumo" && (
                <span className="ml-1 opacity-70">({n})</span>
              )}
            </button>
          );
        })}
      </div>

      <div className="space-y-4">
        {tab === "resumo" && <ResumoTab prof={prof} dados={dados} resumo={resumo} />}
        {tab === "projetos" && (
          <ListPanel
            empty="Nenhum projeto registrado."
            items={dados.projetos.map((p) => (
              <RecordCard key={p.id} badge={p.tipo} title={p.titulo} meta={`${p.ano_inicio} — ${p.ano_fim ?? "Atual"} · ${p.papel_docente}`} body={p.descricao} />
            ))}
          />
        )}
        {tab === "eventos" && (
          <ListPanel
            empty="Nenhum evento registrado."
            items={dados.eventos.map((e) => (
              <RecordCard
                key={e.id}
                badge={e.eh_organizacao ? "organização" : e.tipo_participacao}
                title={e.nome_evento}
                meta={`${e.ano} · ${e.cidade}, ${e.pais}`}
                body={e.titulo_trabalho}
              />
            ))}
          />
        )}
        {tab === "producoes" &&
          producoesPorTipo.map((group) => (
            <section key={group.tipo} className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-2">
                {group.label}
                <span className="text-slate-500 font-normal">({group.items.length})</span>
              </h3>
              {group.items.map((p) => (
                <RecordCard
                  key={p.id}
                  badge={p.tipo}
                  title={p.titulo}
                  meta={`${p.ano} · ${p.veiculo}${p.qualis ? ` · Qualis ${p.qualis}` : ""}`}
                />
              ))}
            </section>
          ))}
        {tab === "producoes" && dados.producoes.length === 0 && (
          <EmptyMsg text="Nenhuma produção registrada." />
        )}
        {tab === "financiamentos" && (
          <ListPanel
            empty="Nenhum financiamento registrado."
            items={dados.financiamentos.map((f) => (
              <RecordCard
                key={f.id}
                badge={f.tipo}
                title={`${f.fonte} — ${f.agencia}`}
                meta={`${f.ano}${f.valor ? ` · ${f.valor}` : ""}`}
              />
            ))}
          />
        )}
        {tab === "orientacoes" &&
          orientacoesPorTipo.map((group) => (
            <section key={group.tipo} className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-2">
                {group.label}
                <span className="text-slate-500 font-normal">({group.items.length})</span>
              </h3>
              {group.items.map((o) => (
                <RecordCard
                  key={o.id}
                  badge={`${o.tipo} · ${o.status}`}
                  title={o.nome_orientando || "Orientando não identificado"}
                  meta={[o.ano_inicio && `Início ${o.ano_inicio}`, o.ano_conclusao && `Conclusão ${o.ano_conclusao}`]
                    .filter(Boolean)
                    .join(" · ")}
                  body={o.titulo_trabalho || undefined}
                />
              ))}
            </section>
          ))}
        {tab === "orientacoes" && dados.orientacoes.length === 0 && (
          <EmptyMsg text="Nenhuma orientação registrada." />
        )}
        {tab === "formacoes_academicas" && (
          <ListPanel
            empty="Nenhuma formação registrada."
            items={dados.formacoes_academicas.map((f) => (
              <RecordCard
                key={f.id}
                badge={f.nivel}
                title={f.curso || "Curso não informado"}
                meta={[f.instituicao, f.ano_fim && `Conclusão ${f.ano_fim}`]
                  .filter(Boolean)
                  .join(" · ")}
              />
            ))}
          />
        )}
        {tab === "bancas" && (
          <ListPanel
            empty="Nenhuma banca registrada."
            items={dados.bancas.map((b) => (
              <RecordCard
                key={b.id}
                badge={b.tipo}
                title={b.nome_candidato || "Candidato não identificado"}
                meta={[b.ano, b.instituicao].filter(Boolean).join(" · ")}
                body={b.titulo_trabalho || undefined}
              />
            ))}
          />
        )}
        {tab === "producoes_tecnicas" && (
          <ListPanel
            empty="Nenhuma produção técnica registrada."
            items={dados.producoes_tecnicas.map((p) => (
              <RecordCard key={p.id} badge={p.tipo} title={p.titulo} meta={String(p.ano ?? "")} body={p.descricao || undefined} />
            ))}
          />
        )}
        {tab === "premios" && (
          <ListPanel
            empty="Nenhum prêmio registrado."
            items={dados.premios.map((p) => (
              <RecordCard key={p.id} badge={p.tipo} title={p.nome} meta={String(p.ano ?? "")} body={p.descricao || undefined} />
            ))}
          />
        )}
        {tab === "grupos_pesquisa" && (
          <ListPanel
            empty="Nenhum grupo de pesquisa registrado."
            items={dados.grupos_pesquisa.map((g) => (
              <RecordCard
                key={g.id}
                badge={g.papel}
                title={g.nome_grupo}
                meta={[g.codigo_dgp, g.instituicao].filter(Boolean).join(" · ")}
              />
            ))}
          />
        )}
      </div>
    </div>
  );
}

function ResumoTab({
  prof,
  dados,
  resumo,
}: {
  prof: ProfessorCatalog;
  dados: ProfessorDadosPayload;
  resumo: ProfessorResumo | null;
}) {
  const stats = [
    { label: "Projetos", value: prof.total_projetos },
    { label: "Produções", value: prof.total_producoes },
    { label: "Eventos", value: prof.total_eventos },
    { label: "Orientações", value: prof.total_orientacoes },
    { label: "Bancas", value: prof.total_bancas },
    { label: "Financiamentos", value: prof.total_financiamentos },
  ];
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {stats.map((s) => (
          <div
            key={s.label}
            className="glow-card rounded-xl p-4 border border-slate-800 text-center"
          >
            <p className="text-2xl font-bold text-indigo-300">{s.value}</p>
            <p className="text-[10px] text-slate-500 uppercase font-semibold mt-1">
              {s.label}
            </p>
          </div>
        ))}
      </div>
      {resumo && (
        <p className="text-xs text-slate-500">
          {resumo.orientacoes_concluidas} orientações concluídas ·{" "}
          {resumo.orientacoes_em_andamento} em andamento ·{" "}
          {resumo.orientacoes_ultimos_5_anos} nos últimos 5 anos
        </p>
      )}
      {dados.projetos.length === 0 &&
        dados.producoes.length === 0 &&
        dados.orientacoes.length === 0 && (
          <EmptyMsg text="Ainda não há dados importados para este docente." />
        )}
    </div>
  );
}

function ListPanel({
  empty,
  items,
}: {
  empty: string;
  items: React.ReactNode[];
}) {
  if (items.length === 0) return <EmptyMsg text={empty} />;
  return <div className="space-y-3">{items}</div>;
}

function RecordCard({
  badge,
  title,
  meta,
  body,
}: {
  badge: string;
  title: string;
  meta?: string;
  body?: string;
}) {
  return (
    <div className="glow-card rounded-xl p-4 border border-slate-800">
      <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 rounded font-bold uppercase text-slate-400">
        {badge}
      </span>
      <h3 className="text-sm font-bold text-slate-200 mt-2">{title}</h3>
      {meta && <p className="text-[11px] text-slate-500 mt-1">{meta}</p>}
      {body && (
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">{body}</p>
      )}
    </div>
  );
}

function EmptyMsg({ text }: { text: string }) {
  return (
    <p className="text-sm text-slate-500 text-center py-12 border border-dashed border-slate-800 rounded-xl">
      {text}
    </p>
  );
}
