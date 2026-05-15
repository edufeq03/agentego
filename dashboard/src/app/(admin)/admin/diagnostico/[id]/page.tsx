"use client";

import { useEffect, useState, use } from "react";
import api from "@/lib/api";
import { 
  Activity, 
  ArrowLeft, 
  CheckCircle2, 
  XCircle, 
  RefreshCcw, 
  ShieldCheck, 
  Zap,
  Bot,
  Globe,
  Terminal as TerminalIcon,
  Clock
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface DiagnosticData {
  empresa: {
    nome: string;
    id: string;
    ativa: boolean;
    telefone: string;
  };
  integracao: {
    instancia: string;
    status_conexao: string;
    webhook_atual: string;
    webhook_esperado: string;
    webhook_ok: boolean;
    base_url_configurada: string;
  };
  configuracao_ia: {
    ok: boolean;
    nicho: string;
  };
  ultimos_eventos: Array<{
    timestamp: string;
    tipo: string;
    metadata: any;
  }>;
}

export default function DiagnosticoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [data, setData] = useState<DiagnosticData | null>(null);
  const [loading, setLoading] = useState(true);
  const [adminToken, setAdminToken] = useState("");
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    // Tenta pegar o token do localStorage se existir (ou o usuário terá que digitar)
    const savedToken = localStorage.getItem("admin_token") || "";
    setAdminToken(savedToken);
  }, []);

  async function fetchDiagnostic(token: string) {
    setLoading(true);
    try {
      const res = await api.get(`admin/empresas/${id}/diagnostico`, {
        headers: { "X-Admin-Token": token }
      });
      setData(res.data);
      setIsAuthorized(true);
      localStorage.setItem("admin_token", token);
    } catch (err) {
      setIsAuthorized(false);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (adminToken) {
      fetchDiagnostic(adminToken);
    }
  }, [adminToken]);

  async function handleSync() {
    if (!data) return;
    setSyncing(true);
    try {
      // Usamos o endpoint de sync do dashboard via admin (impersonate/bypass ou direto se disponível)
      // Como o dashboard_api tem o /whatsapp/sync, podemos tentar chamar via admin_api se existir
      // Por enquanto, vamos simular ou chamar se o endpoint existir. 
      // Se não, avisamos que a sincronização automática acontece ao abrir a página.
      alert("Disparando comando de sincronização forçada...");
      await api.post(`admin/empresas/${id}/sync`, {}, {
        headers: { "X-Admin-Token": adminToken }
      });
      fetchDiagnostic(adminToken);
    } catch (err) {
      alert("Erro ao sincronizar. Verifique os logs.");
    } finally {
      setSyncing(false);
    }
  }

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center p-6 text-white">
        <div className="glass-panel p-8 w-full max-w-md space-y-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="p-4 rounded-full bg-purple-500/10 text-purple-400">
              <ShieldCheck size={48} />
            </div>
            <h1 className="text-2xl font-bold">Diagnóstico Protegido</h1>
            <p className="text-slate-400">Insira o Token Master para visualizar o status técnico deste cliente.</p>
          </div>
          <div className="space-y-4">
            <input 
              type="password"
              placeholder="Digite o Token Master..."
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-purple-500 transition-all"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
            />
            <button 
              onClick={() => fetchDiagnostic(adminToken)}
              className="w-full py-3 bg-purple-600 hover:bg-purple-700 rounded-xl font-semibold transition-all"
            >
              Validar Acesso
            </button>
            <Link href="/admin" className="block text-center text-sm text-slate-500 hover:text-white transition-colors">
              Voltar para Lista
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center text-white">
        <div className="flex flex-col items-center gap-4">
          <RefreshCcw className="animate-spin text-blue-500" size={48} />
          <p className="text-slate-400 font-mono">Escaneando infraestrutura...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)] p-6 md:p-12 text-white">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header de Navegação */}
        <div className="flex items-center justify-between">
          <Link href="/admin" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft size={20} />
            Voltar para a Central
          </Link>
          <div className="flex gap-3">
            <button 
              onClick={() => fetchDiagnostic(adminToken)}
              className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 transition-all text-sm"
            >
              <RefreshCcw size={16} />
              Atualizar Dados
            </button>
            <button 
              onClick={handleSync}
              disabled={syncing}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg shadow-lg shadow-blue-600/20 transition-all text-sm font-bold"
            >
              <Zap size={16} />
              {syncing ? "Sincronizando..." : "Forçar Sincronização"}
            </button>
          </div>
        </div>

        {/* Hero de Status */}
        <header className="glass-panel p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 border-l-4 border-blue-500">
          <div className="flex items-center gap-6">
            <div className={`p-5 rounded-2xl ${data.integracao.status_conexao === 'connected' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
              <Activity size={40} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-3xl font-bold tracking-tight">{data.empresa.nome}</h1>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${data.empresa.ativa ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                  {data.empresa.ativa ? "Ativa" : "Inativa"}
                </span>
              </div>
              <p className="text-slate-400 font-mono text-sm mt-1">ID: {data.empresa.id}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
            <div className="text-center">
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">WhatsApp</p>
              <div className="flex items-center justify-center gap-2">
                {data.integracao.status_conexao === 'connected' ? (
                  <CheckCircle2 className="text-green-500" size={18} />
                ) : (
                  <XCircle className="text-red-500" size={18} />
                )}
                <span className="font-bold">{data.integracao.status_conexao === 'connected' ? 'ONLINE' : 'OFFLINE'}</span>
              </div>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Webhook</p>
              <div className="flex items-center justify-center gap-2">
                {data.integracao.webhook_ok ? (
                  <CheckCircle2 className="text-green-500" size={18} />
                ) : (
                  <XCircle className="text-red-500" size={18} />
                )}
                <span className="font-bold">{data.integracao.webhook_ok ? 'OK' : 'FALHA'}</span>
              </div>
            </div>
            <div className="text-center col-span-2 md:col-span-1">
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Configuração IA</p>
              <div className="flex items-center justify-center gap-2">
                {data.configuracao_ia.ok ? (
                  <CheckCircle2 className="text-blue-500" size={18} />
                ) : (
                  <XCircle className="text-yellow-500" size={18} />
                )}
                <span className="font-bold uppercase">{data.configuracao_ia.nicho}</span>
              </div>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Detalhes Técnicos */}
          <div className="lg:col-span-1 space-y-6">
            <div className="glass-panel p-6 space-y-6">
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                <Globe size={16} /> Infraestrutura
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="text-[10px] text-slate-500 uppercase font-bold">Instância Evolution</label>
                  <p className="font-mono text-sm bg-black/30 p-2 rounded border border-white/5 mt-1">{data.integracao.instancia || "Não vinculada"}</p>
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 uppercase font-bold">Webhook Atual (API)</label>
                  <p className={`font-mono text-[10px] p-2 rounded border mt-1 break-all ${data.integracao.webhook_ok ? 'bg-green-500/5 border-green-500/20 text-green-400' : 'bg-red-500/5 border-red-500/20 text-red-400'}`}>
                    {data.integracao.webhook_atual || "Nenhum configurado"}
                  </p>
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 uppercase font-bold">Webhook Esperado</label>
                  <p className="font-mono text-[10px] bg-black/30 p-2 rounded border border-white/5 mt-1 break-all text-slate-400">
                    {data.integracao.webhook_esperado}
                  </p>
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 uppercase font-bold">Base URL (Server)</label>
                  <p className="font-mono text-sm text-blue-400 mt-1">{data.integracao.base_url_configurada}</p>
                </div>
              </div>
            </div>

            <div className="glass-panel p-6">
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2 mb-4">
                <Bot size={16} /> Status da IA
              </h3>
              <div className="flex items-center gap-4 p-4 rounded-xl bg-blue-500/5 border border-blue-500/10">
                <div className={`p-3 rounded-lg ${data.configuracao_ia.ok ? 'bg-blue-500/20 text-blue-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                  <Bot size={24} />
                </div>
                <div>
                  <p className="font-bold">{data.configuracao_ia.ok ? "Pronta para Conversar" : "Aguardando Config"}</p>
                  <p className="text-xs text-slate-500">Personalidade e regras do nicho aplicadas.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Terminal de Atividade */}
          <div className="lg:col-span-2">
            <div className="bg-[#0c0e14] rounded-2xl border border-white/10 overflow-hidden shadow-2xl flex flex-col h-[600px]">
              <div className="bg-white/5 p-4 border-b border-white/10 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TerminalIcon size={18} className="text-slate-400" />
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Atividade do Sistema - Console</span>
                </div>
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 font-mono text-sm space-y-4 custom-scrollbar">
                {data.ultimos_eventos.length === 0 ? (
                  <div className="text-slate-600 italic">Aguardando primeiros eventos do cliente...</div>
                ) : (
                  data.ultimos_eventos.map((ev, i) => (
                    <div key={i} className="flex gap-4 group">
                      <span className="text-slate-600 whitespace-nowrap">[{new Date(ev.timestamp).toLocaleTimeString()}]</span>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${
                            ev.tipo.includes('erro') ? 'text-red-400' : 
                            ev.tipo.includes('webhook') ? 'text-blue-400' : 
                            'text-green-400'
                          }`}>
                            {ev.tipo.toUpperCase()}
                          </span>
                          <span className="text-slate-400 text-xs">PROCESS_OK</span>
                        </div>
                        {ev.metadata && (
                          <pre className="text-[10px] text-slate-500 bg-white/5 p-2 rounded-lg border border-white/5 overflow-x-auto max-w-full">
                            {JSON.stringify(ev.metadata, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  ))
                )}
                <div className="flex gap-2 animate-pulse">
                  <span className="text-green-500">_</span>
                </div>
              </div>
              
              <div className="p-4 bg-white/5 border-t border-white/10 flex items-center gap-4 text-[10px] text-slate-500 font-mono">
                <div className="flex items-center gap-1">
                  <Clock size={12} />
                  ÚLTIMA ATUALIZAÇÃO: {new Date().toLocaleTimeString()}
                </div>
                <div className="flex items-center gap-1">
                  <Activity size={12} />
                  CPU: 2%
                </div>
                <div className="ml-auto text-blue-400 uppercase font-bold">
                  Sistema Operacional AgenteGo v2.4
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
