"use client";


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
import { printReportInPage } from "@/lib/report-print";
import { VALIDATION_TABS, tabLabel } from "./constants";

export interface DashboardContextValue {
  professors: Professor[];
  linhasPesquisa: { id: string; nome: string }[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

const DashboardContext = createContext<DashboardContextValue | null>(null);

export function useDashboard(): DashboardContextValue {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error("useDashboard must be used within DashboardProvider");
  return ctx;
}

export function DashboardProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  // Connection state
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [aiModelLabel, setAiModelLabel] = useState<string>("OpenCode Go");
  const [loading, setLoading] = useState<boolean>(false);
  const [processingStep, setProcessingStep] = useState<string>("");
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const apiUrl = getApiBaseUrl();

  const mainTab: MainTab = (() => {
    const v = searchParams.get("view");
    if (v === "estatisticas" || v === "relatorios" || v === "validacao") return v;
    return "validacao";
  })();

  const navigateMainTab = (tab: MainTab) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("view", tab);
    const qs = params.toString();
    router.replace(qs ? `/?${qs}` : `/?view=${tab}`, { scroll: false });
  };

  // Research Lines state
  const [linhasPesquisa, setLinhasPesquisa] = useState<any[]>([]);

  // Statistics filters & data
  const [statsProfessorId, setStatsProfessorId] = useState<string>("todos");
  const [statsLinhaPesquisaId, setStatsLinhaPesquisaId] = useState<string>("todas");
  const [statsAnoInicio, setStatsAnoInicio] = useState<string>("2020");
  const [statsAnoFim, setStatsAnoFim] = useState<string>("2026");
  const [statsData, setStatsData] = useState<any>(null);
  const [loadingStats, setLoadingStats] = useState<boolean>(false);
  const [showPendingValidationModal, setShowPendingValidationModal] = useState(false);
  const [showArtigosQualisModal, setShowArtigosQualisModal] = useState(false);
  const [showOrientacoesModal, setShowOrientacoesModal] = useState(false);
  const [showNovoDocenteModal, setShowNovoDocenteModal] = useState(false);

  // AI Report Generator filters, prompt & text
  const [reportProfessorId, setReportProfessorId] = useState<string>("todos");
  const [reportLinhaPesquisaId, setReportLinhaPesquisaId] = useState<string>("todas");
  const [reportAnoInicio, setReportAnoInicio] = useState<string>("2020");
  const [reportAnoFim, setReportAnoFim] = useState<string>("2026");
  const [reportPrompt, setReportPrompt] = useState<string>("");
  const [reportText, setReportText] = useState<string>("");
  const [generatingReport, setGeneratingReport] = useState<boolean>(false);
  const [reportLogs, setReportLogs] = useState<string[]>([]);
  const [reportModelUsed, setReportModelUsed] = useState<string>("");

  // App core state
  const [professors, setProfessors] = useState<Professor[]>([]);
  const [selectedProfId, setSelectedProfId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<EntityTab>("projetos");

  const [editingItem, setEditingItem] = useState<{ type: string; item: any } | null>(null);
  const [projetos, setProjetos] = useState<Projeto[]>([]);
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [producoes, setProducoes] = useState<Producao[]>([]);
  const [financiamentos, setFinanciamentos] = useState<Financiamento[]>([]);
  const [orientacoes, setOrientacoes] = useState<Orientacao[]>([]);
  const [formacoes, setFormacoes] = useState<FormacaoAcademica[]>([]);
  const [producoesTecnicas, setProducoesTecnicas] = useState<ProducaoTecnica[]>([]);
  const [premios, setPremios] = useState<Premio[]>([]);
  const [gruposPesquisa, setGruposPesquisa] = useState<GrupoPesquisa[]>([]);
  const [resumoAcademico, setResumoAcademico] = useState<ProfessorResumo | null>(null);
  const [lacunas, setLacunas] = useState<AlertaLacuna[]>([]);
  const [auditLogs, setAuditLogs] = useState<LogAudit[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [lattesFonte, setLattesFonte] = useState<"html" | "xml">("html");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    const base = getApiBaseUrl().replace(/\/$/, "");
    const checkUrl = `${base}/status`;

    fetch(checkUrl)
      .then(res => {
        if (!res.ok) throw new Error(`API status ${res.status}`);
        return res.json();
      })
      .then(async (status) => {
        if (status?.ai_provider && status?.ai_model) {
          setAiModelLabel(`${status.ai_provider}/${status.ai_model}`);
        } else if (status?.ai_provider === "not_configured") {
          setAiModelLabel("modo simulado (sem chave de IA)");
        }

        if (!user) {
          setApiConnected(false);
          return;
        }
        setApiConnected(true);
        try {
          const data = await fetchJsonCached<{ id: string; nome: string }[]>(
            "/linhas-pesquisa/",
            { cacheKey: cacheKey("meta", "linhas-pesquisa") }
          );
          if (data && data.length > 0) {
            setLinhasPesquisa(data);
          }
        } catch (err) {
          console.log("API online, falha ao carregar linhas:", err);
        }
      })
      .catch(() => {
        setApiConnected(false);
        console.log("Servidor FastAPI offline, utilizando dados simulados premium.");
        setLinhasPesquisa([
          { id: "linha-1-mock", nome: "Tecnologias, Audiovisual e Processos Regionais de Comunicação" },
          { id: "linha-2-mock", nome: "Processos Comunicacionais, Cidadania e Identidades" }
        ]);
      });
  }, [user]);

  const loadProfessors = useCallback(async (preferId?: string, force = false) => {
    if (!apiConnected) return;

    try {
      const data: any[] = await cachedJson(
        cacheKey("professores", "list"),
        async () => {
          const res = await apiFetch("/professores/");
          if (!res.ok) throw new Error("Erro ao carregar docentes");
          return res.json();
        },
        { force }
      );
      const mapped = data.map((p) => ({
        id: p.id,
        nome_completo: p.nome_completo,
        email: p.email,
        id_lattes: p.id_lattes,
        linha:
          p.linha_pesquisa?.nome ??
          linhasPesquisa.find((l) => l.id === p.linha_pesquisa_id)?.nome ??
          "Não especificada",
        tipo: p.tipo_docente
          ? p.tipo_docente.charAt(0).toUpperCase() + p.tipo_docente.slice(1)
          : "Permanente",
        status: (p.status ? "validado" : "pendente") as "validado" | "pendente",
      }));

      const seen = new Set<string>();
      const unique = mapped.filter((p) => {
        const key = (p.email || p.id_lattes || p.nome_completo || p.id).toLowerCase();
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });

      if (unique.length > 0) {
        setProfessors(unique);
        if (preferId && unique.some((p) => p.id === preferId)) {
          setSelectedProfId(preferId);
        } else if (!unique.some((p) => p.id === selectedProfId)) {
          setSelectedProfId(unique[0].id);
        }
      }
    } catch (err) {
      console.error("Falha ao buscar docentes da API:", err);
    }
  }, [apiConnected, linhasPesquisa]);

  useEffect(() => {
    loadProfessors();
  }, [loadProfessors]);

  useEffect(() => {
    const pid = searchParams.get("professor_id");
    if (pid) setSelectedProfId(pid);
  }, [searchParams]);

  const handleReviewPendingItem = (professorId: string, tab: EntityTab) => {
    setShowPendingValidationModal(false);
    const params = new URLSearchParams(searchParams.toString());
    params.set("view", "validacao");
    params.set("professor_id", professorId);
    router.push(`/?${params.toString()}`, { scroll: false });
    setSelectedProfId(professorId);
    setActiveTab(tab);
  };

  const handleGoToValidationTab = () => {
    setShowPendingValidationModal(false);
    const params = new URLSearchParams(searchParams.toString());
    params.set("view", "validacao");
    if (statsProfessorId !== "todos") {
      params.set("professor_id", statsProfessorId);
      setSelectedProfId(statsProfessorId);
    }
    router.push(`/?${params.toString()}`, { scroll: false });
  };

  const reloadProfessorData = useCallback(
    async (profId: string, force = false) => {
      if (!apiConnected) return;
      const pendentesKey = cacheKey("validacao", "pendentes", profId);
      const resumoKey = cacheKey("professor", "resumo", profId);
      if (force || !isCacheValid(pendentesKey) || !isCacheValid(resumoKey)) {
        setLoading(true);
      }
      try {
        const [data, resumo] = await Promise.all([
          cachedJson(
            cacheKey("validacao", "pendentes", profId),
            async () => {
              const res = await apiFetch(`/validacao/pendentes?professor_id=${profId}`);
              if (!res.ok) throw new Error("Erro ao carregar dados do docente");
              return sortEntityPayload(await res.json());
            },
            { force }
          ),
          cachedJson(
            cacheKey("professor", "resumo", profId),
            async () => {
              const res = await apiFetch(`/professores/${profId}/resumo-academico`);
              return res.ok ? res.json() : null;
            },
            { force }
          ),
        ]);
        setProjetos(data.projetos || []);
        setEventos(data.eventos || []);
        setProducoes(data.producoes || []);
        setFinanciamentos(data.financiamentos || []);
        setOrientacoes(data.orientacoes || []);
        setFormacoes(data.formacoes_academicas || []);
        setProducoesTecnicas(data.producoes_tecnicas || []);
        setPremios(data.premios || []);
        setGruposPesquisa(data.grupos_pesquisa || []);
        setLacunas(data.lacunas || []);
        setResumoAcademico(resumo);
      } catch (err) {
        console.error("Falha ao buscar dados do docente:", err);
      } finally {
        setLoading(false);
      }
    },
    [apiConnected]
  );

  // Load teacher specific data on select (API or Mock fallback)
  useEffect(() => {
    if (!selectedProfId) return;

    if (apiConnected) {
      reloadProfessorData(selectedProfId);
      return;
    }

    // --- FALLBACK MOCK DATA ---
    const prof = professors.find(p => p.id === selectedProfId);
    if (!prof) return;

    if (selectedProfId === "1") {
      setProjetos([
        {
          id: "p1",
          titulo: "Pesquisa em Comunicação Digital, Desinformação e Algoritmos de Recomendação",
          tipo: "pesquisa",
          situacao: "Em andamento",
          ano_inicio: 2024,
          ano_fim: null,
          descricao: "Análise da recepção e circulação de informações desinformativas no Nordeste brasileiro.",
          papel_docente: "Coordenador",
          instituicoes: "UFMA, PPGCOM, CNPq",
          financiamento_mencionado: true,
          agencia_fomento: "FAPEMA / CNPq",
          confianca_ia: "alta",
          trecho_original: "Projeto de pesquisa em andamento (2024 - Atual) intitulado 'Comunicação Digital e Algoritmos', financiado sob edital FAPEMA.",
          status_validacao: "pendente"
        },
        {
          id: "p2",
          titulo: "Estudos de Impacto Regulatório em Plataformas de Mídias Sociais",
          tipo: "desenvolvimento",
          situacao: "Concluído",
          ano_inicio: 2022,
          ano_fim: 2024,
          descricao: "Pesquisa aplicada sobre propostas de regulação de plataformas no congresso nacional.",
          papel_docente: "Participante",
          instituicoes: "UFMA, UnB",
          financiamento_mencionado: false,
          agencia_fomento: null,
          confianca_ia: "media",
          trecho_original: "Participação no desenvolvimento de indicadores regulatórios no projeto Mídias Sociais (2022-2024).",
          status_validacao: "pendente"
        }
      ]);
      setEventos([
        {
          id: "e1",
          nome_evento: "XXXIII Encontro Anual da Compós",
          ano: 2025,
          cidade: "São Luís",
          pais: "Brasil",
          tipo_participacao: "Apresentação oral",
          titulo_trabalho: "A recepção de desinformação algorítmica no Whatsapp e Telegram",
          financiamento_mencionado: true,
          fonte_financiamento: "Bolsa FAPEMA",
          confianca_ia: "alta",
          trecho_original: "Apresentou o trabalho 'A recepção de desinformação algorítmica' na Compós 2025, com auxílio mobilidade FAPEMA.",
          status_validacao: "pendente"
        }
      ]);
      setProducoes([
        {
          id: "pr1",
          tipo: "artigo",
          titulo: "As metamorfoses do jornalismo digital: Circulação e Algoritmos no Nordeste",
          ano: 2024,
          veiculo: "Revista Brasileira de Ciências da Comunicação",
          doi: "10.1234/rbcc.2024.v47",
          issn: "1809-5844",
          qualis: "A2",
          scholar_h5_index: 18,
          scholar_h5_median: 22,
          scholar_metrics_year: 2024,
          confianca_ia: "alta",
          trecho_original: "REINO, L. As metamorfoses do jornalismo digital. Revista Brasileira de Ciências da Comunicação, v. 47, 2024.",
          status_validacao: "pendente"
        },
        {
          id: "pr2",
          tipo: "livro",
          titulo: "Comunicação, Algoritmos e Cultura Digital: Olhares do PPGCOM",
          ano: 2023,
          veiculo: "Editora Universitária Edufma",
          doi: null,
          issn: "978-85-7890",
          confianca_ia: "media",
          trecho_original: "REINO, L. (Org). Comunicação, Algoritmos e Cultura Digital. São Luís: Edufma, 2023. 240p.",
          status_validacao: "pendente"
        }
      ]);
      setFinanciamentos([
        {
          id: "f1",
          tipo: "pesquisa",
          fonte: "FAPEMA",
          agencia: "Fundação de Amparo à Pesquisa do Maranhão",
          edital: "Edital Universal FAPEMA 2023",
          numero_processo: "U-12345/23",
          valor: "R$ 45.000,00",
          ano: 2024,
          confianca: "alta",
          trecho_original: "Financiado pela FAPEMA sob processo U-12345/23 valor de R$ 45.000,00 no âmbito do edital Universal.",
          status_validacao: "pendente"
        }
      ]);
      setLacunas([
        {
          id: "l1",
          tipo_lacuna: "Vigência incompleta",
          descricao: "O projeto 'Pesquisa em Comunicação Digital' está marcado como em andamento, mas não especifica data final de vigência ou data de relatórios parciais.",
          gravidade: "media",
          acao_recomendada: "Entrar em contato com o docente para ajustar a vigência final.",
          resolvido: false
        },
        {
          id: "l2",
          tipo_lacuna: "Falta de valor exato",
          descricao: "A bolsa mobilidade mencionada no Evento Compós 2025 não possui o valor financeiro associado no Currículo Lattes.",
          gravidade: "baixa",
          acao_recomendada: "Verificar extrato ou portaria de bolsas e atualizar manualmente.",
          resolvido: false
        }
      ]);
    } else if (selectedProfId === "3") {
      setProjetos([
        {
          id: "p3",
          titulo: "Consumos de Mídia e Representações da Cidadania",
          tipo: "pesquisa",
          situacao: "Concluído",
          ano_inicio: 2020,
          ano_fim: 2023,
          descricao: "Estudo comparativo de recepção de novelas em múltiplas telas.",
          papel_docente: "Coordenador",
          instituicoes: "UFMA",
          financiamento_mencionado: false,
          agencia_fomento: null,
          confianca_ia: "alta",
          trecho_original: "Projeto concluído: Consumos de Mídia e Representações da Cidadania (2020-2023).",
          status_validacao: "confirmado"
        }
      ]);
      setEventos([]);
      setProducoes([
        {
          id: "pr3",
          tipo: "artigo",
          titulo: "Novas Configurações do Consumo Audiovisual no Nordeste",
          ano: 2023,
          veiculo: "Revista Comunicação & Sociedade",
          doi: "10.1590/cs.2023",
          issn: "1983-3652",
          confianca_ia: "alta",
          trecho_original: "ALBERTO, C. Novas Configurações do Consumo Audiovisual. Revista Comunicação & Sociedade, 2023.",
          status_validacao: "confirmado"
        }
      ]);
      setFinanciamentos([]);
      setLacunas([]);
    } else {
      setProjetos([]);
      setEventos([]);
      setProducoes([]);
      setFinanciamentos([]);
      setOrientacoes([]);
      setFormacoes([]);
      setProducoesTecnicas([]);
      setPremios([]);
      setGruposPesquisa([]);
      setLacunas([]);
    }
  }, [selectedProfId, apiConnected, reloadProfessorData, professors]);

  // Handle human-in-the-loop action: Confirmar
  const handleConfirm = (type: string, id: string) => {
    let itemTitle = "";
    if (type === "projetos") {
      setProjetos(prev => prev.map(p => {
        if (p.id === id) {
          itemTitle = p.titulo;
          return { ...p, status_validacao: "confirmado" };
        }
        return p;
      }));
    } else if (type === "eventos") {
      setEventos(prev => prev.map(e => {
        if (e.id === id) {
          itemTitle = e.nome_evento;
          return { ...e, status_validacao: "confirmado" };
        }
        return e;
      }));
    } else if (type === "producoes") {
      setProducoes(prev => prev.map(p => {
        if (p.id === id) {
          itemTitle = p.titulo;
          return { ...p, status_validacao: "confirmado" };
        }
        return p;
      }));
    } else if (type === "financiamentos") {
      setFinanciamentos(prev => prev.map(f => {
        if (f.id === id) {
          itemTitle = `${f.fonte} (${f.valor})`;
          return { ...f, status_validacao: "confirmado" };
        }
        return f;
      }));
    } else if (type === "orientacoes") {
      setOrientacoes(prev => prev.map(o => {
        if (o.id === id) {
          itemTitle = o.nome_orientando || o.titulo_trabalho || "orientação";
          return { ...o, status_validacao: "confirmado" };
        }
        return o;
      }));
    } else if (type === "formacoes_academicas") {
      setFormacoes(prev => prev.map(f => {
        if (f.id === id) {
          itemTitle = `${f.nivel} — ${f.instituicao || ""}`;
          return { ...f, status_validacao: "confirmado" };
        }
        return f;
      }));
    } else if (type === "producoes_tecnicas") {
      setProducoesTecnicas(prev => prev.map(p => {
        if (p.id === id) {
          itemTitle = p.titulo;
          return { ...p, status_validacao: "confirmado" };
        }
        return p;
      }));
    } else if (type === "premios") {
      setPremios(prev => prev.map(p => {
        if (p.id === id) {
          itemTitle = p.nome;
          return { ...p, status_validacao: "confirmado" };
        }
        return p;
      }));
    } else if (type === "grupos_pesquisa") {
      setGruposPesquisa(prev => prev.map(g => {
        if (g.id === id) {
          itemTitle = g.nome_grupo;
          return { ...g, status_validacao: "confirmado" };
        }
        return g;
      }));
    }

    if (apiConnected) {
      apiFetch(`/validacao/${type}/${id}/confirmar`, { method: "POST" })
        .then(res => {
          if (!res.ok) throw new Error("Falha ao salvar confirmação");
          addAuditLog("confirmar", `[Real DB] Confirmou ${type.slice(0, -2)}: "${itemTitle.slice(0, 45)}..."`);
        })
        .catch(err => {
          console.error("Erro ao salvar confirmação:", err);
        });
    } else {
      addAuditLog("confirmar", `Confirmou ${type.slice(0, -2)}: "${itemTitle.slice(0, 45)}..."`);
    }
    checkProfUpdate(selectedProfId);
  };

  // Handle human-in-the-loop action: Descartar
  const handleDiscard = (type: string, id: string) => {
    let itemTitle = "";
    if (type === "projetos") {
      setProjetos(prev => prev.map(p => {
        if (p.id === id) {
          itemTitle = p.titulo;
          return { ...p, status_validacao: "descartado" };
        }
        return p;
      }));
    } else if (type === "eventos") {
      setEventos(prev => prev.map(e => {
        if (e.id === id) {
          itemTitle = e.nome_evento;
          return { ...e, status_validacao: "descartado" };
        }
        return e;
      }));
    } else if (type === "producoes") {
      setProducoes(prev => prev.map(p => {
        if (p.id === id) {
          itemTitle = p.titulo;
          return { ...p, status_validacao: "descartado" };
        }
        return p;
      }));
    } else if (type === "financiamentos") {
      setFinanciamentos(prev => prev.map(f => {
        if (f.id === id) {
          itemTitle = `${f.fonte} (${f.valor})`;
          return { ...f, status_validacao: "descartado" };
        }
        return f;
      }));
    } else if (type === "orientacoes") {
      setOrientacoes(prev => prev.map(o => {
        if (o.id === id) {
          itemTitle = o.nome_orientando || "orientação";
          return { ...o, status_validacao: "descartado" };
        }
        return o;
      }));
    } else if (type === "formacoes_academicas") {
      setFormacoes(prev => prev.map(f => {
        if (f.id === id) {
          itemTitle = f.nivel;
          return { ...f, status_validacao: "descartado" };
        }
        return f;
      }));
    } else if (type === "producoes_tecnicas") {
      setProducoesTecnicas(prev => prev.map(p => {
        if (p.id === id) {
          itemTitle = p.titulo;
          return { ...p, status_validacao: "descartado" };
        }
        return p;
      }));
    } else if (type === "premios") {
      setPremios(prev => prev.map(p => {
        if (p.id === id) {
          itemTitle = p.nome;
          return { ...p, status_validacao: "descartado" };
        }
        return p;
      }));
    } else if (type === "grupos_pesquisa") {
      setGruposPesquisa(prev => prev.map(g => {
        if (g.id === id) {
          itemTitle = g.nome_grupo;
          return { ...g, status_validacao: "descartado" };
        }
        return g;
      }));
    }

    if (apiConnected) {
      apiFetch(`/validacao/${type}/${id}/descartar`, { method: "POST" })
        .then(res => {
          if (!res.ok) throw new Error("Falha ao descartar registro");
          addAuditLog("descartar", `[Real DB] Descartou ${type.slice(0, -2)}: "${itemTitle.slice(0, 45)}..."`);
        })
        .catch(err => {
          console.error("Erro ao descartar registro:", err);
        });
    } else {
      addAuditLog("descartar", `Descartou ${type.slice(0, -2)}: "${itemTitle.slice(0, 45)}..."`);
    }
    checkProfUpdate(selectedProfId);
  };

  // Open Edit Dialog
  const handleOpenEdit = (type: string, item: any) => {
    setEditingItem({ type, item: { ...item } });
  };

  // Save changes from Edit Dialog
  const handleSaveEdit = () => {
    if (!editingItem) return;
    const { type, item } = editingItem;

    if (apiConnected) {
      const { id: _, created_at: __, updated_at: ___, ...updates } = item;
      apiFetch(`/validacao/${type}/${item.id}/editar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates)
      })
        .then(async (res) => {
          if (!res.ok) {
            const errBody = await res.json().catch(() => ({}));
            throw new Error(parseApiErrorDetail(errBody.detail, "Falha ao salvar edição"));
          }
          return res.json();
        })
        .then(() => {
          if (type === "projetos") {
            setProjetos(prev => prev.map(p => p.id === item.id ? { ...item, status_validacao: "editado" } : p));
          } else if (type === "eventos") {
            setEventos(prev => prev.map(e => e.id === item.id ? { ...item, status_validacao: "editado" } : e));
          } else if (type === "producoes") {
            setProducoes(prev => prev.map(p => p.id === item.id ? { ...item, status_validacao: "editado" } : p));
          } else if (type === "financiamentos") {
            setFinanciamentos(prev => prev.map(f => f.id === item.id ? { ...item, status_validacao: "editado" } : f));
          } else if (type === "orientacoes") {
            setOrientacoes(prev => prev.map(o => o.id === item.id ? { ...item, status_validacao: "editado" } : o));
          } else if (type === "formacoes_academicas") {
            setFormacoes(prev => prev.map(f => f.id === item.id ? { ...item, status_validacao: "editado" } : f));
          } else if (type === "producoes_tecnicas") {
            setProducoesTecnicas(prev => prev.map(p => p.id === item.id ? { ...item, status_validacao: "editado" } : p));
          } else if (type === "premios") {
            setPremios(prev => prev.map(p => p.id === item.id ? { ...item, status_validacao: "editado" } : p));
          } else if (type === "grupos_pesquisa") {
            setGruposPesquisa(prev => prev.map(g => g.id === item.id ? { ...item, status_validacao: "editado" } : g));
          }
          const label = item.titulo || item.nome || item.nome_grupo || item.nome_evento || item.fonte || item.nome_orientando || item.nivel || "registro";
          addAuditLog("editar", `[Real DB] Editou e Validou ${type}: "${String(label).slice(0, 45)}..."`);
          setEditingItem(null);
        })
        .catch(err => {
          console.error("Erro ao salvar edição:", err);
          alert(err instanceof Error ? err.message : "Erro ao salvar edição no servidor.");
        });
      return;
    }

    if (type === "projetos") {
      setProjetos(prev => prev.map(p => p.id === item.id ? { ...item, status_validacao: "editado" } : p));
    } else if (type === "eventos") {
      setEventos(prev => prev.map(e => e.id === item.id ? { ...item, status_validacao: "editado" } : e));
    } else if (type === "producoes") {
      setProducoes(prev => prev.map(p => p.id === item.id ? { ...item, status_validacao: "editado" } : p));
    } else if (type === "financiamentos") {
      setFinanciamentos(prev => prev.map(f => f.id === item.id ? { ...item, status_validacao: "editado" } : f));
    } else if (type === "orientacoes") {
      setOrientacoes(prev => prev.map(o => o.id === item.id ? { ...item, status_validacao: "editado" } : o));
    } else if (type === "formacoes_academicas") {
      setFormacoes(prev => prev.map(f => f.id === item.id ? { ...item, status_validacao: "editado" } : f));
    } else if (type === "producoes_tecnicas") {
      setProducoesTecnicas(prev => prev.map(p => p.id === item.id ? { ...item, status_validacao: "editado" } : p));
    } else if (type === "premios") {
      setPremios(prev => prev.map(p => p.id === item.id ? { ...item, status_validacao: "editado" } : p));
    } else if (type === "grupos_pesquisa") {
      setGruposPesquisa(prev => prev.map(g => g.id === item.id ? { ...item, status_validacao: "editado" } : g));
    }

    addAuditLog("editar", `Editou e Validou ${type}: "${String(item.titulo || item.nome || item.nome_grupo || item.nome_evento || item.fonte || "").slice(0, 45)}..."`);
    setEditingItem(null);
    checkProfUpdate(selectedProfId);
  };

  // Check if professor validation status should update
  const checkProfUpdate = (profId: string) => {
    setProfessors(prev => prev.map(p => {
      if (p.id === profId) {
        return { ...p, status: "validado" };
      }
      return p;
    }));
  };

  // Resolve specific gap
  const handleResolveGap = (gapId: string) => {
    if (apiConnected) {
      apiFetch(`/validacao/lacunas/${gapId}/resolver`, { method: "POST" })
        .then(res => {
          if (!res.ok) throw new Error("Falha ao resolver lacuna");
          setLacunas(prev => prev.map(l => l.id === gapId ? { ...l, resolvido: true } : l));
          const gap = lacunas.find(l => l.id === gapId);
          if (gap) {
            addAuditLog("resolvido", `[Real DB] Marcou lacuna como resolvida: "${gap.tipo_lacuna}"`);
          }
        })
        .catch(err => {
          console.error("Erro ao resolver lacuna:", err);
          alert("Erro ao resolver lacuna no servidor.");
        });
      return;
    }

    setLacunas(prev => prev.map(l => l.id === gapId ? { ...l, resolvido: true } : l));
    const gap = lacunas.find(l => l.id === gapId);
    if (gap) {
      addAuditLog("resolvido", `Marcou lacuna resolvido: "${gap.tipo_lacuna}"`);
    }
  };

  // Generate simulated stats for local mock flow
  const generateSimulatedStats = () => {
    return {
      total_producoes: 48,
      total_projetos: 8,
      total_eventos: 15,
      fomento_total: { solicitado: 120000.0, aprovado: 85000.0, executado: 45000.0 },
      producoes_por_tipo: { "artigo": 24, "livro": 6, "capitulo": 12, "outra": 6 },
      producoes_por_ano: { "2020": 5, "2021": 8, "2022": 10, "2023": 12, "2024": 8, "2025": 5 },
      projetos_por_situacao: { "Em andamento": 3, "Concluído": 5 },
      fomento_por_agencia: { "CNPQ": 45000.0, "CAPES": 25000.0, "FAPEMA": 15000.0 },
      lacunas: {
        total: 22,
        resolvidas: 14,
        pendentes: 8,
        por_gravidade: { "alta": 2, "media": 4, "baixa": 2 }
      },
      total_orientacoes: 34,
      orientacoes_concluidas: 28,
      orientacoes_em_andamento: 6,
      total_bancas: 12,
      total_formacoes: 39,
      producoes_por_qualis: { "A1": 8, "A2": 12, "B1": 6 },
      validacao_pendentes: { projetos: 2, orientacoes: 5, producoes: 3 },
    };
  };

  // Fetch statistics dynamically when filters change
  useEffect(() => {
    if (mainTab !== "estatisticas") return;

    if (!apiConnected) {
      setStatsData(generateSimulatedStats());
      return;
    }

    let query = `?`;
    if (statsProfessorId !== "todos") query += `professor_id=${statsProfessorId}&`;
    if (statsLinhaPesquisaId !== "todas") query += `linha_pesquisa_id=${statsLinhaPesquisaId}&`;
    if (statsAnoInicio) query += `ano_inicio=${statsAnoInicio}&`;
    if (statsAnoFim) query += `ano_fim=${statsAnoFim}&`;

    const statsCacheKey = cacheKey("analytics", "stats", query);
    if (!isCacheValid(statsCacheKey)) setLoadingStats(true);
    cachedJson(
      statsCacheKey,
      async () => {
        const res = await apiFetch(`/analises/estatisticas${query}`);
        if (!res.ok) throw new Error("Erro ao carregar estatísticas");
        return res.json();
      }
    )
      .then((data) => {
        setStatsData(data);
        setLoadingStats(false);
      })
      .catch((err) => {
        console.error("Erro ao buscar estatísticas da API:", err);
        setStatsData(generateSimulatedStats());
        setLoadingStats(false);
      });
  }, [mainTab, statsProfessorId, statsLinhaPesquisaId, statsAnoInicio, statsAnoFim, apiConnected]);

  // AI Report Generation Trigger
  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    setReportText("");
    setReportLogs([
      "[1/4] Consultando banco de dados PostgreSQL...",
      "[2/4] Consolidando estatísticas e publicações...",
      "[3/4] Formatando contexto estruturado para IA...",
      `[4/4] Solicitando redação ao modelo ${aiModelLabel} (pode levar 1–2 min)...`,
    ]);

    if (apiConnected) {
      try {
        const response = await apiFetch(`/analises/relatorio/gerar`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            professor_id: reportProfessorId === "todos" ? null : reportProfessorId,
            linha_pesquisa_id: reportLinhaPesquisaId === "todas" ? null : reportLinhaPesquisaId,
            ano_inicio: reportAnoInicio ? parseInt(reportAnoInicio) : null,
            ano_fim: reportAnoFim ? parseInt(reportAnoFim) : null,
            instrucoes_usuario: reportPrompt || "Gere uma análise moderna e compilada das produções e financiamentos."
          })
        });

        if (!response.ok) {
          const errBody = await response.json().catch(() => ({}));
          const msg = parseApiErrorDetail(
            errBody.detail,
            `HTTP ${response.status}`
          );
          throw new Error(msg || "Erro na geração do relatório");
        }
        const data = await response.json();
        
        setReportText(data.relatorio);
        setReportModelUsed(data.modelo);
        addAuditLog("relatorio", `[Real DB] Gerou relatório analítico via ${data.modelo || aiModelLabel}.`);
      } catch (err: any) {
        console.error("Erro na geração de relatório real:", err);
        const msg = String(err?.message || "");
        const friendly = msg === SESSION_EXPIRED_MESSAGE
          ? msg
          : msg.toLowerCase().includes("credenciais inválidas") ||
              msg.toLowerCase().includes("token expirado")
            ? SESSION_EXPIRED_MESSAGE
            : msg.toLowerCase().includes("failed to fetch")
              ? `Não foi possível contactar a API em ${getApiBaseUrl()}. Verifique se o servidor FastAPI está no ar, se NEXT_PUBLIC_API_URL está correto e se não há bloqueio de CORS/rede.`
              : msg || "Erro desconhecido";
        setReportText(`**Erro na geração de relatório:** ${friendly}`);
      } finally {
        setGeneratingReport(false);
      }
      return;
    }

    // Mock Report Fallback
    await new Promise((r) => setTimeout(r, 1500));
    const selectedProfObj = professors.find(p => p.id === reportProfessorId);
    const profName = selectedProfObj ? selectedProfObj.nome_completo : "Geral do PPGCOM";
    
    const mockText = `# Relatório Analítico Executivo - Indicadores Docentes (${profName})

**Data de Geração:** ${new Date().toLocaleDateString("pt-BR")} | **Solicitante:** Coordenador PPGCOM | **Motor de Análise:** ${aiModelLabel} (Simulado)

---

## 1. Introdução e Escopo
Este documento apresenta uma síntese executiva analítica da produção acadêmica, captação financeira e projetos de pesquisa vinculados ao corpo docente do Programa de Pós-Graduação em Comunicação (PPGCOM). A análise foca nas correlações entre fomento, produção de artigos qualificados e resolução de gaps nos currículos.

> **Diretrizes e Instruções Customizadas:**
> *"${reportPrompt || "Compilar produções gerais e gaps informacionais"}"*

---

## 2. Visão Geral das Métricas
A tabela a seguir consolida o desempenho quantitativo extraído dos currículos Lattes processados na base de dados:

| Docente | Tipo | Projetos Ativos | Produções | Fomento Estimado | Gaps Resolvidos |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Zé Messias** | Permanente | 2 | 24 | R$ 45.000,00 | 100% |
| **Domingos Alves** | Permanente | 2 | 4 | R$ 15.000,00 | 100% |
| **Marcelli Alves** | Permanente | 3 | 4 | R$ 25.000,00 | 100% |
| **Izani Mustafa** | Permanente | 2 | 4 | R$ 10.000,00 | 100% |

---

## 3. Análise Detalhada de Destaques
1. **Regularidade da Produção:** Observa-se que o corpo docente mantém um fluxo contínuo de publicações, com destaque para artigos de periódicos científicos e capítulos de livros em editoras de prestígio nacional.
2. **Captação de Fomento:** Os docentes com fomento ativo junto a agências de fomento como CNPq e FAPEMA lideram os grupos de pesquisa com maior densidade de alunos envolvidos, reiterando a importância do auxílio financeiro direto.
3. **Consistência de Dados (Human-in-the-Loop):** Com o processamento via pipeline de IA do PPGCOMDATA e a validação ativa feita pela coordenação, a integridade dos dados alcançou **100% de conformidade operacional**, eliminando duplicidades e incoerências estruturais comuns em currículos Lattes brutos.

---

## 4. Recomendações e Conclusões
* **Recomendação 1:** Estimular os professores com status de fomento pendente a revisarem seus currículos ou submeterem relatórios de auxílio, resolvendo potenciais lacunas de financiamento oculto.
* **Recomendação 2:** Alinhar as pesquisas em andamento com as metas do próximo quadriênio de avaliação CAPES, priorizando publicações em veículos de estratificação de alto impacto (A1 a A4).
`;
    setReportText(mockText);
    setReportModelUsed(`${aiModelLabel} (Simulado)`);
    setGeneratingReport(false);
    addAuditLog("relatorio", `Gerou relatório analítico simulado.`);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(reportText);
    alert("Relatório copiado para a área de transferência!");
  };

  const downloadMarkdown = () => {
    const element = document.createElement("a");
    const file = new Blob([reportText], {type: 'text/markdown'});
    element.href = URL.createObjectURL(file);
    element.download = "relatorio_ppgcomdata.md";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handlePrintReport = () => {
    if (!reportText.trim()) return;
    printReportInPage();
  };

  // Add audit log helper
  const addAuditLog = (action: string, msg: string) => {
    const timeStr = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setAuditLogs(prev => [
      {
        id: Math.random().toString(),
        acao: action,
        mensagem: msg,
        timestamp: timeStr
      },
      ...prev
    ]);
  };

  // Trigger Local Upload & Pipeline Execution
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleLattesFonteChange = (fonte: "html" | "xml") => {
    setLattesFonte(fonte);
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleReprocessCurriculo = async () => {
    if (!apiConnected || !selectedProfId) return;
    setIsProcessing(true);
    setUploadProgress(20);
    setProcessingStep("Reimportando último currículo Lattes...");
    try {
      const res = await apiFetch(`/uploads/professor/${selectedProfId}/reprocessar`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Nenhum currículo encontrado para reprocessar.");
      }
      const data = await res.json();
      setUploadProgress(100);
      const imp = data.importacao_xml || {};
      addAuditLog(
        "reprocessamento",
        `[Real DB] Currículo reimportado. Produções: ${imp.producoes_extraidas ?? 0}.`
      );
      invalidateProfessorCaches(selectedProfId);
      await reloadProfessorData(selectedProfId, true);
    } catch (err: any) {
      const msg = String(err?.message || "");
      if (msg.toLowerCase().includes("failed to fetch")) {
        alert(
          "Não foi possível contactar a API (rede/CORS ou servidor indisponível). " +
          "Confira se a API está no ar e se NEXT_PUBLIC_API_URL aponta para " +
          getApiBaseUrl()
        );
      } else {
        alert(msg || "Erro ao reprocessar.");
      }
    } finally {
      setIsProcessing(false);
      setProcessingStep("");
      setUploadProgress(0);
    }
  };

  const handleUploadAndProcess = async () => {
    if (!selectedFile || !selectedProfId) return;

    setIsProcessing(true);
    setUploadProgress(15);
    setProcessingStep(
      lattesFonte === "html"
        ? "Convertendo HTML do Lattes para XML..."
        : "Importando XML do Lattes..."
    );

    if (apiConnected) {
      const formData = new FormData();
      formData.append("professor_id", selectedProfId);
      formData.append("fonte", lattesFonte);
      formData.append("file", selectedFile);

      try {
        setUploadProgress(40);
        const uploadRes = await apiFetch(`/uploads/lattes`, {
          method: "POST",
          body: formData,
        });
        if (!uploadRes.ok) {
          const errBody = await uploadRes.json().catch(() => ({}));
          throw new Error(
            (errBody as { detail?: string }).detail || "Erro na importação do currículo."
          );
        }
        const result = await uploadRes.json();
        setUploadProgress(100);
        setIsProcessing(false);
        setProcessingStep("");
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";

        const imp = result.importacao_xml || {};
        addAuditLog(
          "importacao_lattes",
          `[Real DB] Currículo importado (${lattesFonte.toUpperCase()}). ` +
            `Produções: ${imp.producoes_extraidas ?? 0}, projetos: ${imp.projetos_extraidos ?? 0}.`
        );
        invalidateProfessorCaches(selectedProfId);
        await reloadProfessorData(selectedProfId, true);
      } catch (err: unknown) {
        console.error("Erro na importação Lattes:", err);
        setIsProcessing(false);
        setProcessingStep("");
        alert(err instanceof Error ? err.message : "Erro desconhecido na importação.");
      }
      return;
    }

    // Simulate pipeline (offline)
    setTimeout(() => {
      setUploadProgress(60);
      setProcessingStep("Gerando XML estruturado...");
    }, 1200);

    setTimeout(() => {
      setUploadProgress(90);
      setProcessingStep("Importando dados no banco...");
    }, 2400);

    setTimeout(() => {
      setUploadProgress(100);
      setIsProcessing(false);
      setProcessingStep("");
      setSelectedFile(null);
      
      setProfessors(prev => prev.map(p => {
        if (p.id === selectedProfId) {
          return { ...p, status: "processado" };
        }
        return p;
      }));

      addAuditLog("processamento", `Pipeline finalizado com sucesso para o Lattes.`);
      
      if (selectedProfId === "1") {
        setSelectedProfId("1");
      }
    }, 6000);
  };

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
