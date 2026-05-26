import fs from "fs";
import path from "path";

const root = path.resolve(import.meta.dirname, "..");
const pagePath = path.join(root, "apps/web/src/app/page.tsx");
const lines = fs.readFileSync(pagePath, "utf8").split(/\r?\n/);

const logicStart = 71;
const logicEnd = 1141;
const validacaoStart = 1163;
const validacaoEnd = 1998;
const statsStart = 2004;
const statsEnd = 2488;
const relStart = 2494;
const relEnd = 2720;
const editStart = 2723;
const editEnd = 3112;

const base = path.join(root, "apps/web/src/components/dashboard");
fs.mkdirSync(path.join(base, "views"), { recursive: true });

const client = '"use client";\n\n';

const constLines = lines.slice(32, 52);
fs.writeFileSync(
  path.join(base, "constants.ts"),
  `${client}import type { EntityTab } from "@/lib/types";\n\n${constLines.join("\n")}\n`
);

const logic = lines.slice(logicStart, logicEnd + 1).join("\n");

const provider = `${client}
import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
  createContext,
  useContext,
  type ReactNode,
} from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import {
  apiFetch,
  getApiBaseUrl,
  parseApiErrorDetail,
  SESSION_EXPIRED_MESSAGE,
} from "@/lib/api";
import {
  cacheKey,
  cachedJson,
  fetchJsonCached,
  invalidateProfessorCaches,
  isCacheValid,
} from "@/lib/api-cache";
import type {
  Professor,
  Projeto,
  Evento,
  Producao,
  Financiamento,
  AlertaLacuna,
  LogAudit,
  MainTab,
  EntityTab,
  Orientacao,
  FormacaoAcademica,
  ProfessorResumo,
  ProducaoTecnica,
  Premio,
  GrupoPesquisa,
} from "@/lib/types";
import { groupOrientacoesByTipo } from "@/lib/orientacao-groups";
import { groupProducoesByTipo } from "@/lib/producao-groups";
import { sortEntityPayload } from "@/lib/sort-entities";
import { VALIDATION_TABS, tabLabel } from "./constants";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type DashboardContextValue = Record<string, any>;

const DashboardContext = createContext<DashboardContextValue | null>(null);

export function useDashboard(): DashboardContextValue {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error("useDashboard must be used within DashboardProvider");
  return ctx;
}

export function DashboardProvider({ children }: { children: ReactNode }) {
${logic}

  const orientacoesPorTipo = useMemo(
    () => groupOrientacoesByTipo(orientacoes),
    [orientacoes]
  );
  const producoesPorTipo = useMemo(
    () => groupProducoesByTipo(producoes),
    [producoes]
  );

  const value: DashboardContextValue = {
    router,
    searchParams,
    user,
    authLoading,
    apiConnected,
    aiModelLabel,
    loading,
    setLoading,
    processingStep,
    setProcessingStep,
    uploadProgress,
    setUploadProgress,
    isProcessing,
    setIsProcessing,
    apiUrl,
    mainTab,
    navigateMainTab,
    linhasPesquisa,
    setLinhasPesquisa,
    statsProfessorId,
    setStatsProfessorId,
    statsLinhaPesquisaId,
    setStatsLinhaPesquisaId,
    statsAnoInicio,
    setStatsAnoInicio,
    statsAnoFim,
    setStatsAnoFim,
    statsData,
    loadingStats,
    showPendingValidationModal,
    setShowPendingValidationModal,
    showArtigosQualisModal,
    setShowArtigosQualisModal,
    showOrientacoesModal,
    setShowOrientacoesModal,
    showNovoDocenteModal,
    setShowNovoDocenteModal,
    reportProfessorId,
    setReportProfessorId,
    reportLinhaPesquisaId,
    setReportLinhaPesquisaId,
    reportAnoInicio,
    setReportAnoInicio,
    reportAnoFim,
    setReportAnoFim,
    reportPrompt,
    setReportPrompt,
    reportText,
    setReportText,
    generatingReport,
    reportLogs,
    reportModelUsed,
    professors,
    setProfessors,
    selectedProfId,
    setSelectedProfId,
    activeTab,
    setActiveTab,
    editingItem,
    setEditingItem,
    projetos,
    setProjetos,
    eventos,
    setEventos,
    producoes,
    setProducoes,
    financiamentos,
    setFinanciamentos,
    orientacoes,
    setOrientacoes,
    formacoes,
    setFormacoes,
    producoesTecnicas,
    setProducoesTecnicas,
    premios,
    setPremios,
    gruposPesquisa,
    setGruposPesquisa,
    resumoAcademico,
    lacunas,
    auditLogs,
    selectedFile,
    setSelectedFile,
    lattesFonte,
    fileInputRef,
    loadProfessors,
    handleReviewPendingItem,
    handleGoToValidationTab,
    reloadProfessorData,
    handleConfirm,
    handleDiscard,
    handleOpenEdit,
    handleSaveEdit,
    handleResolveGap,
    handleGenerateReport,
    copyToClipboard,
    downloadMarkdown,
    handlePrintReport,
    addAuditLog,
    handleFileChange,
    handleLattesFonteChange,
    handleReprocessCurriculo,
    handleUploadAndProcess,
    orientacoesPorTipo,
    producoesPorTipo,
    tabLabel,
    VALIDATION_TABS,
  };

  return (
    <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>
  );
}
`;

fs.writeFileSync(path.join(base, "DashboardProvider.tsx"), provider);

function wrapView(name, sliceStart, sliceEnd, extraImports) {
  const inner = lines.slice(sliceStart, sliceEnd + 1).join("\n");
  const body = inner
    .replace(/\bprofessors\b/g, "d.professors")
    .replace(/\bselectedProfId\b/g, "d.selectedProfId")
    .replace(/\bsetSelectedProfId\b/g, "d.setSelectedProfId")
    .replace(/\bactiveTab\b/g, "d.activeTab")
    .replace(/\bsetActiveTab\b/g, "d.setActiveTab")
    .replace(/\bapiConnected\b/g, "d.apiConnected")
    .replace(/\bloading\b/g, "d.loading")
    .replace(/\bprojetos\b/g, "d.projetos")
    .replace(/\beventos\b/g, "d.eventos")
    .replace(/\bproducoes\b/g, "d.producoes")
    .replace(/\bfinanciamentos\b/g, "d.financiamentos")
    .replace(/\borientacoes\b/g, "d.orientacoes")
    .replace(/\bformacoes\b/g, "d.formacoes")
    .replace(/\bproducoesTecnicas\b/g, "d.producoesTecnicas")
    .replace(/\bpremios\b/g, "d.premios")
    .replace(/\bgruposPesquisa\b/g, "d.gruposPesquisa")
    .replace(/\blacunas\b/g, "d.lacunas")
    .replace(/\bauditLogs\b/g, "d.auditLogs")
    .replace(/\bresumoAcademico\b/g, "d.resumoAcademico")
    .replace(/\borientacoesPorTipo\b/g, "d.orientacoesPorTipo")
    .replace(/\bproducoesPorTipo\b/g, "d.producoesPorTipo")
    .replace(/\bhandleConfirm\b/g, "d.handleConfirm")
    .replace(/\bhandleDiscard\b/g, "d.handleDiscard")
    .replace(/\bhandleOpenEdit\b/g, "d.handleOpenEdit")
    .replace(/\bhandleResolveGap\b/g, "d.handleResolveGap")
    .replace(/\bhandleFileChange\b/g, "d.handleFileChange")
    .replace(/\bhandleLattesFonteChange\b/g, "d.handleLattesFonteChange")
    .replace(/\bhandleReprocessCurriculo\b/g, "d.handleReprocessCurriculo")
    .replace(/\bhandleUploadAndProcess\b/g, "d.handleUploadAndProcess")
    .replace(/\bisProcessing\b/g, "d.isProcessing")
    .replace(/\bprocessingStep\b/g, "d.processingStep")
    .replace(/\buploadProgress\b/g, "d.uploadProgress")
    .replace(/\bselectedFile\b/g, "d.selectedFile")
    .replace(/\bsetSelectedFile\b/g, "d.setSelectedFile")
    .replace(/\blattesFonte\b/g, "d.lattesFonte")
    .replace(/\bfileInputRef\b/g, "d.fileInputRef")
    .replace(/\bsetShowNovoDocenteModal\b/g, "d.setShowNovoDocenteModal")
    .replace(/\bstatsProfessorId\b/g, "d.statsProfessorId")
    .replace(/\bsetStatsProfessorId\b/g, "d.setStatsProfessorId")
    .replace(/\bstatsLinhaPesquisaId\b/g, "d.statsLinhaPesquisaId")
    .replace(/\bsetStatsLinhaPesquisaId\b/g, "d.setStatsLinhaPesquisaId")
    .replace(/\bstatsAnoInicio\b/g, "d.statsAnoInicio")
    .replace(/\bsetStatsAnoInicio\b/g, "d.setStatsAnoInicio")
    .replace(/\bstatsAnoFim\b/g, "d.statsAnoFim")
    .replace(/\bsetStatsAnoFim\b/g, "d.setStatsAnoFim")
    .replace(/\bstatsData\b/g, "d.statsData")
    .replace(/\bloadingStats\b/g, "d.loadingStats")
    .replace(/\bsetShowPendingValidationModal\b/g, "d.setShowPendingValidationModal")
    .replace(/\bsetShowArtigosQualisModal\b/g, "d.setShowArtigosQualisModal")
    .replace(/\bsetShowOrientacoesModal\b/g, "d.setShowOrientacoesModal")
    .replace(/\blinhasPesquisa\b/g, "d.linhasPesquisa")
    .replace(/\breportProfessorId\b/g, "d.reportProfessorId")
    .replace(/\bsetReportProfessorId\b/g, "d.setReportProfessorId")
    .replace(/\breportLinhaPesquisaId\b/g, "d.reportLinhaPesquisaId")
    .replace(/\bsetReportLinhaPesquisaId\b/g, "d.setReportLinhaPesquisaId")
    .replace(/\breportAnoInicio\b/g, "d.reportAnoInicio")
    .replace(/\bsetReportAnoInicio\b/g, "d.setReportAnoInicio")
    .replace(/\breportAnoFim\b/g, "d.reportAnoFim")
    .replace(/\bsetReportAnoFim\b/g, "d.setReportAnoFim")
    .replace(/\breportPrompt\b/g, "d.reportPrompt")
    .replace(/\bsetReportPrompt\b/g, "d.setReportPrompt")
    .replace(/\breportText\b/g, "d.reportText")
    .replace(/\bgeneratingReport\b/g, "d.generatingReport")
    .replace(/\breportLogs\b/g, "d.reportLogs")
    .replace(/\breportModelUsed\b/g, "d.reportModelUsed")
    .replace(/\bhandleGenerateReport\b/g, "d.handleGenerateReport")
    .replace(/\bcopyToClipboard\b/g, "d.copyToClipboard")
    .replace(/\bdownloadMarkdown\b/g, "d.downloadMarkdown")
    .replace(/\bhandlePrintReport\b/g, "d.handlePrintReport")
    .replace(/\baiModelLabel\b/g, "d.aiModelLabel")
    .replace(/\beditingItem\b/g, "d.editingItem")
    .replace(/\bsetEditingItem\b/g, "d.setEditingItem")
    .replace(/\bhandleSaveEdit\b/g, "d.handleSaveEdit")
    .replace(/\btabLabel\b/g, "d.tabLabel");

  return `${client}${extraImports}
import { useDashboard } from "../DashboardProvider";

export function ${name}() {
  const d = useDashboard();
  return (
${body}
  );
}
`;
}

fs.writeFileSync(
  path.join(base, "views/ValidacaoView.tsx"),
  wrapView(
    "ValidacaoView",
    validacaoStart,
    validacaoEnd,
    `import React from "react";
import {
  FileText, Upload, Check, Edit2, Trash2, AlertTriangle,
  HelpCircle, CheckCircle, RefreshCw, BarChart2, Plus,
  BookOpen, Calendar, DollarSign, Eye, EyeOff, Clock, ArrowRight, UserPlus, Info,
  Users, GraduationCap, Wrench, Trophy, Network
} from "lucide-react";
import { ResumoAcademicoCard } from "@/components/academic/ResumoAcademicoCard";
import {
  ActionPanel, ConfidenceBadge, EmptyState, OriginalFragment,
} from "@/components/ui/validation-ui";
import type { EntityTab } from "@/lib/types";`
  )
);

fs.writeFileSync(
  path.join(base, "views/EstatisticasView.tsx"),
  wrapView(
    "EstatisticasView",
    statsStart,
    statsEnd,
    `import React from "react";
import { BarChart2, AlertTriangle, BookOpen, Calendar, DollarSign, GraduationCap, Users } from "lucide-react";`
  )
);

fs.writeFileSync(
  path.join(base, "views/RelatoriosView.tsx"),
  wrapView(
    "RelatoriosView",
    relStart,
    relEnd,
    `import React from "react";
import { BarChart2, Award, RefreshCw } from "lucide-react";
import { SimpleMarkdownRenderer } from "@/components/ui/validation-ui";`
  )
);

fs.writeFileSync(
  path.join(base, "ValidationEditModal.tsx"),
  wrapView(
    "ValidationEditModal",
    editStart,
    editEnd,
    `import React from "react";
import { Check, Edit2 } from "lucide-react";
import type { EntityTab } from "@/lib/types";`
  )
);

console.log("Split complete ->", base);
