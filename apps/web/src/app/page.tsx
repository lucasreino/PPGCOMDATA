"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { 
  FileText, Upload, Check, Edit2, Trash2, AlertTriangle, 
  HelpCircle, CheckCircle, RefreshCw, BarChart2, Plus, 
  BookOpen, Calendar, DollarSign, Eye, EyeOff, Award, Clock, ArrowRight, UserPlus, Info,
  Users, GraduationCap, Wrench, Trophy, Network
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  apiFetch,
  getApiBaseUrl,
  getStoredToken,
  parseApiErrorDetail,
  SESSION_EXPIRED_MESSAGE,
} from "@/lib/api";
import type {
  Professor, Projeto, Evento, Producao, Financiamento, AlertaLacuna, LogAudit, MainTab, EntityTab,
  Orientacao, FormacaoAcademica, ProfessorResumo,
  ProducaoTecnica, Premio, GrupoPesquisa,
} from "@/lib/types";

const VALIDATION_TABS: EntityTab[] = [
  "projetos", "eventos", "producoes", "financiamentos",
  "orientacoes", "formacoes_academicas",
  "producoes_tecnicas", "premios", "grupos_pesquisa",
];

function tabLabel(tab: EntityTab): string {
  const labels: Record<EntityTab, string> = {
    projetos: "projetos",
    eventos: "eventos",
    producoes: "produções",
    financiamentos: "financiamentos",
    orientacoes: "orientações",
    formacoes_academicas: "formação",
    producoes_tecnicas: "prod. técnica",
    premios: "prêmios",
    grupos_pesquisa: "grupos",
  };
  return labels[tab];
}
import { ResumoAcademicoCard } from "@/components/academic/ResumoAcademicoCard";
import { PendingValidationModal } from "@/components/validation/PendingValidationModal";
import { ArtigosQualisModal } from "@/components/analytics/ArtigosQualisModal";
import { AppShellHeader } from "@/components/layout/AppShellHeader";
import { groupOrientacoesByTipo } from "@/lib/orientacao-groups";
import { groupProducoesByTipo } from "@/lib/producao-groups";
import { printReportInPage } from "@/lib/report-print";
import { sortEntityPayload } from "@/lib/sort-entities";
import {
  ActionPanel,
  ConfidenceBadge,
  EmptyState,
  OriginalFragment,
  SimpleMarkdownRenderer,
} from "@/components/ui/validation-ui";

export default function Dashboard() {
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
          const linhasRes = await apiFetch("/linhas-pesquisa/");
          if (linhasRes.ok) {
            const data = await linhasRes.json();
            if (data && data.length > 0) {
              setLinhasPesquisa(data);
            }
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

  // Fetch all professors when API is connected
  useEffect(() => {
    if (!apiConnected) return;

    apiFetch("/professores/")
      .then(res => {
        if (!res.ok) throw new Error("Erro ao carregar docentes");
        return res.json();
      })
      .then((data: any[]) => {
        const mapped = data.map(p => ({
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
          status: (p.status ? "validado" : "pendente") as "validado" | "pendente"
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
          if (!unique.some(p => p.id === selectedProfId)) {
            setSelectedProfId(unique[0].id);
          }
        }
      })
      .catch(err => {
        console.error("Falha ao buscar docentes da API:", err);
      });
  }, [apiConnected, apiUrl, linhasPesquisa]);

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

  const reloadProfessorData = (profId: string) => {
    if (!apiConnected) return;
    setLoading(true);
    Promise.all([
      apiFetch(`/validacao/pendentes?professor_id=${profId}`),
      apiFetch(`/professores/${profId}/orientacoes`),
      apiFetch(`/professores/${profId}/formacoes`),
    ])
      .then(async ([pendentesRes, orientRes, formRes]) => {
        if (!pendentesRes.ok) throw new Error("Erro ao carregar dados do docente");
        const data = sortEntityPayload(await pendentesRes.json());
        setProjetos(data.projetos || []);
        setEventos(data.eventos || []);
        setProducoes(data.producoes || []);
        setFinanciamentos(data.financiamentos || []);
        setProducoesTecnicas(data.producoes_tecnicas || []);
        setPremios(data.premios || []);
        setGruposPesquisa(data.grupos_pesquisa || []);
        setLacunas(data.lacunas || []);

        if (orientRes.ok) {
          const orientData = await orientRes.json();
          setOrientacoes(
            orientData.length > 0 ? orientData : data.orientacoes || []
          );
        } else {
          setOrientacoes(data.orientacoes || []);
        }

        if (formRes.ok) {
          const formData = await formRes.json();
          setFormacoes(
            formData.length > 0 ? formData : data.formacoes_academicas || []
          );
        } else {
          setFormacoes(data.formacoes_academicas || []);
        }

        setLoading(false);
      })
      .catch((err) => {
        console.error("Falha ao buscar dados do docente:", err);
        setLoading(false);
      });
    apiFetch(`/professores/${profId}/resumo-academico`)
      .then((res) => (res.ok ? res.json() : null))
      .then((r) => setResumoAcademico(r))
      .catch(() => setResumoAcademico(null));
  };

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
  }, [selectedProfId, apiConnected, apiUrl]);

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
        .then(res => {
          if (!res.ok) throw new Error("Falha ao salvar edição");
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
          alert("Erro ao salvar edição no servidor.");
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

    setLoadingStats(true);
    let query = `?`;
    if (statsProfessorId !== "todos") query += `professor_id=${statsProfessorId}&`;
    if (statsLinhaPesquisaId !== "todas") query += `linha_pesquisa_id=${statsLinhaPesquisaId}&`;
    if (statsAnoInicio) query += `ano_inicio=${statsAnoInicio}&`;
    if (statsAnoFim) query += `ano_fim=${statsAnoFim}&`;

    apiFetch(`/analises/estatisticas${query}`)
      .then(res => {
        if (!res.ok) throw new Error("Erro ao carregar estatísticas");
        return res.json();
      })
      .then(data => {
        setStatsData(data);
        setLoadingStats(false);
      })
      .catch(err => {
        console.error("Erro ao buscar estatísticas da API:", err);
        setStatsData(generateSimulatedStats());
        setLoadingStats(false);
      });
  }, [mainTab, statsProfessorId, statsLinhaPesquisaId, statsAnoInicio, statsAnoFim, apiConnected, apiUrl]);

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

  const handleReprocessCurriculo = async () => {
    if (!apiConnected || !selectedProfId) return;
    setIsProcessing(true);
    setUploadProgress(20);
    setProcessingStep("Reprocessando último PDF do docente...");
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
      addAuditLog(
        "reprocessamento",
        `[Real DB] Currículo reprocessado. Seções: ${data.secoes_detectadas || 0}.`
      );
      reloadProfessorData(selectedProfId);
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
    if (!selectedFile) return;

    setIsProcessing(true);
    setUploadProgress(10);
    setProcessingStep("Enviando Currículo Lattes PDF...");

    if (apiConnected) {
      const formData = new FormData();
      formData.append("professor_id", selectedProfId);
      formData.append("file", selectedFile);

      try {
        const uploadRes = await apiFetch(`/uploads/`, {
          method: "POST",
          body: formData
        });
        if (!uploadRes.ok) throw new Error("Erro no upload do arquivo.");
        const uploadData = await uploadRes.json();
        
        setUploadProgress(50);
        setProcessingStep("Processamento iniciado (IA pode levar 5–15 min)...");

        const processRes = await apiFetch(`/uploads/${uploadData.id}/processar`, {
          method: "POST",
        });
        if (!processRes.ok) throw new Error("Erro ao iniciar processamento do arquivo.");
        const startData = await processRes.json();

        const pollUntilDone = async () => {
          const maxAttempts = 200;
          for (let i = 0; i < maxAttempts; i++) {
            await new Promise((r) => setTimeout(r, 3000));
            const statusRes = await apiFetch(`/uploads/${uploadData.id}`);
            if (!statusRes.ok) continue;
            const uploadStatus = await statusRes.json();
            const st = uploadStatus.status as string;
            setUploadProgress(Math.min(95, 50 + Math.floor((i / maxAttempts) * 45)));
            setProcessingStep(
              `Processando… status: ${st.replace(/_/g, " ")} (${Math.floor((i * 3) / 60)} min)`
            );
            if (st === "processando") continue;
            if (st === "erro_no_processamento") {
              throw new Error(uploadStatus.mensagem_erro || "Erro no processamento do PDF.");
            }
            return uploadStatus;
          }
          throw new Error(
            "Processamento demorou demais. Verifique os logs da API ou use Reprocessar depois."
          );
        };

        await pollUntilDone();

        setUploadProgress(100);
        setIsProcessing(false);
        setProcessingStep("");
        setSelectedFile(null);
        addAuditLog(
          "processamento",
          `[Real DB] Lattes processado (${startData.status || "ok"}). Docente: ${selectedProfId}.`
        );

        reloadProfessorData(selectedProfId);
      } catch (err: any) {
        console.error("Erro no processamento real:", err);
        setIsProcessing(false);
        setProcessingStep("");
        alert(`Erro no processamento: ${err.message || "Erro desconhecido"}`);
      }
      return;
    }

    // Simulate pipeline beautifully (mock)
    setTimeout(() => {
      setUploadProgress(40);
      setProcessingStep("Extraindo texto do PDF (PyMuPDF)...");
    }, 1500);

    setTimeout(() => {
      setUploadProgress(75);
      setProcessingStep("Identificando seções estruturadas do Lattes...");
    }, 3000);

    setTimeout(() => {
      setUploadProgress(95);
      setProcessingStep(`IA (${aiModelLabel}) mapeando Projetos, Produções e Auxílios...`);
    }, 4500);

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

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400 text-sm">
        Carregando sessão...
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      <AppShellHeader
        section="operacao"
        operacaoView={mainTab}
        onOperacaoViewChange={navigateMainTab}
        apiConnected={apiConnected}
      />

      {/* 📊 Dashboard Core */}
      {mainTab === "validacao" && (
        <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 animate-fadeIn">
        
        {/* Left Side: Professor Selection & Lattes Upload (3 Cols) */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Professors Card */}
          <div className="glow-card rounded-xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-semibold tracking-wider text-slate-300 uppercase">Corpo Docente</h2>
              <span className="text-xs px-2 py-0.5 bg-slate-800 rounded text-slate-400 font-semibold">{professors.length}</span>
            </div>
            
            <div className="space-y-3">
              {professors.map((p) => {
                const isSelected = p.id === selectedProfId;
                return (
                  <button
                    key={p.id}
                    onClick={() => setSelectedProfId(p.id)}
                    className={`w-full text-left p-3 rounded-lg border transition-all duration-200 flex flex-col ${
                      isSelected 
                        ? "bg-indigo-950/40 border-indigo-700/80 shadow-md shadow-indigo-950/20" 
                        : "bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/70"
                    }`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <span className="font-semibold text-sm text-slate-200">{p.nome_completo}</span>
                      <span className={`w-2 h-2 rounded-full ${
                        p.status === "validado" ? "bg-emerald-500" : p.status === "processado" ? "bg-blue-500 animate-pulse" : "bg-amber-500"
                      }`}></span>
                    </div>
                    <span className="text-xs text-slate-400 mt-1">{p.linha}</span>
                    
                    <div className="flex justify-between items-center w-full mt-2.5 pt-2 border-t border-slate-900 text-[10px]">
                      <span className="text-slate-500 font-medium">{p.tipo}</span>
                      <span className={`px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                        p.status === "validado" 
                          ? "bg-emerald-950/60 text-emerald-400 border border-emerald-900/60" 
                          : p.status === "processado" 
                          ? "bg-blue-950/60 text-blue-400 border border-blue-900/60"
                          : "bg-amber-950/60 text-amber-400 border border-amber-900/60"
                      }`}>
                        {p.status}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            <button className="w-full mt-4 flex items-center justify-center gap-2 py-2 px-3 bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 rounded-lg text-xs font-semibold text-slate-300 transition-colors">
              <UserPlus className="w-4.5 h-4.5" />
              Novo Docente
            </button>
          </div>

          {/* Lattes Upload Card */}
          <div className="glow-card rounded-xl p-5">
            <h2 className="text-sm font-semibold tracking-wider text-slate-300 uppercase mb-4">Upload do Lattes</h2>
            
            <div className="space-y-4">
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-800 hover:border-indigo-800 hover:bg-indigo-950/10 rounded-xl p-6 text-center cursor-pointer transition-all duration-200"
              >
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  accept=".pdf" 
                  className="hidden" 
                />
                <Upload className="w-8 h-8 text-indigo-400 mx-auto mb-3" />
                <span className="text-xs font-semibold text-slate-300 block mb-1">
                  {selectedFile ? selectedFile.name : "Clique para selecionar PDF"}
                </span>
                <span className="text-[10px] text-slate-500 block">
                  Apenas PDFs digitais oficiais do Lattes
                </span>
              </div>

              {isProcessing && (
                <div className="space-y-2 p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-indigo-400 font-semibold">{processingStep}</span>
                    <span className="text-slate-400 font-bold">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                    <div 
                      className="bg-indigo-600 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <button
                disabled={!selectedFile || isProcessing}
                onClick={handleUploadAndProcess}
                className={`w-full py-2.5 px-4 rounded-lg font-semibold text-xs transition-all flex items-center justify-center gap-2 ${
                  selectedFile && !isProcessing
                    ? "bg-indigo-600 text-white hover:bg-indigo-500 shadow-lg shadow-indigo-600/20 cursor-pointer"
                    : "bg-slate-800 text-slate-500 cursor-not-allowed"
                }`}
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Processando...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    Processar com IA
                  </>
                )}
              </button>

              <button
                type="button"
                disabled={!apiConnected || isProcessing}
                onClick={handleReprocessCurriculo}
                className={`w-full py-2 px-4 rounded-lg font-semibold text-xs border transition-all flex items-center justify-center gap-2 ${
                  apiConnected && !isProcessing
                    ? "border-slate-600 text-slate-300 hover:border-indigo-700 hover:bg-slate-900"
                    : "border-slate-800 text-slate-600 cursor-not-allowed"
                }`}
                title="Reextrai dados do último PDF enviado deste docente (sem novo upload)"
              >
                <RefreshCw className={`w-4 h-4 ${isProcessing ? "animate-spin" : ""}`} />
                Reprocessar último Lattes
              </button>
            </div>
          </div>
        </div>

        {/* Center Panel: Human-in-the-Loop Validation View (6 Cols) */}
        <div className="lg:col-span-6 space-y-6">

          <ResumoAcademicoCard resumo={resumoAcademico} />
          
          {/* Tabs navigation */}
          <div className="bg-[#0f172a]/50 p-1 border border-[#1e293b] rounded-xl flex flex-wrap gap-1">
            {VALIDATION_TABS.map((tab) => {
              const count =
                tab === "projetos" ? projetos.length
                : tab === "eventos" ? eventos.length
                : tab === "producoes" ? producoes.length
                : tab === "financiamentos" ? financiamentos.length
                : tab === "orientacoes" ? orientacoes.length
                : tab === "formacoes_academicas" ? formacoes.length
                : tab === "producoes_tecnicas" ? producoesTecnicas.length
                : tab === "premios" ? premios.length
                : gruposPesquisa.length;

              return (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 min-w-[88px] py-2 px-2 text-[11px] font-semibold rounded-lg transition-all duration-200 flex items-center justify-center gap-1.5 ${
                    activeTab === tab
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/10"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {tab === "projetos" && <BookOpen className="w-3.5 h-3.5" />}
                  {tab === "eventos" && <Calendar className="w-3.5 h-3.5" />}
                  {tab === "producoes" && <FileText className="w-3.5 h-3.5" />}
                  {tab === "financiamentos" && <DollarSign className="w-3.5 h-3.5" />}
                  {tab === "orientacoes" && <Users className="w-3.5 h-3.5" />}
                  {tab === "formacoes_academicas" && <GraduationCap className="w-3.5 h-3.5" />}
                  {tab === "producoes_tecnicas" && <Wrench className="w-3.5 h-3.5" />}
                  {tab === "premios" && <Trophy className="w-3.5 h-3.5" />}
                  {tab === "grupos_pesquisa" && <Network className="w-3.5 h-3.5" />}
                  {tabLabel(tab)}
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    activeTab === tab ? "bg-indigo-500 text-white" : "bg-slate-800 text-slate-400"
                  }`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Validation workspace */}
          <div className="space-y-4">
            
            {/* Empty State */}
            {activeTab === "projetos" && projetos.length === 0 && <EmptyState tab="projetos" />}
            {activeTab === "eventos" && eventos.length === 0 && <EmptyState tab="eventos" />}
            {activeTab === "producoes" && producoes.length === 0 && <EmptyState tab="producoes" />}
            {activeTab === "financiamentos" && financiamentos.length === 0 && <EmptyState tab="financiamentos" />}
            {activeTab === "orientacoes" && orientacoes.length === 0 && <EmptyState tab="orientacoes" />}
            {activeTab === "formacoes_academicas" && formacoes.length === 0 && <EmptyState tab="formacoes_academicas" />}
            {activeTab === "producoes_tecnicas" && producoesTecnicas.length === 0 && <EmptyState tab="produções técnicas" />}
            {activeTab === "premios" && premios.length === 0 && <EmptyState tab="prêmios" />}
            {activeTab === "grupos_pesquisa" && gruposPesquisa.length === 0 && <EmptyState tab="grupos de pesquisa" />}

            {/* PROJECTS VIEW */}
            {activeTab === "projetos" && projetos.map((item) => (
              <div 
                key={item.id} 
                className={`glow-card rounded-xl p-5 border transition-all duration-300 relative overflow-hidden ${
                  item.status_validacao === "confirmado" ? "border-emerald-700/60 bg-emerald-950/10" :
                  item.status_validacao === "editado" ? "border-indigo-700/60 bg-indigo-950/10" :
                  item.status_validacao === "descartado" ? "border-rose-950 bg-rose-950/5 opacity-40 hover:opacity-70" : "border-slate-800"
                }`}
              >
                {/* Visual Status Indicator tag */}
                <div className="absolute top-0 left-0 right-0 h-1 flex">
                  <div className={`w-full ${
                    item.status_validacao === "confirmado" ? "bg-emerald-500" :
                    item.status_validacao === "editado" ? "bg-indigo-500" :
                    item.status_validacao === "descartado" ? "bg-rose-500" : "bg-slate-700"
                  }`}></div>
                </div>

                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 text-slate-300 rounded font-bold uppercase tracking-wider">
                      {item.tipo}
                    </span>
                    <h3 className="text-sm font-bold text-slate-200 mt-1">{item.titulo}</h3>
                  </div>

                  <ConfidenceBadge level={item.confianca_ia} />
                </div>

                <p className="text-xs text-slate-400 mt-3.5 leading-relaxed bg-slate-950/40 p-2.5 rounded border border-slate-900">
                  {item.descricao}
                </p>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4 text-[11px] text-slate-300">
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Vigência</span>
                    <span className="font-semibold">{item.ano_inicio} — {item.ano_fim || "Atual"}</span>
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Papel</span>
                    <span className="font-semibold">{item.papel_docente}</span>
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850 col-span-2 md:col-span-1">
                    <span className="text-[9px] text-slate-500 block">Fomento</span>
                    <span className={`font-semibold ${item.financiamento_mencionado ? "text-emerald-400" : "text-slate-400"}`}>
                      {item.agencia_fomento || (item.financiamento_mencionado ? "Sim (Verificar)" : "Nenhum")}
                    </span>
                  </div>
                </div>

                {/* Collapsible Original Fragment */}
                <OriginalFragment text={item.trecho_original} />

                {/* Human-in-the-loop actions */}
                <ActionPanel 
                  status={item.status_validacao} 
                  onConfirm={() => handleConfirm("projetos", item.id)}
                  onEdit={() => handleOpenEdit("projetos", item)}
                  onDiscard={() => handleDiscard("projetos", item.id)}
                />
              </div>
            ))}

            {/* EVENTS VIEW */}
            {activeTab === "eventos" && eventos.map((item) => (
              <div 
                key={item.id} 
                className={`glow-card rounded-xl p-5 border transition-all duration-300 relative overflow-hidden ${
                  item.status_validacao === "confirmado" ? "border-emerald-700/60 bg-emerald-950/10" :
                  item.status_validacao === "editado" ? "border-indigo-700/60 bg-indigo-950/10" :
                  item.status_validacao === "descartado" ? "border-rose-950 bg-rose-950/5 opacity-40" : "border-slate-800"
                }`}
              >
                <div className="absolute top-0 left-0 right-0 h-1 flex">
                  <div className={`w-full ${
                    item.status_validacao === "confirmado" ? "bg-emerald-500" :
                    item.status_validacao === "editado" ? "bg-indigo-500" :
                    item.status_validacao === "descartado" ? "bg-rose-500" : "bg-slate-700"
                  }`}></div>
                </div>

                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 text-slate-300 rounded font-bold uppercase tracking-wider">
                      {item.eh_organizacao ? "organização" : item.tipo_participacao}
                    </span>
                    <h3 className="text-sm font-bold text-slate-200 mt-1">{item.nome_evento}</h3>
                  </div>

                  <ConfidenceBadge level={item.confianca_ia} />
                </div>

                <div className="text-xs text-slate-400 mt-3 bg-slate-950/40 p-2.5 rounded border border-slate-900">
                  <span className="text-[9px] text-slate-500 block mb-0.5">Trabalho Apresentado</span>
                  <span className="font-semibold text-slate-200">"{item.titulo_trabalho}"</span>
                </div>

                <div className="grid grid-cols-3 gap-3 mt-4 text-[11px] text-slate-300">
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Ano</span>
                    <span className="font-semibold">{item.ano}</span>
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Localidade</span>
                    <span className="font-semibold">{item.cidade}, {item.pais}</span>
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Auxílio Mobilidade</span>
                    <span className={`font-semibold ${item.financiamento_mencionado ? "text-emerald-400" : "text-slate-500"}`}>
                      {item.fonte_financiamento || "Não consta"}
                    </span>
                  </div>
                </div>

                <OriginalFragment text={item.trecho_original} />

                <ActionPanel 
                  status={item.status_validacao} 
                  onConfirm={() => handleConfirm("eventos", item.id)}
                  onEdit={() => handleOpenEdit("eventos", item)}
                  onDiscard={() => handleDiscard("eventos", item.id)}
                />
              </div>
            ))}

            {/* PRODUÇÕES — agrupadas por tipo */}
            {activeTab === "producoes" && producoesPorTipo.map((group) => (
              <section key={group.tipo} className="space-y-4">
                <div className="flex items-center gap-2 sticky top-24 z-10 py-2 bg-[#0b1120]/90 backdrop-blur-sm border-b border-slate-800/80">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                    {group.label}
                  </h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-semibold">
                    {group.items.length}
                  </span>
                </div>
                {group.items.map((item) => (
                  <div
                    key={item.id}
                    className={`glow-card rounded-xl p-5 border transition-all duration-300 relative overflow-hidden ${
                      item.status_validacao === "confirmado" ? "border-emerald-700/60 bg-emerald-950/10" :
                      item.status_validacao === "editado" ? "border-indigo-700/60 bg-indigo-950/10" :
                      item.status_validacao === "descartado" ? "border-rose-950 bg-rose-950/5 opacity-40" : "border-slate-800"
                    }`}
                  >
                    <div className="absolute top-0 left-0 right-0 h-1 flex">
                      <div className={`w-full ${
                        item.status_validacao === "confirmado" ? "bg-emerald-500" :
                        item.status_validacao === "editado" ? "bg-indigo-500" :
                        item.status_validacao === "descartado" ? "bg-rose-500" : "bg-slate-700"
                      }`}></div>
                    </div>

                    <div className="flex justify-between items-start gap-4">
                      <div className="space-y-1">
                        <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 text-slate-300 rounded font-bold uppercase tracking-wider">
                          {item.tipo}
                        </span>
                        <h3 className="text-sm font-bold text-slate-200 mt-1">{item.titulo}</h3>
                      </div>

                      <ConfidenceBadge level={item.confianca_ia} />
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-[11px] text-slate-300">
                      <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                        <span className="text-[9px] text-slate-500 block">Ano</span>
                        <span className="font-semibold">{item.ano}</span>
                      </div>
                      <div className="bg-slate-900/40 p-2 rounded border border-slate-850 col-span-2 md:col-span-1">
                        <span className="text-[9px] text-slate-500 block">Veículo / Editora</span>
                        <span className="font-semibold truncate block">{item.veiculo}</span>
                      </div>
                      <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                        <span className="text-[9px] text-slate-500 block">DOI</span>
                        <span className="font-semibold font-mono text-[10px] truncate block text-indigo-400">{item.doi || "N/D"}</span>
                      </div>
                      <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                        <span className="text-[9px] text-slate-500 block">ISSN / ISBN</span>
                        <span className="font-semibold font-mono text-[10px] truncate block">{item.issn || "N/D"}</span>
                      </div>
                      {item.qualis && (
                        <div className="bg-indigo-950/40 p-2 rounded border border-indigo-900">
                          <span className="text-[9px] text-indigo-400 block font-bold">Qualis</span>
                          <span className="font-bold text-indigo-300">{item.qualis}</span>
                        </div>
                      )}
                    </div>

                    <OriginalFragment text={item.trecho_original} />

                    <ActionPanel
                      status={item.status_validacao}
                      onConfirm={() => handleConfirm("producoes", item.id)}
                      onEdit={() => handleOpenEdit("producoes", item)}
                      onDiscard={() => handleDiscard("producoes", item.id)}
                    />
                  </div>
                ))}
              </section>
            ))}

            {/* ORIENTAÇÕES — agrupadas por tipo */}
            {activeTab === "orientacoes" && orientacoesPorTipo.map((group) => (
              <section key={group.tipo} className="space-y-4">
                <div className="flex items-center gap-2 sticky top-24 z-10 py-2 bg-[#0b1120]/90 backdrop-blur-sm border-b border-slate-800/80">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                    {group.label}
                  </h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-semibold">
                    {group.items.length}
                  </span>
                </div>
                {group.items.map((item) => (
                  <div
                    key={item.id}
                    className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                      item.status_validacao === "confirmado" ? "border-emerald-700/60 bg-emerald-950/10" :
                      item.status_validacao === "editado" ? "border-indigo-700/60 bg-indigo-950/10" :
                      item.status_validacao === "descartado" ? "border-rose-950 bg-rose-950/5 opacity-40" : "border-slate-800"
                    }`}
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 rounded font-bold uppercase">
                          {item.status}
                        </span>
                        <h3 className="text-sm font-bold text-slate-200 mt-2">
                          {item.nome_orientando || "Orientando não identificado"}
                        </h3>
                        {item.titulo_trabalho && (
                          <p className="text-[11px] text-slate-400 mt-1">{item.titulo_trabalho}</p>
                        )}
                      </div>
                      <ConfidenceBadge level={item.confianca_ia} />
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-3 text-[11px] text-slate-300">
                      <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                        <span className="text-[9px] text-slate-500 block">Início</span>
                        {item.ano_inicio ?? "—"}
                      </div>
                      <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                        <span className="text-[9px] text-slate-500 block">Conclusão</span>
                        {item.ano_conclusao ?? "—"}
                      </div>
                      <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                        <span className="text-[9px] text-slate-500 block">Papel</span>
                        {item.papel}
                      </div>
                    </div>
                    <OriginalFragment text={item.trecho_original} />
                    <ActionPanel
                      status={item.status_validacao}
                      onConfirm={() => handleConfirm("orientacoes", item.id)}
                      onEdit={() => handleOpenEdit("orientacoes", item)}
                      onDiscard={() => handleDiscard("orientacoes", item.id)}
                    />
                  </div>
                ))}
              </section>
            ))}

            {/* FORMAÇÃO */}
            {activeTab === "formacoes_academicas" && formacoes.map((item) => (
              <div
                key={item.id}
                className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                  item.status_validacao === "confirmado" ? "border-emerald-700/60 bg-emerald-950/10" :
                  item.status_validacao === "editado" ? "border-indigo-700/60 bg-indigo-950/10" :
                  item.status_validacao === "descartado" ? "border-rose-950 bg-rose-950/5 opacity-40" : "border-slate-800"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 rounded font-bold uppercase">
                      {item.nivel}
                    </span>
                    <h3 className="text-sm font-bold text-slate-200 mt-2">{item.curso || "Curso não informado"}</h3>
                    <p className="text-[11px] text-slate-400">{item.instituicao}</p>
                  </div>
                  <ConfidenceBadge level={item.confianca_ia} />
                </div>
                <div className="grid grid-cols-2 gap-2 mt-3 text-[11px] text-slate-300">
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Período</span>
                    {item.ano_inicio ?? "?"} — {item.ano_fim ?? "?"}
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Área</span>
                    {item.area_conhecimento || "—"}
                  </div>
                </div>
                <OriginalFragment text={item.trecho_original} />
                <ActionPanel
                  status={item.status_validacao}
                  onConfirm={() => handleConfirm("formacoes_academicas", item.id)}
                  onEdit={() => handleOpenEdit("formacoes_academicas", item)}
                  onDiscard={() => handleDiscard("formacoes_academicas", item.id)}
                />
              </div>
            ))}

            {/* PRODUÇÃO TÉCNICA */}
            {activeTab === "producoes_tecnicas" && producoesTecnicas.map((item) => (
              <div
                key={item.id}
                className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                  item.status_validacao === "confirmado" ? "border-emerald-700/60 bg-emerald-950/10" :
                  item.status_validacao === "editado" ? "border-indigo-700/60 bg-indigo-950/10" :
                  item.status_validacao === "descartado" ? "border-rose-950 bg-rose-950/5 opacity-40" : "border-slate-800"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 rounded font-bold uppercase">
                      {item.tipo}
                    </span>
                    <h3 className="text-sm font-bold text-slate-200 mt-2">{item.titulo}</h3>
                    {item.instituicao && <p className="text-[11px] text-slate-400 mt-1">{item.instituicao}</p>}
                  </div>
                  <ConfidenceBadge level={item.confianca_ia} />
                </div>
                {item.descricao && (
                  <p className="text-xs text-slate-400 mt-3 bg-slate-950/40 p-2.5 rounded border border-slate-900">{item.descricao}</p>
                )}
                <div className="grid grid-cols-2 gap-2 mt-3 text-[11px] text-slate-300">
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Ano</span>
                    {item.ano ?? "—"}
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">URL</span>
                    <span className="truncate block text-indigo-400">{item.url || "—"}</span>
                  </div>
                </div>
                <OriginalFragment text={item.trecho_original} />
                <ActionPanel
                  status={item.status_validacao}
                  onConfirm={() => handleConfirm("producoes_tecnicas", item.id)}
                  onEdit={() => handleOpenEdit("producoes_tecnicas", item)}
                  onDiscard={() => handleDiscard("producoes_tecnicas", item.id)}
                />
              </div>
            ))}

            {/* PRÊMIOS */}
            {activeTab === "premios" && premios.map((item) => (
              <div
                key={item.id}
                className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                  item.status_validacao === "confirmado" ? "border-emerald-700/60 bg-emerald-950/10" :
                  item.status_validacao === "editado" ? "border-indigo-700/60 bg-indigo-950/10" :
                  item.status_validacao === "descartado" ? "border-rose-950 bg-rose-950/5 opacity-40" : "border-slate-800"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 rounded font-bold uppercase">
                      {item.tipo}
                    </span>
                    <h3 className="text-sm font-bold text-slate-200 mt-2">{item.nome}</h3>
                    {item.instituicao_concedente && (
                      <p className="text-[11px] text-slate-400 mt-1">{item.instituicao_concedente}</p>
                    )}
                  </div>
                  <ConfidenceBadge level={item.confianca_ia} />
                </div>
                {item.descricao && (
                  <p className="text-xs text-slate-400 mt-3 bg-slate-950/40 p-2.5 rounded border border-slate-900">{item.descricao}</p>
                )}
                <div className="grid grid-cols-2 gap-2 mt-3 text-[11px] text-slate-300">
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Ano</span>
                    {item.ano ?? "—"}
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Concedente</span>
                    {item.instituicao_concedente || "—"}
                  </div>
                </div>
                <OriginalFragment text={item.trecho_original} />
                <ActionPanel
                  status={item.status_validacao}
                  onConfirm={() => handleConfirm("premios", item.id)}
                  onEdit={() => handleOpenEdit("premios", item)}
                  onDiscard={() => handleDiscard("premios", item.id)}
                />
              </div>
            ))}

            {/* GRUPOS DE PESQUISA */}
            {activeTab === "grupos_pesquisa" && gruposPesquisa.map((item) => (
              <div
                key={item.id}
                className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                  item.status_validacao === "confirmado" ? "border-emerald-700/60 bg-emerald-950/10" :
                  item.status_validacao === "editado" ? "border-indigo-700/60 bg-indigo-950/10" :
                  item.status_validacao === "descartado" ? "border-rose-950 bg-rose-950/5 opacity-40" : "border-slate-800"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 rounded font-bold uppercase">
                      {item.papel}
                    </span>
                    <h3 className="text-sm font-bold text-slate-200 mt-2">{item.nome_grupo}</h3>
                    {item.linha_tematica && (
                      <p className="text-[11px] text-slate-400 mt-1">{item.linha_tematica}</p>
                    )}
                  </div>
                  <ConfidenceBadge level={item.confianca_ia} />
                </div>
                <div className="grid grid-cols-3 gap-2 mt-3 text-[11px] text-slate-300">
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Código DGP</span>
                    {item.codigo_dgp || "—"}
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850 col-span-2">
                    <span className="text-[9px] text-slate-500 block">Instituição</span>
                    {item.instituicao || "—"}
                  </div>
                </div>
                <OriginalFragment text={item.trecho_original} />
                <ActionPanel
                  status={item.status_validacao}
                  onConfirm={() => handleConfirm("grupos_pesquisa", item.id)}
                  onEdit={() => handleOpenEdit("grupos_pesquisa", item)}
                  onDiscard={() => handleDiscard("grupos_pesquisa", item.id)}
                />
              </div>
            ))}

            {/* FUNDING VIEW */}
            {activeTab === "financiamentos" && financiamentos.map((item) => (
              <div 
                key={item.id} 
                className={`glow-card rounded-xl p-5 border transition-all duration-300 relative overflow-hidden ${
                  item.status_validacao === "confirmado" ? "border-emerald-700/60 bg-emerald-950/10" :
                  item.status_validacao === "editado" ? "border-indigo-700/60 bg-indigo-950/10" :
                  item.status_validacao === "descartado" ? "border-rose-950 bg-rose-950/5 opacity-40" : "border-slate-800"
                }`}
              >
                <div className="absolute top-0 left-0 right-0 h-1 flex">
                  <div className={`w-full ${
                    item.status_validacao === "confirmado" ? "bg-emerald-500" :
                    item.status_validacao === "editado" ? "bg-indigo-500" :
                    item.status_validacao === "descartado" ? "bg-rose-500" : "bg-slate-700"
                  }`}></div>
                </div>

                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 border border-slate-700 text-slate-300 rounded font-bold uppercase tracking-wider">
                      {item.tipo}
                    </span>
                    <h3 className="text-sm font-bold text-slate-200 mt-1">{item.fonte}</h3>
                  </div>

                  <ConfidenceBadge level={item.confianca} />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-[11px] text-slate-300">
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Agência</span>
                    <span className="font-semibold block truncate">{item.agencia}</span>
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Edital</span>
                    <span className="font-semibold block truncate">{item.edital || "Não identificado"}</span>
                  </div>
                  <div className="bg-slate-900/40 p-2 rounded border border-slate-850">
                    <span className="text-[9px] text-slate-500 block">Processo</span>
                    <span className="font-semibold block font-mono text-[10px]">{item.numero_processo || "Não consta"}</span>
                  </div>
                  <div className="bg-slate-950 p-2 rounded border border-emerald-950">
                    <span className="text-[9px] text-emerald-500 block font-bold">Valor Captado</span>
                    <span className="font-bold text-emerald-400 text-xs">{item.valor}</span>
                  </div>
                </div>

                <OriginalFragment text={item.trecho_original} />

                <ActionPanel 
                  status={item.status_validacao} 
                  onConfirm={() => handleConfirm("financiamentos", item.id)}
                  onEdit={() => handleOpenEdit("financiamentos", item)}
                  onDiscard={() => handleDiscard("financiamentos", item.id)}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Right Side: Gaps & Realtime Audit Logs (3 Cols) */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* AI Gap Detection Card */}
          <div className="glow-card rounded-xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-semibold tracking-wider text-slate-300 uppercase flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                Lacunas de Informação
              </h2>
              <span className="text-xs px-2 py-0.5 bg-amber-950 text-amber-400 border border-amber-900 rounded font-semibold">
                {lacunas.filter(l => !l.resolvido).length}
              </span>
            </div>

            <div className="space-y-3.5">
              {lacunas.length === 0 ? (
                <div className="text-center py-6 text-slate-500 text-xs">
                  <CheckCircle className="w-8 h-8 text-emerald-600/80 mx-auto mb-2" />
                  Nenhuma lacuna detectada para este docente!
                </div>
              ) : (
                lacunas.map((gap) => (
                  <div 
                    key={gap.id}
                    className={`p-3 rounded-lg border transition-all duration-300 ${
                      gap.resolvido 
                        ? "bg-slate-950/40 border-slate-900/60 opacity-30" 
                        : "bg-slate-950 border-slate-850 hover:border-slate-800"
                    }`}
                  >
                    <div className="flex justify-between items-center w-full">
                      <span className="font-bold text-[10px] text-slate-400 uppercase tracking-wider">{gap.tipo_lacuna}</span>
                      {!gap.resolvido && (
                        <span className={`text-[9px] px-1.5 py-0.2 rounded font-bold uppercase tracking-wider ${
                          gap.gravidade === "alta" ? "bg-rose-950 text-rose-400 border border-rose-900" :
                          gap.gravidade === "media" ? "bg-amber-950 text-amber-400 border border-amber-900" :
                          "bg-blue-950 text-blue-400 border border-blue-900"
                        }`}>
                          {gap.gravidade}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-300 mt-2 leading-relaxed">{gap.descricao}</p>
                    
                    {!gap.resolvido && (
                      <div className="mt-2.5 pt-2 border-t border-slate-900 flex justify-between items-center">
                        <span className="text-[9px] text-slate-500 max-w-[70%] leading-snug">{gap.acao_recomendada}</span>
                        <button 
                          onClick={() => handleResolveGap(gap.id)}
                          className="py-1 px-2 bg-indigo-950/60 hover:bg-indigo-900/60 border border-indigo-800 text-[10px] text-indigo-400 font-semibold rounded transition-colors"
                        >
                          Resolver
                        </button>
                      </div>
                    )}

                    {gap.resolvido && (
                      <div className="mt-2.5 pt-2 border-t border-slate-900 flex items-center gap-1.5 text-[10px] text-emerald-500 font-bold">
                        <Check className="w-3.5 h-3.5" />
                        Resolvido
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Audit Log Card */}
          <div className="glow-card rounded-xl p-5">
            <h2 className="text-sm font-semibold tracking-wider text-slate-300 uppercase mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              Logs de Validação
            </h2>

            <div className="space-y-3 max-h-[220px] overflow-y-auto pr-1">
              {auditLogs.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  Aguardando interações humanas...
                </div>
              ) : (
                auditLogs.map((log) => (
                  <div key={log.id} className="text-[10px] bg-slate-950 p-2.5 border border-slate-900 rounded-lg flex flex-col gap-1">
                    <div className="flex justify-between items-center text-slate-500">
                      <span className={`font-bold uppercase tracking-wider px-1 py-0.2 rounded text-[8px] ${
                        log.acao === "confirmar" ? "bg-emerald-950/80 text-emerald-400 border border-emerald-900/80" :
                        log.acao === "editar" ? "bg-indigo-950/80 text-indigo-400 border border-indigo-900/80" :
                        log.acao === "descartar" ? "bg-rose-950/80 text-rose-400 border border-rose-900/80" :
                        "bg-slate-900 text-slate-400 border border-slate-800"
                      }`}>
                        {log.acao}
                      </span>
                      <span>{log.timestamp}</span>
                    </div>
                    <span className="text-slate-300 leading-normal">{log.mensagem}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
      )}

      {/* ========================================================================= */}
      {/* 📊 Aba Estatísticas */}
      {/* ========================================================================= */}
      {mainTab === "estatisticas" && (
        <main className="flex-1 p-6 space-y-6 animate-fadeIn bg-slate-950/20">
          {/* Barra de Filtros */}
          <div className="glow-card rounded-xl p-5 flex flex-wrap gap-4 items-end bg-[#0f172a]/60 border border-[#1e293b] backdrop-blur-md">
            <div className="flex-1 min-w-[200px] space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Docente</label>
              <select
                value={statsProfessorId}
                onChange={(e) => setStatsProfessorId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 outline-none p-2.5 rounded text-xs text-slate-200"
              >
                <option value="todos">Todos os Docentes</option>
                {professors.map((p) => (
                  <option key={p.id} value={p.id}>{p.nome_completo}</option>
                ))}
              </select>
            </div>

            <div className="flex-1 min-w-[200px] space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Linha de Pesquisa</label>
              <select
                value={statsLinhaPesquisaId}
                onChange={(e) => setStatsLinhaPesquisaId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 outline-none p-2.5 rounded text-xs text-slate-200"
              >
                <option value="todas">Todas as Linhas</option>
                {linhasPesquisa.map((l) => (
                  <option key={l.id} value={l.id}>{l.nome}</option>
                ))}
              </select>
            </div>

            <div className="w-[110px] space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Início</label>
              <input
                type="number"
                value={statsAnoInicio}
                onChange={(e) => setStatsAnoInicio(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 outline-none p-2.5 rounded text-xs text-slate-200"
              />
            </div>

            <div className="w-[110px] space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Fim</label>
              <input
                type="number"
                value={statsAnoFim}
                onChange={(e) => setStatsAnoFim(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 outline-none p-2.5 rounded text-xs text-slate-200"
              />
            </div>

            <button
              onClick={() => {
                // Force stats refresh
                const currentTab = mainTab;
                navigateMainTab("validacao");
                setTimeout(() => navigateMainTab(currentTab), 50);
              }}
              className="py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold text-xs shadow-lg shadow-indigo-600/10 transition-all flex items-center justify-center gap-2 min-h-[38px]"
            >
              <RefreshCw className={`w-4 h-4 ${loadingStats ? "animate-spin" : ""}`} />
              Filtrar
            </button>
          </div>

          {loadingStats ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-3">
              <RefreshCw className="w-10 h-10 text-indigo-500 animate-spin" />
              <span className="text-xs text-slate-400">Processando e computando agregações estatísticas...</span>
            </div>
          ) : statsData ? (
            <div className="space-y-6">
              {/* KPIs Highlights */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                <div className="glow-card rounded-xl p-5 border border-slate-850 flex items-center space-x-4 bg-gradient-to-br from-indigo-950/20 to-slate-900/30">
                  <div className="bg-indigo-950/80 border border-indigo-800/60 p-3 rounded-xl text-indigo-400">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Total de Produções</span>
                    <h3 className="text-2xl font-bold text-white mt-0.5">{statsData.total_producoes}</h3>
                    <span className="text-[9px] text-slate-400 block mt-0.5">Artigos, livros e capítulos</span>
                  </div>
                </div>

                <div className="glow-card rounded-xl p-5 border border-slate-850 flex items-center space-x-4 bg-gradient-to-br from-emerald-950/20 to-slate-900/30">
                  <div className="bg-emerald-950/80 border border-emerald-800/60 p-3 rounded-xl text-emerald-400">
                    <DollarSign className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Fomento Aprovado</span>
                    <h3 className="text-2xl font-bold text-emerald-400 mt-0.5">
                      {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(statsData.fomento_total?.aprovado || 0)}
                    </h3>
                    <span className="text-[9px] text-slate-400 block mt-0.5">
                      Captado de FAPEMA, CNPq, etc.
                    </span>
                  </div>
                </div>

                <div className="glow-card rounded-xl p-5 border border-slate-850 flex items-center space-x-4 bg-gradient-to-br from-purple-950/20 to-slate-900/30">
                  <div className="bg-purple-950/80 border border-purple-800/60 p-3 rounded-xl text-purple-400">
                    <BookOpen className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Projetos Ativos</span>
                    <h3 className="text-2xl font-bold text-purple-400 mt-0.5">{statsData.total_projetos}</h3>
                    <span className="text-[9px] text-slate-400 block mt-0.5">Pesquisas institucionais</span>
                  </div>
                </div>

                <div className="glow-card rounded-xl p-5 border border-slate-850 flex items-center space-x-4 bg-gradient-to-br from-amber-950/20 to-slate-900/30">
                  <div className="bg-amber-950/80 border border-amber-800/60 p-3 rounded-xl text-amber-400">
                    <AlertTriangle className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Gaps Pendentes</span>
                    <h3 className="text-2xl font-bold text-amber-400 mt-0.5">{statsData.lacunas?.pendentes || 0}</h3>
                    <span className="text-[9px] text-slate-400 block mt-0.5">
                      Taxa resolução: {statsData.lacunas?.total > 0 ? Math.round((statsData.lacunas.resolvidas / statsData.lacunas.total) * 100) : 100}%
                    </span>
                  </div>
                </div>
              </div>

              {(statsData.total_orientacoes != null) && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="glow-card rounded-xl p-4 border border-slate-850">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Orientações</span>
                    <p className="text-xl font-bold text-white mt-1">{statsData.total_orientacoes}</p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      {statsData.orientacoes_concluidas} concluídas · {statsData.orientacoes_em_andamento} em andamento
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowArtigosQualisModal(true)}
                    className="glow-card rounded-xl p-4 border border-slate-850 text-left w-full cursor-pointer transition-all hover:border-indigo-700/60 hover:bg-indigo-950/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
                    title="Abrir painel de artigos por estrato Qualis, revistas e docentes"
                  >
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Qualis (artigos)</span>
                    <p className="text-xl font-bold text-indigo-300 mt-1">
                      {Object.keys(statsData.producoes_por_qualis || {}).length} estratos
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      {Object.entries(statsData.producoes_por_qualis || {}).map(([k, v]) => `${k}: ${v}`).join(" · ") || "Sem dados"}
                      {" · clique para gráficos"}
                    </p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowPendingValidationModal(true)}
                    className="glow-card rounded-xl p-4 border border-slate-850 text-left w-full cursor-pointer transition-all hover:border-amber-700/60 hover:bg-amber-950/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500/50"
                    title="Ver fila completa de itens aguardando validação"
                  >
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Validação pendente</span>
                    <p className="text-xl font-bold text-amber-300 mt-1">
                      {Object.values(statsData.validacao_pendentes || {}).reduce((a: number, b) => a + (b as number), 0)}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      itens aguardando revisão humana · clique para abrir a fila
                    </p>
                  </button>
                </div>
              )}

              {/* Charts Section */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* 1. Evolução Histórica das Produções */}
                <div className="glow-card rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold tracking-wider text-slate-300 uppercase flex items-center gap-2 border-b border-slate-900 pb-3">
                    <Calendar className="w-4 h-4 text-indigo-400" />
                    Evolução Histórica das Produções
                  </h3>

                  {Object.keys(statsData.producoes_por_ano || {}).length === 0 ? (
                    <div className="text-center py-10 text-slate-500 text-xs">Nenhum dado histórico encontrado</div>
                  ) : (
                    <div className="w-full space-y-3 pt-2">
                      {/* Simple Pure React SVG Line Chart with Gradient */}
                      <div className="relative h-44 w-full">
                        <svg className="w-full h-full" viewBox="0 0 500 200" preserveAspectRatio="none">
                          <defs>
                            <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.4" />
                              <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.0" />
                            </linearGradient>
                          </defs>

                          {/* Grid Lines */}
                          <line x1="0" y1="50" x2="500" y2="50" stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.5" />
                          <line x1="0" y1="100" x2="500" y2="100" stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.5" />
                          <line x1="0" y1="150" x2="500" y2="150" stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.5" />

                          {(() => {
                            const years = Object.keys(statsData.producoes_por_ano);
                            const values = Object.values(statsData.producoes_por_ano) as number[];
                            const maxVal = Math.max(...values, 5);
                            
                            const points = years.map((yr, idx) => {
                              const x = (idx / (years.length - 1)) * 480 + 10;
                              const y = 170 - (values[idx] / maxVal) * 140;
                              return { x, y, value: values[idx], year: yr };
                            });

                            const linePath = points.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
                            const areaPath = `${linePath} L ${points[points.length - 1].x} 170 L ${points[0].x} 170 Z`;

                            return (
                              <>
                                {/* Filled Area */}
                                <path d={areaPath} fill="url(#lineGrad)" />
                                {/* Smooth Stroke Line */}
                                <path d={linePath} fill="none" stroke="#6366f1" strokeWidth="3.5" strokeLinecap="round" />

                                {/* Dots */}
                                {points.map((p, idx) => (
                                  <g key={idx} className="group cursor-pointer">
                                    <circle
                                      cx={p.x}
                                      cy={p.y}
                                      r="6"
                                      fill="#4f46e5"
                                      stroke="#ffffff"
                                      strokeWidth="2"
                                      className="transition-all duration-200 hover:r-8"
                                    />
                                    <circle
                                      cx={p.x}
                                      cy={p.y}
                                      r="12"
                                      fill="#6366f1"
                                      fillOpacity="0"
                                      className="hover:fill-opacity-20 transition-all duration-200"
                                    />
                                    {/* Mini tooltip for each dot */}
                                    <text
                                      x={p.x}
                                      y={p.y - 12}
                                      fill="#a5b4fc"
                                      fontSize="10"
                                      fontWeight="bold"
                                      textAnchor="middle"
                                      className="opacity-90 bg-slate-900"
                                    >
                                      {p.value}
                                    </text>
                                  </g>
                                ))}
                              </>
                            );
                          })()}
                        </svg>
                      </div>

                      {/* X Axis Labels */}
                      <div className="flex justify-between px-2 text-[10px] text-slate-500 font-bold">
                        {Object.keys(statsData.producoes_por_ano).map((yr) => (
                          <span key={yr}>{yr}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* 2. Proporção por Tipo de Produção */}
                <div className="glow-card rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold tracking-wider text-slate-300 uppercase flex items-center gap-2 border-b border-slate-900 pb-3">
                    <FileText className="w-4 h-4 text-indigo-400" />
                    Mix de Produção Acadêmica
                  </h3>

                  {Object.keys(statsData.producoes_por_tipo || {}).length === 0 ? (
                    <div className="text-center py-10 text-slate-500 text-xs">Nenhuma produção registrada</div>
                  ) : (
                    <div className="space-y-4 pt-1">
                      {(() => {
                        const types = Object.keys(statsData.producoes_por_tipo);
                        const values = Object.values(statsData.producoes_por_tipo) as number[];
                        const total = values.reduce((a, b) => a + b, 0);

                        return types.map((type, idx) => {
                          const val = values[idx];
                          const pct = Math.round((val / total) * 100);
                          
                          // Custom colors based on index
                          const barColors = [
                            "from-indigo-600 to-indigo-400",
                            "from-purple-600 to-purple-400",
                            "from-pink-600 to-pink-400",
                            "from-emerald-600 to-emerald-400",
                            "from-amber-600 to-amber-400"
                          ];

                          return (
                            <div key={type} className="space-y-1.5">
                              <div className="flex justify-between items-center text-xs">
                                <span className="capitalize font-semibold text-slate-300 flex items-center gap-1.5">
                                  <span className={`w-2.5 h-2.5 rounded bg-gradient-to-br ${barColors[idx % barColors.length]}`}></span>
                                  {type === "artigo" ? "Artigos de Periódicos" 
                                   : type === "livro" ? "Livros Publicados" 
                                   : type === "capitulo" ? "Capítulos de Livros" 
                                   : type === "evento" ? "Trabalhos em Eventos" 
                                   : type}
                                </span>
                                <span className="font-bold text-slate-400">
                                  {val} <span className="text-[10px] text-slate-500 font-normal">({pct}%)</span>
                                </span>
                              </div>
                              <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-900">
                                <div 
                                  className={`bg-gradient-to-r ${barColors[idx % barColors.length]} h-full rounded-full transition-all duration-1000`}
                                  style={{ width: `${pct}%` }}
                                ></div>
                              </div>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  )}
                </div>

                {/* 3. Distribuição de Fomento por Agência Financiadora */}
                <div className="glow-card rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold tracking-wider text-slate-300 uppercase flex items-center gap-2 border-b border-slate-900 pb-3">
                    <Award className="w-4 h-4 text-indigo-400" />
                    Distribuição de Fomento por Agência
                  </h3>

                  {Object.keys(statsData.fomento_por_agencia || {}).length === 0 ? (
                    <div className="text-center py-10 text-slate-500 text-xs">Nenhum fomento/recurso mapeado</div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                      {/* Premium Circle Donut Chart */}
                      <div className="flex justify-center py-2">
                        {(() => {
                          const agencies = Object.keys(statsData.fomento_por_agencia);
                          const values = Object.values(statsData.fomento_por_agencia) as number[];
                          const total = values.reduce((a, b) => a + b, 0);

                          if (total === 0) return <div className="text-xs text-slate-500 font-semibold">R$ 0,00 Aprovados</div>;

                          let cumulativePercent = 0;
                          const slices = agencies.map((ag, idx) => {
                            const val = values[idx];
                            const percent = (val / total) * 100;
                            const offset = cumulativePercent;
                            cumulativePercent += percent;
                            return { percent, offset, name: ag };
                          });

                          const colorPalette = ["#4f46e5", "#a855f7", "#ec4899", "#10b981", "#f59e0b"];

                          return (
                            <div className="relative w-44 h-44">
                              <svg viewBox="0 0 42 42" className="w-full h-full transform -rotate-90">
                                <circle cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#0f172a" strokeWidth="4.5" />
                                {slices.map((slice, index) => (
                                  <circle
                                    key={slice.name}
                                    cx="21"
                                    cy="21"
                                    r="15.91549430918954"
                                    fill="transparent"
                                    stroke={colorPalette[index % colorPalette.length]}
                                    strokeWidth="4.8"
                                    strokeDasharray={`${slice.percent} ${100 - slice.percent}`}
                                    strokeDashoffset={100 - slice.offset}
                                    className="transition-all duration-1000 ease-out"
                                  />
                                ))}
                              </svg>
                              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                                <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Aprovado</span>
                                <span className="text-sm font-extrabold text-white mt-0.5">
                                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(total)}
                                </span>
                              </div>
                            </div>
                          );
                        })()}
                      </div>

                      {/* Legend */}
                      <div className="space-y-3">
                        {(() => {
                          const agencies = Object.keys(statsData.fomento_por_agencia);
                          const values = Object.values(statsData.fomento_por_agencia) as number[];
                          const total = values.reduce((a, b) => a + b, 0);
                          const colorPalette = ["#4f46e5", "#a855f7", "#ec4899", "#10b981", "#f59e0b"];

                          return agencies.map((ag, idx) => {
                            const val = values[idx];
                            const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                            return (
                              <div key={ag} className="flex justify-between items-center bg-slate-950/40 p-2 border border-slate-900 rounded-lg animate-fadeIn">
                                <div className="flex items-center gap-2">
                                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: colorPalette[idx % colorPalette.length] }}></span>
                                  <span className="text-[11px] font-bold text-slate-300">{ag}</span>
                                </div>
                                <div className="text-[11px] font-bold text-slate-400 text-right">
                                  <span>{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)}</span>
                                  <span className="text-[9px] text-slate-500 font-normal block">{pct}% do fomento</span>
                                </div>
                              </div>
                            );
                          });
                        })()}
                      </div>
                    </div>
                  )}
                </div>

                {/* 4. Gravidade de Alertas & Gaps */}
                <div className="glow-card rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold tracking-wider text-slate-300 uppercase flex items-center gap-2 border-b border-slate-900 pb-3">
                    <AlertTriangle className="w-4 h-4 text-indigo-400" />
                    Gravidade de Lacunas Pendentes
                  </h3>

                  {statsData.lacunas?.total === 0 ? (
                    <div className="text-center py-10 text-slate-500 text-xs">Nenhuma lacuna registrada no sistema</div>
                  ) : (
                    <div className="space-y-4 pt-1">
                      {/* Visual summary of gaps */}
                      <div className="flex bg-slate-950 h-4.5 rounded-full overflow-hidden border border-slate-900 p-0.5">
                        {(() => {
                          const high = statsData.lacunas?.por_gravidade?.alta || 0;
                          const med = statsData.lacunas?.por_gravidade?.media || 0;
                          const low = statsData.lacunas?.por_gravidade?.baixa || 0;
                          const total = high + med + low || 1;

                          const pctH = (high / total) * 100;
                          const pctM = (med / total) * 100;
                          const pctL = (low / total) * 100;

                          return (
                            <>
                              {high > 0 && <div className="bg-rose-500 h-full rounded-l-full" style={{ width: `${pctH}%` }} title={`Alta: ${high}`}></div>}
                              {med > 0 && <div className="bg-amber-500 h-full" style={{ width: `${pctM}%` }} title={`Média: ${med}`}></div>}
                              {low > 0 && <div className="bg-blue-500 h-full rounded-r-full" style={{ width: `${pctL}%` }} title={`Baixa: ${low}`}></div>}
                            </>
                          );
                        })()}
                      </div>

                      {/* Detail list */}
                      <div className="grid grid-cols-3 gap-3">
                        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-900 text-center">
                          <span className="text-[10px] text-rose-400 font-bold uppercase tracking-wider block">Gravidade Alta</span>
                          <span className="text-xl font-extrabold text-white block mt-1">{statsData.lacunas?.por_gravidade?.alta || 0}</span>
                          <span className="text-[9px] text-slate-500 mt-0.5 block">Exige ação imediata</span>
                        </div>

                        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-900 text-center">
                          <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider block">Gravidade Média</span>
                          <span className="text-xl font-extrabold text-white block mt-1">{statsData.lacunas?.por_gravidade?.media || 0}</span>
                          <span className="text-[9px] text-slate-500 mt-0.5 block">Revisão recomendada</span>
                        </div>

                        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-900 text-center">
                          <span className="text-[10px] text-blue-400 font-bold uppercase tracking-wider block">Gravidade Baixa</span>
                          <span className="text-xl font-extrabold text-white block mt-1">{statsData.lacunas?.por_gravidade?.baixa || 0}</span>
                          <span className="text-[9px] text-slate-500 mt-0.5 block">Ajustes informacionais</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

              </div>
            </div>
          ) : (
            <div className="text-center py-16 text-slate-500 text-xs">Nenhum dado analítico pôde ser computado</div>
          )}
        </main>
      )}

      {/* ========================================================================= */}
      {/* 🤖 Aba Gerador de Relatórios com IA */}
      {/* ========================================================================= */}
      {mainTab === "relatorios" && (
        <main className="report-print-layout flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 animate-fadeIn bg-slate-950/20">
          
          {/* Lado Esquerdo: Configuração da Geração (4 colunas) */}
          <div className="no-print lg:col-span-4 space-y-6">
            <div className="glow-card rounded-xl p-5 space-y-5 bg-[#0f172a]/60 border border-[#1e293b] backdrop-blur-md">
              <div className="flex items-center space-x-2 border-b border-slate-900 pb-3">
                <BarChart2 className="w-5 h-5 text-indigo-400 animate-pulse" />
                <h2 className="text-sm font-bold tracking-wider text-slate-300 uppercase">Configurar Relatório</h2>
              </div>

              {/* Filtros Contextuais */}
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Docente Alvo</label>
                  <select
                    value={reportProfessorId}
                    onChange={(e) => setReportProfessorId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 outline-none p-2.5 rounded text-xs text-slate-200"
                  >
                    <option value="todos">Todos os Docentes (Geral)</option>
                    {professors.map((p) => (
                      <option key={p.id} value={p.id}>{p.nome_completo}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Linha de Pesquisa</label>
                  <select
                    value={reportLinhaPesquisaId}
                    onChange={(e) => setReportLinhaPesquisaId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 outline-none p-2.5 rounded text-xs text-slate-200"
                  >
                    <option value="todas">Todas as Linhas</option>
                    {linhasPesquisa.map((l) => (
                      <option key={l.id} value={l.id}>{l.nome}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Início</label>
                    <input
                      type="number"
                      value={reportAnoInicio}
                      onChange={(e) => setReportAnoInicio(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 outline-none p-2.5 rounded text-xs text-slate-200"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Fim</label>
                    <input
                      type="number"
                      value={reportAnoFim}
                      onChange={(e) => setReportAnoFim(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 outline-none p-2.5 rounded text-xs text-slate-200"
                    />
                  </div>
                </div>
              </div>

              {/* Templates Rápidos */}
              <div className="space-y-2.5 pt-2 border-t border-slate-900">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Presets e Templates Rápidos</label>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => setReportPrompt("Gere um relatório abrangente contendo o balanço de fomento recebido (CNPq, CAPES, FAPEMA), discriminando os valores por agência e o percentual de captação de cada docente.")}
                    className="w-full text-left p-2 bg-slate-950 border border-slate-850 hover:border-indigo-900 rounded text-[10.5px] text-slate-400 hover:text-indigo-300 font-medium transition-colors"
                  >
                    💰 Balanço de Fomento & Captação
                  </button>
                  <button
                    onClick={() => setReportPrompt("Redija uma síntese acadêmica detalhada das produções, destacando os artigos de periódicos mais relevantes e a aderência deles à linha de pesquisa correspondente.")}
                    className="w-full text-left p-2 bg-slate-950 border border-slate-850 hover:border-indigo-900 rounded text-[10.5px] text-slate-400 hover:text-indigo-300 font-medium transition-colors"
                  >
                    📚 Síntese de Periódicos & Publicações
                  </button>
                  <button
                    onClick={() => setReportPrompt("Gere um sumário executivo focado nos alertas e gaps de informação nos currículos. Explique quais são as principais inconsistências encontradas e forneça recomendações para a coordenação resolvê-las.")}
                    className="w-full text-left p-2 bg-slate-950 border border-slate-850 hover:border-indigo-900 rounded text-[10.5px] text-slate-400 hover:text-indigo-300 font-medium transition-colors"
                  >
                    ⚠️ Sumário Executivo de Gaps/Incoerências
                  </button>
                </div>
              </div>

              {/* Instruções do Coordenador */}
              <div className="space-y-2 pt-2 border-t border-slate-900">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">O que você precisa focar no relatório?</label>
                <textarea
                  rows={4}
                  value={reportPrompt}
                  onChange={(e) => setReportPrompt(e.target.value)}
                  placeholder="Ex: Faça uma análise comparativa do fomento ativo e o volume de publicações recentes em periódicos..."
                  className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 focus:border-indigo-600 outline-none p-2.5 rounded text-xs text-slate-200 placeholder-slate-600 resize-none leading-relaxed"
                />
              </div>

              <button
                disabled={generatingReport}
                onClick={handleGenerateReport}
                className={`w-full py-3 px-4 rounded-xl font-bold text-xs transition-all flex items-center justify-center gap-2 ${
                  generatingReport
                    ? "bg-indigo-900/50 text-indigo-400 border border-indigo-850 cursor-not-allowed"
                    : "bg-indigo-600 text-white hover:bg-indigo-500 hover:scale-[1.01] shadow-lg shadow-indigo-600/20 cursor-pointer active:scale-[0.99]"
                }`}
              >
                {generatingReport ? (
                  <>
                    <RefreshCw className="w-4.5 h-4.5 animate-spin" />
                    Gerando Relatório com IA...
                  </>
                ) : (
                  <>
                    <Award className="w-4.5 h-4.5" />
                    Gerar Relatório Executivo
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Lado Direito: Visualizador de Markdown Executivo (8 colunas) */}
          <div className="report-print-panel lg:col-span-8 flex flex-col h-full min-h-[580px] space-y-6">
            <div className="glow-card rounded-xl p-5 flex flex-col flex-1 bg-[#0f172a]/60 border border-[#1e293b] backdrop-blur-md">
              
              <div className="no-print flex justify-between items-center border-b border-slate-900 pb-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-200 tracking-wider uppercase">Relatório Gerado por IA</h3>
                  {reportModelUsed && (
                    <span className="text-[10px] text-indigo-400 font-bold font-mono block mt-0.5">
                      Modelo: {reportModelUsed}
                    </span>
                  )}
                </div>

                {reportText && !generatingReport && (
                  <div className="flex gap-2">
                    <button
                      onClick={copyToClipboard}
                      className="py-1.5 px-3 bg-slate-950 border border-slate-850 hover:border-slate-750 text-xs font-semibold text-slate-300 hover:text-white rounded-lg transition-colors flex items-center gap-1.5"
                      title="Copiar Relatório"
                    >
                      <Check className="w-3.5 h-3.5" />
                      Copiar
                    </button>
                    <button
                      onClick={downloadMarkdown}
                      className="py-1.5 px-3 bg-slate-950 border border-slate-850 hover:border-slate-750 text-xs font-semibold text-slate-300 hover:text-white rounded-lg transition-colors flex items-center gap-1.5"
                      title="Baixar Markdown (.md)"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Baixar .MD
                    </button>
                    <button
                      onClick={handlePrintReport}
                      className="py-1.5 px-3 bg-indigo-950/60 border border-indigo-900 hover:bg-indigo-900 text-xs font-semibold text-indigo-400 hover:text-indigo-200 rounded-lg transition-all flex items-center gap-1.5"
                      title="Imprimir ou salvar como PDF (na própria página)"
                    >
                      <Award className="w-3.5 h-3.5" />
                      Imprimir PDF
                    </button>
                  </div>
                )}
              </div>

              {/* Workspace Content Area */}
              <div className="flex-1 flex flex-col justify-center mt-5 overflow-y-auto max-h-[500px] pr-1 print:max-h-none print:overflow-visible">
                {generatingReport ? (
                  <div className="no-print flex flex-col items-center justify-center py-20 space-y-6 text-center">
                    <div className="relative">
                      <div className="w-14 h-14 rounded-full border-4 border-indigo-950 border-t-indigo-500 animate-spin"></div>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <BarChart2 className="w-6 h-6 text-indigo-400 animate-pulse" />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="text-sm font-bold text-slate-300">Inteligência Artificial Pensando...</h4>
                      <p className="text-xs text-slate-500 max-w-[280px] mx-auto leading-normal">
                        Estamos consolidando os indicadores e gerando o parecer analítico.
                      </p>
                    </div>

                    {/* Generation Logs Console */}
                    <div className="w-full max-w-sm bg-slate-950 border border-slate-900 rounded-lg p-3 text-left font-mono text-[10px] text-slate-400 space-y-1.5 h-28 overflow-y-auto">
                      {reportLogs.map((log, index) => (
                        <div key={index} className="flex gap-2">
                          <span className="text-indigo-500 font-bold select-none">&gt;</span>
                          <span className={index === reportLogs.length - 1 ? "text-indigo-400 animate-pulse font-semibold" : ""}>{log}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : reportText ? (
                  <div
                    id="report-print-root"
                    className="bg-slate-950/45 p-6 rounded-xl border border-slate-900/60 leading-relaxed text-slate-300 text-xs overflow-wrap-break text-left"
                  >
                    <div className="print-only mb-4 pb-3 border-b border-slate-300 text-slate-800 text-[10pt]">
                      <p className="font-bold text-indigo-900 text-sm">PPGCOMDATA — Relatório analítico</p>
                      <p className="mt-1 text-slate-600">
                        {reportProfessorId === "todos"
                          ? "Todos os docentes"
                          : professors.find((p) => p.id === reportProfessorId)?.nome_completo}
                        {" · "}
                        {reportAnoInicio}—{reportAnoFim}
                        {reportModelUsed ? ` · ${reportModelUsed}` : ""}
                      </p>
                    </div>
                    <SimpleMarkdownRenderer content={reportText} />
                  </div>
                ) : (
                  <div className="no-print text-center py-20 text-slate-500 text-xs space-y-3">
                    <Award className="w-12 h-12 text-slate-700 mx-auto" />
                    <p className="font-semibold text-slate-400">Pronto para gerar pareceres e sínteses analíticas!</p>
                    <p className="max-w-xs mx-auto text-slate-500 leading-normal">
                      Selecione os filtros desejados, escolha um template rápido ou redija uma orientação personalizada para iniciar o pipeline de IA.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      )}

      {/* 📝 Edit Item Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl shadow-2xl max-w-lg w-full overflow-hidden glow-card">
            <div className="border-b border-[#1e293b] p-4 flex justify-between items-center">
              <h3 className="font-bold text-sm text-slate-200 flex items-center gap-2">
                <Edit2 className="w-4.5 h-4.5 text-indigo-400" />
                Editar e Corrigir {({
                  projetos: "Projeto",
                  eventos: "Evento",
                  producoes: "Produção",
                  financiamentos: "Financiamento",
                  orientacoes: "Orientação",
                  formacoes_academicas: "Formação",
                  producoes_tecnicas: "Produção Técnica",
                  premios: "Prêmio",
                  grupos_pesquisa: "Grupo de Pesquisa",
                } as Record<EntityTab, string>)[editingItem.type as EntityTab] || "Registro"}
              </h3>
              <button 
                onClick={() => setEditingItem(null)}
                className="text-slate-400 hover:text-slate-200 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="p-5 space-y-4 max-h-[60vh] overflow-y-auto">
              
              {/* If Project */}
              {editingItem.type === "projetos" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Título do Projeto</label>
                    <input 
                      type="text" 
                      value={editingItem.item.titulo} 
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, titulo: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 focus:border-indigo-600 outline-none p-2.5 rounded text-xs text-slate-200"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Início</label>
                      <input 
                        type="number" 
                        value={editingItem.item.ano_inicio} 
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, ano_inicio: parseInt(e.target.value) } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Fim</label>
                      <input 
                        type="number" 
                        value={editingItem.item.ano_fim || ""} 
                        placeholder="Atual"
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, ano_fim: e.target.value ? parseInt(e.target.value) : null } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Descrição</label>
                    <textarea 
                      rows={3}
                      value={editingItem.item.descricao} 
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, descricao: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 focus:border-indigo-600 outline-none p-2.5 rounded text-xs text-slate-200"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Agência de Fomento</label>
                    <input 
                      type="text" 
                      value={editingItem.item.agencia_fomento || ""} 
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, agencia_fomento: e.target.value, financiamento_mencionado: !!e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                </>
              )}

              {/* If Event */}
              {editingItem.type === "eventos" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Nome do Evento</label>
                    <input 
                      type="text" 
                      value={editingItem.item.nome_evento} 
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, nome_evento: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Trabalho Apresentado</label>
                    <input 
                      type="text" 
                      value={editingItem.item.titulo_trabalho} 
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, titulo_trabalho: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano</label>
                      <input 
                        type="number" 
                        value={editingItem.item.ano} 
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, ano: parseInt(e.target.value) } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Cidade</label>
                      <input 
                        type="text" 
                        value={editingItem.item.cidade} 
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, cidade: e.target.value } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">País</label>
                      <input 
                        type="text" 
                        value={editingItem.item.pais} 
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, pais: e.target.value } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* If Production */}
              {editingItem.type === "producoes" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Título</label>
                    <input 
                      type="text" 
                      value={editingItem.item.titulo} 
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, titulo: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Veículo / Revista / Editora</label>
                    <input 
                      type="text" 
                      value={editingItem.item.veiculo} 
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, veiculo: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano</label>
                      <input 
                        type="number" 
                        value={editingItem.item.ano} 
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, ano: parseInt(e.target.value) } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1 col-span-2">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">DOI</label>
                      <input 
                        type="text" 
                        value={editingItem.item.doi || ""} 
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, doi: e.target.value || null } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none font-mono"
                      />
                    </div>
                  </div>
                </>
              )}

              {editingItem.type === "producoes_tecnicas" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Título</label>
                    <input
                      type="text"
                      value={editingItem.item.titulo}
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, titulo: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Tipo</label>
                      <input
                        type="text"
                        value={editingItem.item.tipo}
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, tipo: e.target.value } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano</label>
                      <input
                        type="number"
                        value={editingItem.item.ano ?? ""}
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, ano: e.target.value ? parseInt(e.target.value) : null } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Instituição</label>
                    <input
                      type="text"
                      value={editingItem.item.instituicao || ""}
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, instituicao: e.target.value || null } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Descrição</label>
                    <textarea
                      rows={2}
                      value={editingItem.item.descricao || ""}
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, descricao: e.target.value || null } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                </>
              )}

              {editingItem.type === "premios" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Nome do prêmio / título</label>
                    <input
                      type="text"
                      value={editingItem.item.nome}
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, nome: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Tipo</label>
                      <input
                        type="text"
                        value={editingItem.item.tipo}
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, tipo: e.target.value } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano</label>
                      <input
                        type="number"
                        value={editingItem.item.ano ?? ""}
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, ano: e.target.value ? parseInt(e.target.value) : null } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Instituição concedente</label>
                    <input
                      type="text"
                      value={editingItem.item.instituicao_concedente || ""}
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, instituicao_concedente: e.target.value || null } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                </>
              )}

              {editingItem.type === "grupos_pesquisa" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Nome do grupo</label>
                    <input
                      type="text"
                      value={editingItem.item.nome_grupo}
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, nome_grupo: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Papel</label>
                      <input
                        type="text"
                        value={editingItem.item.papel}
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, papel: e.target.value } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Código DGP</label>
                      <input
                        type="text"
                        value={editingItem.item.codigo_dgp || ""}
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, codigo_dgp: e.target.value || null } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none font-mono"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Linha temática</label>
                    <input
                      type="text"
                      value={editingItem.item.linha_tematica || ""}
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, linha_tematica: e.target.value || null } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Instituição</label>
                    <input
                      type="text"
                      value={editingItem.item.instituicao || ""}
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, instituicao: e.target.value || null } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                </>
              )}

              {/* If Funding */}
              {editingItem.type === "financiamentos" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Fonte de Recurso</label>
                    <input 
                      type="text" 
                      value={editingItem.item.fonte} 
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, fonte: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Agência de Fomento</label>
                    <input 
                      type="text" 
                      value={editingItem.item.agencia} 
                      onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, agencia: e.target.value } })}
                      className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Número Processo / Edital</label>
                      <input 
                        type="text" 
                        value={editingItem.item.numero_processo || ""} 
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, numero_processo: e.target.value || null } })}
                        className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none font-mono"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-emerald-500">Valor Captado</label>
                      <input 
                        type="text" 
                        value={editingItem.item.valor} 
                        onChange={(e) => setEditingItem({ ...editingItem, item: { ...editingItem.item, valor: e.target.value } })}
                        className="w-full bg-slate-950 border border-emerald-950 p-2.5 rounded text-xs text-slate-200 outline-none font-bold text-emerald-400"
                      />
                    </div>
                  </div>
                </>
              )}

            </div>

            <div className="border-t border-[#1e293b] p-4 flex justify-end gap-3 bg-[#0f172a]/55">
              <button 
                onClick={() => setEditingItem(null)}
                className="py-1.5 px-3 bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-400 rounded-lg hover:text-slate-200 transition-colors"
              >
                Cancelar
              </button>
              <button 
                onClick={handleSaveEdit}
                className="py-1.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white rounded-lg shadow-lg shadow-indigo-600/10 transition-all flex items-center gap-1.5"
              >
                <Check className="w-4 h-4" />
                Salvar & Validar
              </button>
            </div>
          </div>
        </div>
      )}

      <PendingValidationModal
        open={showPendingValidationModal}
        onClose={() => setShowPendingValidationModal(false)}
        professors={professors}
        linhasPesquisa={linhasPesquisa}
        statsProfessorId={statsProfessorId}
        statsLinhaPesquisaId={statsLinhaPesquisaId}
        breakdown={statsData?.validacao_pendentes}
        onReview={handleReviewPendingItem}
        onGoToValidation={handleGoToValidationTab}
      />

      <ArtigosQualisModal
        open={showArtigosQualisModal}
        onClose={() => setShowArtigosQualisModal(false)}
        statsProfessorId={statsProfessorId}
        statsLinhaPesquisaId={statsLinhaPesquisaId}
        statsAnoInicio={statsAnoInicio}
        statsAnoFim={statsAnoFim}
        previewPorQualis={statsData?.producoes_por_qualis}
      />
    </div>
  );
}

