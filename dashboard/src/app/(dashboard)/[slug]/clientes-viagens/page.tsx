"use client";

import { useState, useEffect } from "react";
import {
  Plane, Plus, Trash2, Search, Users, MessageCircle,
  Star, X, Edit3, CheckCircle2, MapPin, Mail, Phone, Tag
} from "lucide-react";
import api from "@/lib/api";

interface ClienteViagem {
  id: string;
  nome: string;
  telefone: string;
  email: string | null;
  canal_entrada: string;
  destinos_interesse: string[];
  observacoes: string | null;
  criado_em: string | null;
}

interface StatsData {
  total: number;
  novos_hoje: number;
  via_whatsapp: number;
}

const CANAL_BADGE: Record<string, { label: string; color: string; icon: string }> = {
  whatsapp: { label: "WhatsApp", color: "bg-green-500/15 text-green-400 border-green-500/30", icon: "🟢" },
  manual: { label: "Manual", color: "bg-blue-500/15 text-blue-400 border-blue-500/30", icon: "✏️" },
  csv: { label: "CSV", color: "bg-purple-500/15 text-purple-400 border-purple-500/30", icon: "📁" },
};

export default function ClientesViagensPage() {
  const [clientes, setClientes] = useState<ClienteViagem[]>([]);
  const [stats, setStats] = useState<StatsData>({ total: 0, novos_hoje: 0, via_whatsapp: 0 });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingCliente, setEditingCliente] = useState<ClienteViagem | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    nome: "",
    telefone: "",
    email: "",
    destinos_interesse: "",
    observacoes: "",
  });

  useEffect(() => {
    fetchAll();
  }, []);

  async function fetchAll() {
    setLoading(true);
    try {
      const [clientesRes, statsRes] = await Promise.all([
        api.get("dashboard/agencia/clientes"),
        api.get("dashboard/agencia/clientes/stats"),
      ]);
      setClientes(clientesRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Erro ao carregar clientes:", error);
    } finally {
      setLoading(false);
    }
  }

  function openAdd() {
    setForm({ nome: "", telefone: "", email: "", destinos_interesse: "", observacoes: "" });
    setEditingCliente(null);
    setIsAddModalOpen(true);
  }

  function openEdit(c: ClienteViagem) {
    setForm({
      nome: c.nome,
      telefone: c.telefone,
      email: c.email || "",
      destinos_interesse: (c.destinos_interesse || []).join(", "),
      observacoes: c.observacoes || "",
    });
    setEditingCliente(c);
    setIsAddModalOpen(true);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const destinos = form.destinos_interesse
        .split(",")
        .map((d) => d.trim())
        .filter(Boolean);

      if (editingCliente) {
        await api.put(`dashboard/agencia/clientes/${editingCliente.id}`, {
          nome: form.nome,
          email: form.email || null,
          destinos_interesse: destinos,
          observacoes: form.observacoes || null,
        });
      } else {
        await api.post("dashboard/agencia/clientes", {
          nome: form.nome,
          telefone: form.telefone,
          email: form.email || null,
          canal_entrada: "manual",
          destinos_interesse: destinos,
          observacoes: form.observacoes || null,
        });
      }
      setIsAddModalOpen(false);
      fetchAll();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Erro ao salvar cliente.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string, nome: string) {
    if (!confirm(`Remover "${nome}" da base de clientes?`)) return;
    try {
      await api.delete(`dashboard/agencia/clientes/${id}`);
      setClientes(clientes.filter((c) => c.id !== id));
      setStats((s) => ({ ...s, total: s.total - 1 }));
    } catch {
      alert("Erro ao remover cliente.");
    }
  }

  const filtered = clientes.filter(
    (c) =>
      c.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.telefone.includes(searchTerm) ||
      (c.email || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.destinos_interesse || []).some((d) => d.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 rounded-xl bg-sky-500/15 text-sky-400">
              <Plane size={22} />
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight">Gestão de Clientes</h2>
          </div>
          <p className="text-[var(--color-foreground-muted)] mt-1 ml-1">
            Clientes cadastrados automaticamente via WhatsApp ou manualmente.
          </p>
        </div>
        <button
          onClick={openAdd}
          className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-xl font-semibold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
        >
          <Plus size={18} />
          Adicionar Cliente
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl">
          <div className="flex items-center gap-4">
            <div className="bg-sky-500/10 p-3 rounded-xl text-sky-400"><Users size={24} /></div>
            <div>
              <p className="text-sm text-[var(--color-foreground-muted)]">Total de Clientes</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </div>
          </div>
        </div>
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl">
          <div className="flex items-center gap-4">
            <div className="bg-emerald-500/10 p-3 rounded-xl text-emerald-400"><CheckCircle2 size={24} /></div>
            <div>
              <p className="text-sm text-[var(--color-foreground-muted)]">Cadastrados Hoje</p>
              <p className="text-2xl font-bold text-white">{stats.novos_hoje}</p>
            </div>
          </div>
        </div>
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl">
          <div className="flex items-center gap-4">
            <div className="bg-green-500/10 p-3 rounded-xl text-green-400"><MessageCircle size={24} /></div>
            <div>
              <p className="text-sm text-[var(--color-foreground-muted)]">Via WhatsApp</p>
              <p className="text-2xl font-bold text-white">{stats.via_whatsapp}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-[var(--color-border)] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" size={18} />
            <input
              type="text"
              placeholder="Buscar por nome, telefone, destino..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 pl-10 pr-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all"
            />
          </div>
          <p className="text-sm text-[var(--color-foreground-muted)]">{filtered.length} cliente(s)</p>
        </div>

        {/* Desktop table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-[var(--color-surface-hover)]/50 text-[var(--color-foreground-muted)] text-sm font-medium">
                <th className="px-6 py-4">Cliente</th>
                <th className="px-6 py-4">Telefone</th>
                <th className="px-6 py-4">Destinos de Interesse</th>
                <th className="px-6 py-4">Canal</th>
                <th className="px-6 py-4">Cadastro</th>
                <th className="px-6 py-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-[var(--color-foreground-muted)]">Carregando...</td></tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16 text-center">
                    <div className="flex flex-col items-center gap-3 text-[var(--color-foreground-muted)]">
                      <Plane size={40} className="opacity-30" />
                      <p>Nenhum cliente encontrado.</p>
                      <p className="text-xs">Os clientes são cadastrados automaticamente quando entram em contato via WhatsApp.</p>
                    </div>
                  </td>
                </tr>
              ) : filtered.map((c) => {
                const canal = CANAL_BADGE[c.canal_entrada] || CANAL_BADGE.manual;
                return (
                  <tr key={c.id} className="hover:bg-[var(--color-surface-hover)]/30 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-sky-500/10 flex items-center justify-center text-sky-400 font-bold text-sm">
                          {c.nome.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <span className="font-medium text-white block">{c.nome}</span>
                          {c.email && <span className="text-xs text-[var(--color-foreground-muted)]">{c.email}</span>}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-[var(--color-foreground-muted)]">{c.telefone}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {(c.destinos_interesse || []).slice(0, 3).map((d) => (
                          <span key={d} className="px-2 py-0.5 rounded-full bg-[var(--color-brand-500)]/10 text-[var(--color-brand-400)] text-xs font-medium border border-[var(--color-brand-500)]/20">
                            {d}
                          </span>
                        ))}
                        {(c.destinos_interesse || []).length > 3 && (
                          <span className="text-xs text-[var(--color-foreground-muted)]">+{c.destinos_interesse.length - 3}</span>
                        )}
                        {(c.destinos_interesse || []).length === 0 && (
                          <span className="text-xs text-[var(--color-foreground-muted)]">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${canal.color}`}>
                        {canal.icon} {canal.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-[var(--color-foreground-muted)]">
                      {c.criado_em ? new Date(c.criado_em).toLocaleDateString("pt-BR") : "—"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-all">
                        <button
                          onClick={() => openEdit(c)}
                          className="p-2 text-[var(--color-foreground-muted)] hover:text-[var(--color-brand-400)] hover:bg-[var(--color-brand-500)]/10 rounded-lg transition-all"
                          title="Editar"
                        >
                          <Edit3 size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(c.id, c.nome)}
                          className="p-2 text-[var(--color-foreground-muted)] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all"
                          title="Remover"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="block md:hidden divide-y divide-[var(--color-border)]">
          {loading ? (
            <div className="py-12 text-center text-[var(--color-foreground-muted)]">Carregando...</div>
          ) : filtered.map((c) => {
            const canal = CANAL_BADGE[c.canal_entrada] || CANAL_BADGE.manual;
            return (
              <div key={c.id} className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-sky-500/10 flex items-center justify-center text-sky-400 font-bold">
                      {c.nome.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-bold text-white">{c.nome}</p>
                      <p className="text-xs text-[var(--color-foreground-muted)]">{c.telefone}</p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => openEdit(c)} className="p-2 text-[var(--color-foreground-muted)] hover:text-[var(--color-brand-400)] rounded-lg">
                      <Edit3 size={16} />
                    </button>
                    <button onClick={() => handleDelete(c.id, c.nome)} className="p-2 text-[var(--color-foreground-muted)] hover:text-red-400 rounded-lg">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {(c.destinos_interesse || []).map((d) => (
                    <span key={d} className="px-2 py-0.5 rounded-full bg-[var(--color-brand-500)]/10 text-[var(--color-brand-400)] text-xs border border-[var(--color-brand-500)]/20">{d}</span>
                  ))}
                </div>
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${canal.color}`}>
                  {canal.icon} {canal.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modal Add/Edit */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => !saving && setIsAddModalOpen(false)} />
          <div className="relative bg-[var(--color-surface)] border border-[var(--color-border)] w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-between">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Plane className="text-sky-400" size={20} />
                {editingCliente ? "Editar Cliente" : "Novo Cliente"}
              </h3>
              <button onClick={() => setIsAddModalOpen(false)} disabled={saving} className="text-[var(--color-foreground-muted)] hover:text-white">
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleSave} className="p-4 space-y-3">
              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">Nome *</label>
                <input
                  type="text"
                  required
                  value={form.nome}
                  onChange={(e) => setForm({ ...form, nome: e.target.value })}
                  placeholder="Nome completo do cliente"
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50"
                />
              </div>

              {!editingCliente && (
                <div>
                  <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">
                    Telefone (WhatsApp) *
                    <span className="ml-1 text-xs text-[var(--color-foreground-muted)]/60">Ex: 11999999999 ou 5511999999999</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={form.telefone}
                    onChange={(e) => setForm({ ...form, telefone: e.target.value })}
                    placeholder="DDD + número"
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">E-mail</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="email@exemplo.com"
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">
                  Destinos de Interesse
                  <span className="ml-1 text-xs text-[var(--color-foreground-muted)]/60">Separar por vírgula</span>
                </label>
                <input
                  type="text"
                  value={form.destinos_interesse}
                  onChange={(e) => setForm({ ...form, destinos_interesse: e.target.value })}
                  placeholder="Europa, Caribe, Miami..."
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">Observações</label>
                <textarea
                  rows={2}
                  value={form.observacoes}
                  onChange={(e) => setForm({ ...form, observacoes: e.target.value })}
                  placeholder="Notas sobre o cliente..."
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 resize-none"
                />
              </div>

              <div className="flex gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  disabled={saving}
                  className="flex-1 py-2.5 bg-[var(--color-surface-hover)] hover:bg-[var(--color-border)] text-white rounded-xl font-semibold transition-all"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-2.5 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] disabled:opacity-50 text-white rounded-xl font-bold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
                >
                  {saving ? "Salvando..." : editingCliente ? "Salvar Alterações" : "Adicionar Cliente"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
