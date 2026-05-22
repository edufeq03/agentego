"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { 
  ClipboardList, Clock, CheckCircle2, XCircle, Search, 
  MapPin, User, Hash, HelpCircle, Eye, Phone, RefreshCw, ShoppingBag 
} from "lucide-react";
import api from "@/lib/api";

interface Cliente {
  nome: string;
  telefone: string;
}

interface ItemPedido {
  id: string;
  nome: string;
  preco_unit: number;
  quantidade: number;
  observacao: string | null;
}

interface Pedido {
  id: string;
  numero_pedido: number;
  modo: string;
  status: string;
  total: number;
  observacao: string | null;
  endereco: string | null;
  nome_balcao: string | null;
  numero_mesa: number | null;
  criado_em: string;
  cliente: Cliente;
  itens: ItemPedido[];
}

export default function PedidosPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [activeTab, setActiveTab] = useState<"ativos" | "historico">("ativos");
  const [pedidosAtivos, setPedidosAtivos] = useState<Pedido[]>([]);
  const [pedidosHistorico, setPedidosHistorico] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Polling interval ref
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    carregarDados(true);
    
    // Configura o Auto Polling de 10 segundos para pedidos ativos
    pollingRef.current = setInterval(() => {
      carregarDados(false);
    }, 10000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [slug]);

  async function carregarDados(showSkeleton = false) {
    try {
      if (showSkeleton) setLoading(true);
      else setRefreshing(true);

      const resAtivos = await api.get("dashboard/lanchonete/pedidos/ativos");
      setPedidosAtivos(resAtivos.data);

      const resHist = await api.get("dashboard/lanchonete/pedidos/historico", {
        params: { limit: 100 }
      });
      setPedidosHistorico(resHist.data);
    } catch (error) {
      console.error("Erro ao carregar pedidos:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  async function handleMudarStatus(pedidoId: string, novoStatus: string) {
    try {
      // Otimização visual imediata
      setPedidosAtivos(prev => 
        prev.map(p => p.id === pedidoId ? { ...p, status: novoStatus } : p)
      );
      
      await api.patch(`dashboard/lanchonete/pedidos/${pedidoId}/status`, {
        status: novoStatus
      });
      
      // Recarrega todos os dados para refletir as mudanças do banco de dados (ex: envio de histórico)
      carregarDados(false);
    } catch (error) {
      console.error("Erro ao atualizar status:", error);
      carregarDados(false);
    }
  }

  // Filtrar pedidos
  const filterPredicate = (p: Pedido) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      p.numero_pedido.toString().includes(term) ||
      p.cliente.nome.toLowerCase().includes(term) ||
      p.cliente.telefone.includes(term) ||
      (p.nome_balcao && p.nome_balcao.toLowerCase().includes(term)) ||
      (p.endereco && p.endereco.toLowerCase().includes(term))
    );
  };

  const ativosFiltrados = pedidosAtivos.filter(filterPredicate);
  const historicoFiltrado = pedidosHistorico.filter(filterPredicate);

  // Mapeamento de emojis e cores do status
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "aguardando":
        return {
          label: "Aguardando",
          bg: "bg-amber-500/10 border-amber-500/20 text-amber-400",
          emoji: "⌛"
        };
      case "em_preparo":
        return {
          label: "Preparando",
          bg: "bg-blue-500/10 border-blue-500/20 text-blue-400",
          emoji: "🍳"
        };
      case "pronto":
        return {
          label: "Pronto",
          bg: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
          emoji: "✅"
        };
      case "entregue":
        return {
          label: "Entregue",
          bg: "bg-slate-800 border-slate-700 text-slate-400",
          emoji: "📦"
        };
      case "cancelado":
        return {
          label: "Cancelado",
          bg: "bg-red-500/10 border-red-500/20 text-red-400",
          emoji: "❌"
        };
      default:
        return {
          label: status,
          bg: "bg-slate-800 border-slate-700 text-slate-400",
          emoji: "❓"
        };
    }
  };

  // Formatar Horário
  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "00:00";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/40 p-6 rounded-2xl border border-slate-800 backdrop-blur-md">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <ClipboardList className="text-[var(--color-brand-400)]" />
            Painel da Cozinha & Pedidos
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Acompanhe a fila de preparo em tempo real. A tela atualiza automaticamente a cada 10 segundos.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {refreshing && (
            <span className="text-slate-500 text-xs flex items-center gap-1.5 animate-pulse">
              <RefreshCw size={12} className="animate-spin" /> Atualizando...
            </span>
          )}
          <button
            onClick={() => carregarDados(true)}
            className="p-2 text-slate-400 hover:text-white bg-slate-800 rounded-lg transition-all"
            title="Atualizar agora"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Tabs de Filtro e Busca */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Navigation Tabs */}
        <div className="flex gap-2 bg-slate-950 p-1.5 rounded-xl border border-slate-850 self-start">
          <button
            onClick={() => setActiveTab("ativos")}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === "ativos"
                ? "bg-[var(--color-brand-500)] text-white shadow-md shadow-[var(--color-brand-500)]/15"
                : "text-slate-450 hover:text-white"
            }`}
          >
            🍳 Fila de Produção ({pedidosAtivos.length})
          </button>
          <button
            onClick={() => setActiveTab("historico")}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === "historico"
                ? "bg-[var(--color-brand-500)] text-white shadow-md shadow-[var(--color-brand-500)]/15"
                : "text-slate-450 hover:text-white"
            }`}
          >
            📜 Histórico de Vendas ({pedidosHistorico.length})
          </button>
        </div>

        {/* Search Field */}
        <div className="relative w-full md:max-w-xs">
          <Search className="absolute left-3 top-3.5 text-slate-600" size={16} />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por #pedido ou nome..."
            className="bg-slate-950 border border-slate-850 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-slate-650 w-full focus:outline-none focus:border-[var(--color-brand-500)]"
          />
        </div>
      </div>

      {/* Exibição da Produção ou Histórico */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">Carregando pedidos...</div>
      ) : activeTab === "ativos" ? (
        /* Painel de Produção Ativo */
        ativosFiltrados.length === 0 ? (
          <div className="text-center py-20 bg-slate-900/10 border border-dashed border-slate-800 rounded-3xl text-slate-400 flex flex-col items-center gap-3">
            <ShoppingBag size={48} className="text-slate-700 stroke-[1.5]" />
            <div>
              <p className="font-bold text-white">Nenhum pedido ativo na fila!</p>
              <p className="text-slate-500 text-sm mt-1">Os pedidos feitos pelos clientes aparecerão aqui instantaneamente.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {ativosFiltrados.map((ped) => {
              const badge = getStatusBadge(ped.status);
              return (
                <div
                  key={ped.id}
                  className="bg-slate-900/25 border border-slate-850 hover:border-slate-800 rounded-2xl p-5 flex flex-col justify-between transition-all space-y-4"
                >
                  {/* Top Pedido Meta */}
                  <div className="flex items-start justify-between border-b border-slate-800/60 pb-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-black text-white">#{ped.numero_pedido}</span>
                        <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${badge.bg}`}>
                          {badge.emoji} {badge.label}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-500 text-xs">
                        <Clock size={12} />
                        <span>{formatTime(ped.criado_em)}</span>
                        <span>•</span>
                        <span className="capitalize font-bold text-slate-400">{ped.modo}</span>
                      </div>
                    </div>
                    <span className="text-lg font-extrabold text-[var(--color-brand-400)]">
                      R$ {ped.total.toFixed(2)}
                    </span>
                  </div>

                  {/* Detalhes do Cliente e Modo */}
                  <div className="bg-slate-950/40 p-3 rounded-xl border border-slate-900 space-y-1.5 text-xs text-slate-350">
                    <div className="flex items-center gap-2">
                      <User size={12} className="text-slate-500" />
                      <span className="font-bold text-white truncate">{ped.cliente.nome}</span>
                      <a 
                        href={`https://wa.me/${ped.cliente.telefone}`} 
                        target="_blank" 
                        rel="noreferrer"
                        className="text-[var(--color-brand-450)] hover:text-white"
                      >
                        <Phone size={10} className="inline mr-0.5" />
                        ({ped.cliente.telefone.slice(-11)})
                      </a>
                    </div>

                    {ped.modo === "delivery" && (
                      <div className="flex items-start gap-2">
                        <MapPin size={12} className="text-slate-500 mt-0.5 shrink-0" />
                        <span className="line-clamp-2">{ped.endereco || "Endereço não informado"}</span>
                      </div>
                    )}
                    {ped.modo === "mesa" && (
                      <div className="flex items-center gap-2">
                        <Hash size={12} className="text-slate-500" />
                        <span>Mesa acomodada: <strong className="text-white font-bold">{ped.numero_mesa}</strong></span>
                      </div>
                    )}
                    {ped.modo === "balcao" && (
                      <div className="flex items-center gap-2">
                        <User size={12} className="text-slate-500" />
                        <span>Nome no balcão: <strong className="text-white font-bold">{ped.nome_balcao || "Não inf."}</strong></span>
                      </div>
                    )}
                  </div>

                  {/* Itens do Pedido */}
                  <div className="flex-1 py-1 space-y-2">
                    <h4 className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Itens do Pedido:</h4>
                    <ul className="space-y-1.5">
                      {ped.itens.map((it) => (
                        <li key={it.id} className="text-sm text-slate-200 leading-tight">
                          <span className="font-extrabold text-[var(--color-brand-400)] mr-1.5">{it.quantidade}x</span>
                          <span className="font-semibold">{it.nome}</span>
                          {it.observacao && (
                            <p className="text-slate-400 text-xs italic pl-6 mt-0.5">
                              ⚠️ "{it.observacao}"
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Observação Geral */}
                  {ped.observacao && (
                    <div className="text-xs bg-amber-500/5 border border-amber-500/10 text-amber-300 p-2.5 rounded-xl">
                      <strong>Obs Geral:</strong> "{ped.observacao}"
                    </div>
                  )}

                  {/* Ações de Transição de Status */}
                  <div className="border-t border-slate-800/60 pt-4 mt-auto">
                    {ped.status === "aguardando" && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleMudarStatus(ped.id, "em_preparo")}
                          className="flex-1 bg-amber-500 hover:bg-amber-600 text-slate-950 py-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5"
                        >
                          🍳 Iniciar Preparo
                        </button>
                        <button
                          onClick={() => handleMudarStatus(ped.id, "cancelado")}
                          className="bg-slate-800 hover:bg-red-500/10 text-slate-400 hover:text-red-400 p-2 rounded-xl text-xs font-bold transition-all"
                          title="Cancelar Pedido"
                        >
                          ✕
                        </button>
                      </div>
                    )}
                    {ped.status === "em_preparo" && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleMudarStatus(ped.id, "pronto")}
                          className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5"
                        >
                          ✅ Pronto para Entrega
                        </button>
                        <button
                          onClick={() => handleMudarStatus(ped.id, "cancelado")}
                          className="bg-slate-800 hover:bg-red-500/10 text-slate-400 hover:text-red-400 p-2 rounded-xl text-xs font-bold transition-all"
                          title="Cancelar"
                        >
                          ✕
                        </button>
                      </div>
                    )}
                    {ped.status === "pronto" && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleMudarStatus(ped.id, "entregue")}
                          className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-slate-950 py-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5"
                        >
                          📦 Finalizar & Entregar
                        </button>
                        <button
                          onClick={() => handleMudarStatus(ped.id, "cancelado")}
                          className="bg-slate-800 hover:bg-red-500/10 text-slate-400 hover:text-red-400 p-2 rounded-xl text-xs font-bold transition-all"
                          title="Cancelar"
                        >
                          ✕
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : (
        /* Histórico de Vendas Concluídas/Canceladas */
        historicoFiltrado.length === 0 ? (
          <div className="text-center py-16 bg-slate-900/10 border border-dashed border-slate-800 rounded-3xl text-slate-400">
            Nenhum pedido finalizado no histórico.
          </div>
        ) : (
          <div className="bg-slate-900/10 border border-slate-850 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-slate-300">
                <thead>
                  <tr className="bg-slate-950 border-b border-slate-850 text-slate-400 text-xs font-bold uppercase tracking-wider">
                    <th className="py-4 px-6">Pedido</th>
                    <th className="py-4 px-6">Horário</th>
                    <th className="py-4 px-6">Cliente</th>
                    <th className="py-4 px-6">Modo</th>
                    <th className="py-4 px-6">Resumo</th>
                    <th className="py-4 px-6 text-right">Total</th>
                    <th className="py-4 px-6 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {historicoFiltrado.map((ped) => {
                    const badge = getStatusBadge(ped.status);
                    const resumoItens = ped.itens.map(i => `${i.quantidade}x ${i.nome}`).join(", ");
                    return (
                      <tr key={ped.id} className="hover:bg-slate-900/20 transition-all text-sm">
                        <td className="py-4 px-6 font-bold text-white">#{ped.numero_pedido}</td>
                        <td className="py-4 px-6 text-slate-400">{formatTime(ped.criado_em)}</td>
                        <td className="py-4 px-6">
                          <div className="font-bold text-white">{ped.cliente.nome}</div>
                          <div className="text-xs text-slate-500">{ped.cliente.telefone}</div>
                        </td>
                        <td className="py-4 px-6 capitalize">{ped.modo}</td>
                        <td className="py-4 px-6 truncate max-w-[200px]" title={resumoItens}>
                          {resumoItens}
                        </td>
                        <td className="py-4 px-6 font-extrabold text-[var(--color-brand-400)] text-right">
                          R$ {ped.total.toFixed(2)}
                        </td>
                        <td className="py-4 px-6 text-center">
                          <span className={`inline-block text-xs font-bold px-2.5 py-0.5 rounded-full border ${badge.bg}`}>
                            {badge.emoji} {badge.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}
    </div>
  );
}
