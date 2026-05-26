"use client";

import { AppShellHeader } from "@/components/layout/AppShellHeader";
import { AppShellContainer } from "@/components/layout/AppShellContainer";
import { NovoDocenteModal } from "@/components/admin/NovoDocenteModal";
import { PendingValidationModal } from "@/components/validation/PendingValidationModal";
import { ArtigosQualisModal } from "@/components/analytics/ArtigosQualisModal";
import { OrientacoesModal } from "@/components/analytics/OrientacoesModal";
import { useDashboard } from "./DashboardProvider";
import type { Professor } from "@/lib/types";
import { ValidacaoView } from "./views/ValidacaoView";
import { EstatisticasView } from "./views/EstatisticasView";
import { RelatoriosView } from "./views/RelatoriosView";
import { ValidationEditModal } from "./ValidationEditModal";

export function DashboardShell() {
  const d = useDashboard();

  if (d.authLoading || !d.user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400 text-sm">
        Carregando sessão...
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <AppShellHeader
        section="operacao"
        operacaoView={d.mainTab}
        onOperacaoViewChange={d.navigateMainTab}
        apiConnected={d.apiConnected}
      />

      <AppShellContainer className="flex-1 flex flex-col">
        {d.mainTab === "validacao" && <ValidacaoView />}
        {d.mainTab === "estatisticas" && <EstatisticasView />}
        {d.mainTab === "relatorios" && <RelatoriosView />}
        <ValidationEditModal />
      </AppShellContainer>

      <NovoDocenteModal
        open={d.showNovoDocenteModal}
        onClose={() => d.setShowNovoDocenteModal(false)}
        linhasPesquisa={d.linhasPesquisa}
        onSuccess={(professorId, nome) => {
          d.loadProfessors(professorId, true);
          d.addAuditLog("cadastro", `Novo docente: ${nome} (${professorId}).`);
        }}
      />

      <PendingValidationModal
        open={d.showPendingValidationModal}
        onClose={() => d.setShowPendingValidationModal(false)}
        professors={d.professors}
        linhasPesquisa={d.linhasPesquisa}
        statsProfessorId={d.statsProfessorId}
        statsLinhaPesquisaId={d.statsLinhaPesquisaId}
        breakdown={d.statsData?.validacao_pendentes}
        onReview={d.handleReviewPendingItem}
        onGoToValidation={d.handleGoToValidationTab}
      />

      <ArtigosQualisModal
        open={d.showArtigosQualisModal}
        onClose={() => d.setShowArtigosQualisModal(false)}
        statsProfessorId={d.statsProfessorId}
        statsLinhaPesquisaId={d.statsLinhaPesquisaId}
        statsAnoInicio={d.statsAnoInicio}
        statsAnoFim={d.statsAnoFim}
        filterSummary={[
          d.statsProfessorId === "todos"
            ? "Todos os docentes"
            : d.professors.find((p: Professor) => p.id === d.statsProfessorId)?.nome_completo ?? "Docente",
          d.statsLinhaPesquisaId === "todas"
            ? "Todas as linhas"
            : d.linhasPesquisa.find((l: { id: string; nome: string }) => l.id === d.statsLinhaPesquisaId)?.nome ?? "Linha",
          `${d.statsAnoInicio}—${d.statsAnoFim}`,
        ].join(" · ")}
        previewPorQualis={d.statsData?.producoes_por_qualis}
      />

      <OrientacoesModal
        open={d.showOrientacoesModal}
        onClose={() => d.setShowOrientacoesModal(false)}
        statsProfessorId={d.statsProfessorId}
        statsLinhaPesquisaId={d.statsLinhaPesquisaId}
        statsAnoInicio={d.statsAnoInicio}
        statsAnoFim={d.statsAnoFim}
        filterSummary={[
          d.statsProfessorId === "todos"
            ? "Todos os docentes"
            : d.professors.find((p: Professor) => p.id === d.statsProfessorId)?.nome_completo ?? "Docente",
          d.statsLinhaPesquisaId === "todas"
            ? "Todas as linhas"
            : d.linhasPesquisa.find((l: { id: string; nome: string }) => l.id === d.statsLinhaPesquisaId)?.nome ?? "Linha",
          `${d.statsAnoInicio}—${d.statsAnoFim}`,
        ].join(" · ")}
      />
    </div>
  );
}
