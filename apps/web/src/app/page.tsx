"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  FileText, Upload, Check, Edit2, Trash2, AlertTriangle, 
  HelpCircle, CheckCircle, RefreshCw, BarChart2, Plus, 
  BookOpen, Calendar, DollarSign, Eye, EyeOff, Award, Clock, ArrowRight, UserPlus, Info
} from "lucide-react";

// Mock types matching the SQLModel schemas
interface Professor {
  id: string;
  nome_completo: string;
  linha: string;
  tipo: string;
  status: "pendente" | "processado" | "validado";
  ultimo_upload?: string;
}

interface Projeto {
  id: string;
  titulo: string;
  tipo: string;
  situacao: string;
  ano_inicio: number;
  ano_fim: number | null;
  descricao: string;
  papel_docente: string;
  instituicoes: string;
  financiamento_mencionado: boolean;
  agencia_fomento: string | null;
  confianca_ia: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

interface Evento {
  id: string;
  nome_evento: string;
  ano: number;
  cidade: string;
  pais: string;
  tipo_participacao: string;
  titulo_trabalho: string;
  financiamento_mencionado: boolean;
  fonte_financiamento: string | null;
  confianca_ia: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

interface Producao {
  id: string;
  tipo: string;
  titulo: string;
  ano: number;
  veiculo: string;
  doi: string | null;
  issn: string | null;
  confianca_ia: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

interface Financiamento {
  id: string;
  tipo: string;
  fonte: string;
  agencia: string;
  edital: string | null;
  numero_processo: string | null;
  valor: string;
  ano: number;
  confianca: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

interface AlertaLacuna {
  id: string;
  tipo_lacuna: string;
  descricao: string;
  gravidade: "alta" | "media" | "baixa";
  acao_recomendada: string;
  resolvido: boolean;
}

interface LogAudit {
  id: string;
  acao: string;
  mensagem: string;
  timestamp: string;
}

export default function Dashboard() {
  // Connection state
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [processingStep, setProcessingStep] = useState<string>("");
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // Dynamic API URL detection
  const [apiUrl, setApiUrl] = useState<string>("http://localhost:8000/api/v1");

  // App core state
  const [professors, setProfessors] = useState<Professor[]>([
    { id: "1", nome_completo: "Prof. Dr. Lucas Reino", linha: "Comunicação e Cultura Digital", tipo: "Permanente", status: "pendente" },
    { id: "2", nome_completo: "Profª. Drª. Amanda Souza", linha: "Mídia, Política e Sociedade", tipo: "Permanente", status: "validado" },
    { id: "3", nome_completo: "Prof. Dr. Carlos Alberto", linha: "Processos de Recepção de Mídia", tipo: "Colaborador", status: "processado" },
  ]);
  const [selectedProfId, setSelectedProfId] = useState<string>("1");
  const [activeTab, setActiveTab] = useState<"projetos" | "eventos" | "producoes" | "financiamentos">("projetos");

  // Selection for edit
  const [editingItem, setEditingItem] = useState<{ type: string; item: any } | null>(null);

  // Core Data Lists (loaded from selected professor)
  const [projetos, setProjetos] = useState<Projeto[]>([]);
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [producoes, setProducoes] = useState<Producao[]>([]);
  const [financiamentos, setFinanciamentos] = useState<Financiamento[]>([]);
  const [lacunas, setLacunas] = useState<AlertaLacuna[]>([]);
  const [auditLogs, setAuditLogs] = useState<LogAudit[]>([]);

  // Form states
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize and check API
  useEffect(() => {
    const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    const detectedUrl = `http://${host}:8000/api/v1`;
    const checkUrl = `http://${host}:8000/`;
    setApiUrl(detectedUrl);

    fetch(checkUrl)
      .then(res => res.json())
      .then(() => setApiConnected(true))
      .catch(() => {
        setApiConnected(false);
        console.log("Servidor FastAPI offline, utilizando dados simulados premium.");
      });
  }, []);

  // Fetch all professors when API is connected
  useEffect(() => {
    if (!apiConnected) return;

    fetch(`${apiUrl}/professores/`)
      .then(res => {
        if (!res.ok) throw new Error("Erro ao carregar docentes");
        return res.json();
      })
      .then((data: any[]) => {
        const mapped = data.map(p => ({
          id: p.id,
          nome_completo: p.nome_completo,
          linha: p.linha_pesquisa ? p.linha_pesquisa.nome : "Comunicação e Cultura Digital",
          tipo: p.tipo_docente || "Permanente",
          status: p.status ? "validado" : "pendente"
        }));
        
        if (mapped.length > 0) {
          setProfessors(mapped);
          // Set first professor as selected if the current selected isn't in the list
          if (!mapped.some(p => p.id === selectedProfId)) {
            setSelectedProfId(mapped[0].id);
          }
        }
      })
      .catch(err => {
        console.error("Falha ao buscar docentes da API:", err);
      });
  }, [apiConnected, apiUrl]);

  // Load teacher specific data on select (API or Mock fallback)
  useEffect(() => {
    if (!selectedProfId) return;

    if (apiConnected) {
      setLoading(true);
      fetch(`${apiUrl}/validacao/pendentes?professor_id=${selectedProfId}`)
        .then(res => {
          if (!res.ok) throw new Error("Erro ao carregar dados do docente");
          return res.json();
        })
        .then((data: any) => {
          setProjetos(data.projetos || []);
          setEventos(data.eventos || []);
          setProducoes(data.producoes || []);
          setFinanciamentos(data.financiamentos || []);
          setLacunas(data.lacunas || []);
          setLoading(false);
        })
        .catch(err => {
          console.error("Falha ao buscar dados do docente:", err);
          setLoading(false);
        });
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
    }

    if (apiConnected) {
      fetch(`${apiUrl}/validacao/${type}/${id}/confirmar`, { method: "POST" })
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
    }

    if (apiConnected) {
      fetch(`${apiUrl}/validacao/${type}/${id}/descartar`, { method: "POST" })
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
      fetch(`${apiUrl}/validacao/${type}/${item.id}/editar`, {
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
          }
          addAuditLog("editar", `[Real DB] Editou e Validou ${type.slice(0, -2)}: "${(item.titulo || item.nome_evento || item.fonte).slice(0, 45)}..."`);
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
    }

    addAuditLog("editar", `Editou e Validou ${type.slice(0, -2)}: "${(item.titulo || item.nome_evento || item.fonte).slice(0, 45)}..."`);
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
      fetch(`${apiUrl}/validacao/lacunas/${gapId}/resolver`, { method: "POST" })
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
        const uploadRes = await fetch(`${apiUrl}/uploads/`, {
          method: "POST",
          body: formData
        });
        if (!uploadRes.ok) throw new Error("Erro no upload do arquivo.");
        const uploadData = await uploadRes.json();
        
        setUploadProgress(50);
        setProcessingStep("Processando e extraindo dados com IA...");

        const processRes = await fetch(`${apiUrl}/uploads/${uploadData.id}/processar`, {
          method: "POST"
        });
        if (!processRes.ok) throw new Error("Erro no processamento do arquivo.");
        const processData = await processRes.json();

        setUploadProgress(100);
        setIsProcessing(false);
        setProcessingStep("");
        setSelectedFile(null);
        addAuditLog("processamento", `[Real DB] Lattes processado! Extraídos: ${processData.extração_ia?.projetos_extraidos || 0} projetos, ${processData.extração_ia?.producoes_extraidas || 0} produções.`);
        
        // Reload teacher data to show the new items
        fetch(`${apiUrl}/validacao/pendentes?professor_id=${selectedProfId}`)
          .then(res => res.json())
          .then(data => {
            setProjetos(data.projetos || []);
            setEventos(data.eventos || []);
            setProducoes(data.producoes || []);
            setFinanciamentos(data.financiamentos || []);
            setLacunas(data.lacunas || []);
          });
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
      setProcessingStep("IA Gemini mapeando Projetos, Produções e Auxílios...");
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

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      {/* 🚀 Header */}
      <header className="border-b border-[#1e293b] bg-[#0f172a]/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-indigo-600 p-2 rounded-lg text-white shadow-lg shadow-indigo-600/20">
            <BarChart2 className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              PPGCOM<span className="text-indigo-400">DATA</span>
              <span className="text-xs px-2 py-0.5 bg-indigo-950 border border-indigo-800 text-indigo-300 font-medium rounded-full">
                v1.0.0
              </span>
            </h1>
            <p className="text-xs text-slate-400">Gestão e Análise de Indicadores Docentes</p>
          </div>
        </div>

        {/* API connection indicator */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-full text-xs">
            <span className={`w-2 h-2 rounded-full ${apiConnected ? "bg-emerald-500 animate-ping" : "bg-amber-500"}`}></span>
            <span className="text-slate-300">
              {apiConnected ? "API Conectada (FastAPI)" : "Simulação Local Premium"}
            </span>
          </div>

          <div className="text-xs text-slate-400">
            {new Date().toLocaleDateString("pt-BR", { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </div>
        </div>
      </header>

      {/* 📊 Dashboard Core */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 p-6">
        
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
            </div>
          </div>
        </div>

        {/* Center Panel: Human-in-the-Loop Validation View (6 Cols) */}
        <div className="lg:col-span-6 space-y-6">
          
          {/* Tabs navigation */}
          <div className="bg-[#0f172a]/50 p-1 border border-[#1e293b] rounded-xl flex">
            {(["projetos", "eventos", "producoes", "financiamentos"] as const).map((tab) => {
              const count = tab === "projetos" ? projetos.length 
                          : tab === "eventos" ? eventos.length 
                          : tab === "producoes" ? producoes.length 
                          : financiamentos.length;

              return (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 py-2 px-3 text-xs font-semibold rounded-lg capitalize transition-all duration-200 flex items-center justify-center gap-2 ${
                    activeTab === tab 
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/10" 
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {tab === "projetos" && <BookOpen className="w-3.5 h-3.5" />}
                  {tab === "eventos" && <Calendar className="w-3.5 h-3.5" />}
                  {tab === "producoes" && <FileText className="w-3.5 h-3.5" />}
                  {tab === "financiamentos" && <DollarSign className="w-3.5 h-3.5" />}
                  {tab}
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
                      {item.tipo_participacao}
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

            {/* PRODUCTIONS VIEW */}
            {activeTab === "producoes" && producoes.map((item) => (
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

      {/* 📝 Edit Item Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl shadow-2xl max-w-lg w-full overflow-hidden glow-card">
            <div className="border-b border-[#1e293b] p-4 flex justify-between items-center">
              <h3 className="font-bold text-sm text-slate-200 flex items-center gap-2">
                <Edit2 className="w-4.5 h-4.5 text-indigo-400" />
                Editar e Corrigir {editingItem.type === "projetos" ? "Projeto" : editingItem.type === "eventos" ? "Evento" : editingItem.type === "producoes" ? "Produção" : "Financiamento"}
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
    </div>
  );
}

// Subcomponent: Confidence Badge
function ConfidenceBadge({ level }: { level: "alta" | "media" | "baixa" }) {
  const styles = {
    alta: "bg-emerald-950/60 text-emerald-400 border-emerald-900/60",
    media: "bg-amber-950/60 text-amber-400 border-amber-900/60",
    baixa: "bg-purple-950/60 text-purple-400 border-purple-900/60"
  };

  return (
    <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider border shadow-sm ${styles[level]}`}>
      IA: {level}
    </span>
  );
}

// Subcomponent: Collapsible Original Fragment block
function OriginalFragment({ text }: { text: string }) {
  const [show, setShow] = useState<boolean>(false);

  return (
    <div className="mt-4 pt-3.5 border-t border-slate-900/80">
      <button 
        onClick={() => setShow(!show)}
        className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-indigo-400 font-semibold transition-colors outline-none"
      >
        {show ? (
          <>
            <EyeOff className="w-3.5 h-3.5" />
            Ocultar fragmento original do PDF
          </>
        ) : (
          <>
            <Eye className="w-3.5 h-3.5" />
            Visualizar fragmento original do PDF
          </>
        )}
      </button>

      {show && (
        <blockquote className="mt-2.5 p-3 rounded bg-slate-950 border-l-2 border-slate-800 text-[10.5px] italic text-slate-500 leading-relaxed font-mono">
          "{text}"
        </blockquote>
      )}
    </div>
  );
}

// Subcomponent: Action Buttons panel
function ActionPanel({ 
  status, onConfirm, onEdit, onDiscard 
}: { 
  status: "pendente" | "confirmado" | "editado" | "descartado";
  onConfirm: () => void;
  onEdit: () => void;
  onDiscard: () => void;
}) {
  return (
    <div className="mt-5 pt-3.5 border-t border-slate-900/80 flex flex-wrap justify-between items-center gap-3">
      <div className="text-[10px] flex items-center gap-1 text-slate-500">
        <Info className="w-3.5 h-3.5" />
        Status da Validação: 
        <span className={`font-bold capitalize ml-0.5 px-1 rounded ${
          status === "confirmado" ? "text-emerald-400 bg-emerald-950/30" :
          status === "editado" ? "text-indigo-400 bg-indigo-950/30" :
          status === "descartado" ? "text-rose-400 bg-rose-950/30" : "text-amber-400 bg-amber-950/30"
        }`}>
          {status}
        </span>
      </div>

      <div className="flex gap-2">
        {status !== "descartado" && (
          <button 
            onClick={onDiscard}
            className="py-1 px-2.5 bg-slate-900/60 hover:bg-rose-950/20 border border-slate-800 hover:border-rose-900/60 text-[10px] text-slate-400 hover:text-rose-400 font-semibold rounded-lg transition-all flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Descartar
          </button>
        )}
        
        <button 
          onClick={onEdit}
          className="py-1 px-2.5 bg-slate-900/60 hover:bg-indigo-950/40 border border-slate-800 hover:border-indigo-900/60 text-[10px] text-slate-400 hover:text-indigo-400 font-semibold rounded-lg transition-all flex items-center gap-1.5"
        >
          <Edit2 className="w-3.5 h-3.5" />
          Corrigir
        </button>

        {status === "pendente" && (
          <button 
            onClick={onConfirm}
            className="py-1 px-3 bg-emerald-600 hover:bg-emerald-500 text-[10px] font-bold text-white rounded-lg shadow-md shadow-emerald-950/20 transition-all flex items-center gap-1.5"
          >
            <Check className="w-3.5 h-3.5" />
            Confirmar
          </button>
        )}
      </div>
    </div>
  );
}

// Subcomponent: Empty State
function EmptyState({ tab }: { tab: string }) {
  return (
    <div className="glow-card rounded-xl p-8 text-center text-slate-500 text-xs">
      <FileText className="w-10 h-10 text-slate-600/80 mx-auto mb-3" />
      Nenhum {tab} cadastrado ou processado ainda para este docente.
    </div>
  );
}
