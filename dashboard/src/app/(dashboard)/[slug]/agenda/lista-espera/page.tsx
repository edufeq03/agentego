"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { 
  Users, 
  Trash2, 
  Clock, 
  Calendar, 
  Phone, 
  Layers, 
  CheckCircle, 
  AlertCircle,
  Bell
} from "lucide-react";
import api from "@/lib/api";

interface WaitlistItem {
  id: number;
  data: string;
  status: string;
  posicao: number;
  notificado_em: string | null;
  cliente_nome: string;
  cliente_telefone: string;
  servico_nome: string;
}

export default function ListaEsperaPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [items, setItems] = useState<WaitlistItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchListaEspera();
  }, []);

  async function fetchListaEspera() {
    try {
      const res = await api.get("dashboard/agenda/lista_espera");
      setItems(res.data);
    } catch (err) {
      console.error("Erro ao carregar lista de espera:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Tem certeza que deseja remover este cliente da lista de espera?")) return;
    try {
      await api.delete(`dashboard/agenda/lista_espera/${id}`);
      fetchListaEspera();
    } catch (err) {
      alert("Erro ao remover da lista de espera.");
    }
  }

  function getStatusBadge(status: string) {
    switch (status) {
      case "aguardando":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-500">Aguardando</span>;
      case "notificado":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-500 flex items-center gap-1"><Bell size={12} /> Notificado</span>;
      case "confirmado":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500">Confirmado</span>;
      case "recusado":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-500">Recusado</span>;
      case "expirado":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-500/10 text-gray-400">Expirado</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-500/10 text-gray-300">{status}</span>;
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div>
        <h2 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <Users className="text-[var(--color-brand-400)]" />
          Lista de Espera
        </h2>
        <p className="text-[var(--color-foreground-muted)] mt-1">
          Gerencie clientes na fila de espera para cancelamentos e horários concorridos.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-[var(--color-foreground-muted)]">Carregando lista de espera...</div>
      ) : items.length === 0 ? (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-12 text-center">
          <Clock className="mx-auto text-[var(--color-foreground-muted)] mb-4" size={48} />
          <h3 className="text-lg font-bold text-white">Lista de espera vazia</h3>
          <p className="text-[var(--color-foreground-muted)] mt-1 max-w-md mx-auto">
            Nenhum cliente está na fila de espera atualmente. Clientes que solicitarem horários ocupados serão sugeridos a entrar na lista pela IA.
          </p>
        </div>
      ) : (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[var(--color-border)] bg-[var(--color-background)]/50">
                  <th className="px-6 py-4 text-sm font-semibold text-white">Posição</th>
                  <th className="px-6 py-4 text-sm font-semibold text-white">Cliente</th>
                  <th className="px-6 py-4 text-sm font-semibold text-white">Serviço solicitado</th>
                  <th className="px-6 py-4 text-sm font-semibold text-white">Data desejada</th>
                  <th className="px-6 py-4 text-sm font-semibold text-white">Status</th>
                  <th className="px-6 py-4 text-sm font-semibold text-white">Notificado Em</th>
                  <th className="px-6 py-4 text-sm font-semibold text-white text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-[var(--color-surface-hover)] transition-colors">
                    <td className="px-6 py-4 text-sm font-bold text-white">
                      #{item.posicao}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-white">{item.cliente_nome}</div>
                      <div className="text-xs text-[var(--color-foreground-muted)] flex items-center gap-1 mt-0.5">
                        <Phone size={12} />
                        {item.cliente_telefone}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-[var(--color-brand-500)]/10 text-[var(--color-brand-400)] border border-[var(--color-brand-500)]/20">
                        <Layers size={12} />
                        {item.servico_nome}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-[var(--color-foreground-muted)]">
                      <div className="flex items-center gap-1.5">
                        <Calendar size={14} className="text-[var(--color-brand-400)]" />
                        {new Date(item.data + "T00:00:00").toLocaleDateString("pt-BR")}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {getStatusBadge(item.status)}
                    </td>
                    <td className="px-6 py-4 text-sm text-[var(--color-foreground-muted)]">
                      {item.notificado_em 
                        ? new Date(item.notificado_em).toLocaleString("pt-BR")
                        : "-"
                      }
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => handleDelete(item.id)}
                        className="p-2 text-[var(--color-foreground-muted)] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                        title="Remover da lista de espera"
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
