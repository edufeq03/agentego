"use client";

import { useState, useEffect } from "react";
import {
  ListFilter, Plus, Trash2, Send, Users, ChevronLeft,
  X, CheckCircle2, AlertCircle, Clock, Image as ImageIcon,
  UserPlus, History, Loader2, MessageSquare, Search, Calendar
} from "lucide-react";
import api, { getApiBaseUrl } from "@/lib/api";

interface Lista {
  id: string;
  nome: string;
  descricao: string | null;
  total_contatos: number;
  ultimo_disparo: string | null;
  criado_em: string | null;
}

interface Contato {
  id: string;
  nome: string;
  telefone: string;
  adicionado_em: string | null;
}

interface Disparo {
  id: string;
  mensagem: string;
  imagem_url: string | null;
  status: string;
  total_contatos: number;
  enviados: number;
  erros: number;
  criado_em: string;
  data_programada: string | null;
  enviado_em: string | null;
}

const STATUS_BADGE: Record<string, { label: string; color: string; icon: React.FC<any> }> = {
  enviado: { label: "Enviado", color: "bg-emerald-500/15 text-emerald-400", icon: CheckCircle2 },
  enviando: { label: "Enviando...", color: "bg-blue-500/15 text-blue-400", icon: Loader2 },
  pendente: { label: "Pendente", color: "bg-amber-500/15 text-amber-400", icon: Clock },
  erro: { label: "Erro", color: "bg-red-500/15 text-red-400", icon: AlertCircle },
};

type View = "listas" | "contatos";
type Modal = null | "nova_lista" | "add_contato" | "disparar";

export default function ListasTransmissaoPage() {
  const [view, setView] = useState<View>("listas");
  const [listas, setListas] = useState<Lista[]>([]);
  const [selectedLista, setSelectedLista] = useState<Lista | null>(null);
  const [contatos, setContatos] = useState<Contato[]>([]);
  const [disparos, setDisparos] = useState<Disparo[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState<Modal>(null);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  const apiBaseUrl = getApiBaseUrl();

  const [formLista, setFormLista] = useState({ nome: "", descricao: "" });
  const [formContato, setFormContato] = useState({ nome: "", telefone: "" });
  const [formDisparo, setFormDisparo] = useState({ mensagem: "", imagem_url: "", data_programada: "" });
  const [showDisparos, setShowDisparos] = useState(false);

  // Estados da Busca
  const [busca, setBusca] = useState("");
  const [resultadosBusca, setResultadosBusca] = useState<{nome: string, telefone: string}[]>([]);
  const [buscando, setBuscando] = useState(false);

  useEffect(() => {
    fetchListas();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (busca.length >= 2) {
        setBuscando(true);
        api.get(`dashboard/listas-transmissao/buscar-contatos?q=${encodeURIComponent(busca)}`)
           .then(res => setResultadosBusca(res.data))
           .catch(() => setResultadosBusca([]))
           .finally(() => setBuscando(false));
      } else {
        setResultadosBusca([]);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [busca]);

  async function fetchListas() {
    setLoading(true);
    try {
      const res = await api.get("dashboard/listas-transmissao");
      setListas(res.data);
    } catch (err) {
      console.error("Erro ao carregar listas:", err);
    } finally {
      setLoading(false);
    }
  }

  async function openLista(lista: Lista) {
    setSelectedLista(lista);
    setView("contatos");
    setShowDisparos(false);
    await Promise.all([fetchContatos(lista.id), fetchDisparos(lista.id)]);
  }

  async function fetchContatos(listaId: string) {
    try {
      const res = await api.get(`dashboard/listas-transmissao/${listaId}/contatos`);
      setContatos(res.data.contatos || []);
    } catch { setContatos([]); }
  }

  async function fetchDisparos(listaId: string) {
    try {
      const res = await api.get(`dashboard/listas-transmissao/${listaId}/disparos`);
      setDisparos(res.data);
    } catch { setDisparos([]); }
  }

  async function criarLista(e: React.FormEvent) {
    e.preventDefault();
    if (!formLista.nome.trim()) return;
    setSaving(true);
    try {
      await api.post("dashboard/listas-transmissao", {
        nome: formLista.nome,
        descricao: formLista.descricao || null,
      });
      setModal(null);
      setFormLista({ nome: "", descricao: "" });
      fetchListas();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Erro ao criar lista.");
    } finally { setSaving(false); }
  }

  async function deletarLista(id: string, nome: string) {
    if (!confirm(`Excluir a lista "${nome}" e todos seus contatos?`)) return;
    try {
      await api.delete(`dashboard/listas-transmissao/${id}`);
      setListas(listas.filter((l) => l.id !== id));
    } catch { alert("Erro ao excluir lista."); }
  }

  async function adicionarContato(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedLista) return;
    setSaving(true);
    try {
      await api.post(`dashboard/listas-transmissao/${selectedLista.id}/contatos`, {
        nome: formContato.nome || null,
        telefone: formContato.telefone,
      });
      setModal(null);
      setFormContato({ nome: "", telefone: "" });
      fetchContatos(selectedLista.id);
      fetchListas();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Erro ao adicionar contato.");
    } finally { setSaving(false); }
  }

  async function removerContato(contatoId: string) {
    if (!selectedLista) return;
    if (!confirm("Remover este contato da lista?")) return;
    try {
      await api.delete(`dashboard/listas-transmissao/${selectedLista.id}/contatos/${contatoId}`);
      setContatos(contatos.filter((c) => c.id !== contatoId));
    } catch { alert("Erro ao remover contato."); }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('dashboard/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setFormDisparo({ ...formDisparo, imagem_url: res.data.url });
    } catch (err) {
      alert("Erro ao subir imagem.");
    } finally {
      setUploading(false);
    }
  }

  async function disparar(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedLista || !formDisparo.mensagem.trim()) return;
    setSaving(true);
    try {
      await api.post(`dashboard/listas-transmissao/${selectedLista.id}/disparar`, {
        mensagem: formDisparo.mensagem,
        imagem_url: formDisparo.imagem_url || null,
        data_programada: formDisparo.data_programada ? new Date(formDisparo.data_programada).toISOString() : null,
      });
      setModal(null);
      setFormDisparo({ mensagem: "", imagem_url: "", data_programada: "" });
      await fetchDisparos(selectedLista.id);
      setShowDisparos(true);
      alert(`✅ Disparo iniciado para ${selectedLista.total_contatos} contato(s)! O envio está sendo processado em background.`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Erro ao disparar mensagem.");
    } finally { setSaving(false); }
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {view === "contatos" && (
            <button
              onClick={() => { setView("listas"); setSelectedLista(null); }}
              className="p-2 text-[var(--color-foreground-muted)] hover:text-white hover:bg-[var(--color-surface-hover)] rounded-xl transition-all"
            >
              <ChevronLeft size={22} />
            </button>
          )}
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="p-2 rounded-xl bg-violet-500/15 text-violet-400">
                <ListFilter size={22} />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">
                {view === "listas" ? "Listas de Transmissão" : selectedLista?.nome || "Lista"}
              </h2>
            </div>
            <p className="text-[var(--color-foreground-muted)] mt-1 ml-1">
              {view === "listas"
                ? "Crie listas segmentadas e dispare mensagens personalizadas para grupos de contatos."
                : selectedLista?.descricao || `${contatos.length} contato(s) nesta lista`}
            </p>
          </div>
        </div>

        {view === "listas" ? (
          <button
            onClick={() => { setFormLista({ nome: "", descricao: "" }); setModal("nova_lista"); }}
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-xl font-semibold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
          >
            <Plus size={18} />
            Nova Lista
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => { setFormContato({ nome: "", telefone: "" }); setBusca(""); setResultadosBusca([]); setModal("add_contato"); }}
              className="flex items-center gap-2 px-4 py-2.5 bg-[var(--color-surface)] hover:bg-[var(--color-surface-hover)] border border-[var(--color-border)] text-white rounded-xl font-semibold transition-all"
            >
              <UserPlus size={16} />
              Contato
            </button>
            <button
              onClick={() => { setFormDisparo({ mensagem: "", imagem_url: "", data_programada: "" }); setModal("disparar"); }}
              disabled={contatos.length === 0}
              className="flex items-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl font-semibold transition-all shadow-lg shadow-violet-600/20"
            >
              <Send size={16} />
              Disparar
            </button>
          </div>
        )}
      </div>

      {/* VIEW: LISTAS */}
      {view === "listas" && (
        <>
          {loading ? (
            <div className="flex justify-center py-16"><Loader2 size={32} className="animate-spin text-[var(--color-brand-400)]" /></div>
          ) : listas.length === 0 ? (
            <div className="glass-panel p-16 text-center">
              <ListFilter size={48} className="mx-auto mb-4 opacity-20 text-[var(--color-foreground-muted)]" />
              <p className="text-white font-semibold text-lg">Nenhuma lista criada ainda</p>
              <p className="text-[var(--color-foreground-muted)] text-sm mt-2">Crie sua primeira lista e adicione contatos para começar a disparar mensagens segmentadas.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {listas.map((lista) => (
                <div key={lista.id} className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 hover:border-violet-500/30 transition-all group cursor-pointer" onClick={() => openLista(lista)}>
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-2.5 rounded-xl bg-violet-500/10 text-violet-400">
                      <ListFilter size={20} />
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); deletarLista(lista.id, lista.nome); }}
                      className="p-2 text-[var(--color-foreground-muted)] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                  <h3 className="text-white font-bold text-lg mb-1">{lista.nome}</h3>
                  {lista.descricao && <p className="text-[var(--color-foreground-muted)] text-sm mb-4 line-clamp-2">{lista.descricao}</p>}
                  <div className="flex items-center justify-between text-sm mt-4 pt-4 border-t border-[var(--color-border)]">
                    <span className="flex items-center gap-1.5 text-[var(--color-foreground-muted)]">
                      <Users size={14} /> {lista.total_contatos} contato(s)
                    </span>
                    {lista.ultimo_disparo ? (
                      <span className="text-xs text-[var(--color-foreground-muted)]">
                        Último disparo: {new Date(lista.ultimo_disparo).toLocaleDateString("pt-BR")}
                      </span>
                    ) : (
                      <span className="text-xs text-[var(--color-foreground-muted)]">Sem disparos</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* VIEW: CONTATOS */}
      {view === "contatos" && selectedLista && (
        <div className="space-y-6">
          {/* Botão histórico */}
          <button
            onClick={() => setShowDisparos(!showDisparos)}
            className="flex items-center gap-2 text-sm text-[var(--color-foreground-muted)] hover:text-white transition-colors"
          >
            <History size={16} />
            {showDisparos ? "Ver Contatos" : `Histórico de Disparos (${disparos.length})`}
          </button>

          {showDisparos ? (
            /* Histórico de disparos */
            <div className="space-y-4">
              {disparos.length === 0 ? (
                <div className="glass-panel p-10 text-center text-[var(--color-foreground-muted)]">
                  <Send size={32} className="mx-auto mb-3 opacity-20" />
                  <p>Nenhum disparo realizado ainda.</p>
                </div>
              ) : disparos.map((d) => {
                const badge = STATUS_BADGE[d.status] || STATUS_BADGE.pendente;
                const BadgeIcon = badge.icon;
                return (
                  <div key={d.id} className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-5">
                    <div className="flex items-start justify-between mb-3">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${badge.color}`}>
                        <BadgeIcon size={12} className={d.status === "enviando" ? "animate-spin" : ""} />
                        {badge.label}
                      </span>
                      <div className="flex flex-col items-end">
                        <span className="text-xs text-white">
                          {d.data_programada ? new Date(d.data_programada).toLocaleDateString("pt-BR") : new Date(d.criado_em || Date.now()).toLocaleDateString("pt-BR")}
                        </span>
                        <span className="text-[10px] text-[var(--color-foreground-muted)]">
                          {d.data_programada ? new Date(d.data_programada).toLocaleTimeString("pt-BR", {hour: '2-digit', minute: '2-digit'}) : new Date(d.criado_em || Date.now()).toLocaleTimeString("pt-BR", {hour: '2-digit', minute: '2-digit'})}
                        </span>
                      </div>
                    </div>
                    <p className="text-white text-sm mb-4 bg-[var(--color-background)] rounded-xl p-3 whitespace-pre-wrap">{d.mensagem}</p>
                    <div className="flex gap-4 text-sm text-[var(--color-foreground-muted)]">
                      <span className="flex items-center gap-1"><Users size={13} /> {d.total_contatos} total</span>
                      <span className="flex items-center gap-1 text-emerald-400"><CheckCircle2 size={13} /> {d.enviados} enviados</span>
                      {d.erros > 0 && <span className="flex items-center gap-1 text-red-400"><AlertCircle size={13} /> {d.erros} erros</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Lista de contatos */
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden">
              <div className="p-5 border-b border-[var(--color-border)]">
                <p className="text-sm text-[var(--color-foreground-muted)]">{contatos.length} contato(s) nesta lista</p>
              </div>
              {contatos.length === 0 ? (
                <div className="py-16 text-center">
                  <Users size={40} className="mx-auto mb-3 opacity-20 text-[var(--color-foreground-muted)]" />
                  <p className="text-[var(--color-foreground-muted)]">Nenhum contato adicionado ainda.</p>
                  <button
                    onClick={() => { setFormContato({ nome: "", telefone: "" }); setBusca(""); setResultadosBusca([]); setModal("add_contato"); }}
                    className="mt-4 px-4 py-2 bg-[var(--color-brand-500)]/10 text-[var(--color-brand-400)] rounded-xl text-sm font-semibold hover:bg-[var(--color-brand-500)]/20 transition-all"
                  >
                    + Adicionar primeiro contato
                  </button>
                </div>
              ) : (
                <div className="divide-y divide-[var(--color-border)]">
                  {contatos.map((c) => (
                    <div key={c.id} className="flex items-center justify-between px-6 py-3.5 hover:bg-[var(--color-surface-hover)]/30 transition-colors group">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-[var(--color-brand-500)]/10 flex items-center justify-center text-[var(--color-brand-400)] text-sm font-bold">
                          {(c.nome || c.telefone).charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="text-white font-medium text-sm">{c.nome || "—"}</p>
                          <p className="text-xs text-[var(--color-foreground-muted)]">{c.telefone}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => removerContato(c.id)}
                        className="p-1.5 text-[var(--color-foreground-muted)] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Modal: Nova Lista */}
      {modal === "nova_lista" && (
        <ModalWrapper title="Nova Lista de Transmissão" icon={<ListFilter size={20} className="text-violet-400" />} onClose={() => setModal(null)} disabled={saving}>
          <form onSubmit={criarLista} className="space-y-3 p-4">
            <div>
              <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">Nome da Lista *</label>
              <input
                required autoFocus
                value={formLista.nome}
                onChange={(e) => setFormLista({ ...formLista, nome: e.target.value })}
                placeholder="Ex: Clientes Europa 2025"
                className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">Descrição</label>
              <textarea
                rows={2}
                value={formLista.descricao}
                onChange={(e) => setFormLista({ ...formLista, descricao: e.target.value })}
                placeholder="Descrição opcional da lista..."
                className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 resize-none"
              />
            </div>
            <ModalFooter onCancel={() => setModal(null)} saving={saving} label="Criar Lista" />
          </form>
        </ModalWrapper>
      )}

      {/* Modal: Adicionar Contato */}
      {modal === "add_contato" && (
        <ModalWrapper title="Adicionar Contato" icon={<UserPlus size={20} className="text-[var(--color-brand-400)]" />} onClose={() => setModal(null)} disabled={saving}>
          <div className="p-4 space-y-4">
            
            {/* Seção de Busca Inteligente */}
            <div className="relative">
              <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">
                Buscar Cliente Cadastrado
              </label>
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" />
                <input
                  autoFocus
                  value={busca}
                  onChange={(e) => setBusca(e.target.value)}
                  placeholder="Digite o nome ou telefone..."
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-xl py-2 pl-9 pr-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:border-[var(--color-brand-500)] transition-all"
                />
                {buscando && (
                  <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-brand-500)] animate-spin" />
                )}
              </div>
              
              {resultadosBusca.length > 0 && (
                <div className="absolute z-[110] w-full mt-1 bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-xl shadow-2xl max-h-48 overflow-y-auto">
                  {resultadosBusca.map((r, i) => (
                    <div 
                      key={i} 
                      className="px-4 py-2 hover:bg-[var(--color-brand-500)]/20 cursor-pointer flex flex-col transition-colors border-b border-[var(--color-border)]/50 last:border-0"
                      onClick={() => {
                        setFormContato({ nome: r.nome, telefone: r.telefone });
                        setBusca("");
                        setResultadosBusca([]);
                      }}
                    >
                      <span className="text-sm font-bold text-white">{r.nome}</span>
                      <span className="text-xs text-[var(--color-foreground-muted)]">{r.telefone}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-4 py-1 opacity-50">
              <div className="h-px bg-[var(--color-foreground-muted)] flex-1"></div>
              <span className="text-[10px] text-[var(--color-foreground-muted)] uppercase tracking-wider font-bold">DADOS DO CONTATO</span>
              <div className="h-px bg-[var(--color-foreground-muted)] flex-1"></div>
            </div>

            {/* Formulário de Adição */}
            <form onSubmit={adicionarContato} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">
                  Telefone (WhatsApp) *
                  <span className="ml-1 text-xs text-[var(--color-foreground-muted)]/60">Ex: 11999999999</span>
                </label>
                <input
                  required
                  value={formContato.telefone}
                  onChange={(e) => setFormContato({ ...formContato, telefone: e.target.value })}
                  placeholder="DDD + número"
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50"
                />
            </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">Nome (opcional)</label>
                <input
                  value={formContato.nome}
                  onChange={(e) => setFormContato({ ...formContato, nome: e.target.value })}
                  placeholder="Nome do contato"
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50"
                />
                <p className="text-xs text-[var(--color-foreground-muted)] mt-1">
                  Selecione na busca acima ou digite manualmente.
                </p>
              </div>
              <ModalFooter onCancel={() => setModal(null)} saving={saving} label="Adicionar na Lista" />
            </form>
          </div>
        </ModalWrapper>
      )}

      {/* Modal: Disparar Mensagem */}
      {modal === "disparar" && selectedLista && (
        <ModalWrapper title={`Disparar para "${selectedLista.nome}"`} icon={<Send size={20} className="text-violet-400" />} onClose={() => setModal(null)} disabled={saving}>
          <form onSubmit={disparar} className="space-y-3 p-4">
            <div className="p-3 bg-violet-500/10 border border-violet-500/20 rounded-xl">
              <p className="text-sm text-violet-300 font-medium">
                📣 Esta mensagem será enviada para <strong>{selectedLista.total_contatos} contato(s)</strong> com intervalo de 5-10s entre envios.
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1">Mensagem *</label>
              <textarea
                required autoFocus
                rows={3}
                value={formDisparo.mensagem}
                onChange={(e) => setFormDisparo({ ...formDisparo, mensagem: e.target.value })}
                placeholder="Digite a mensagem que será enviada para todos os contatos da lista..."
                className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 resize-none"
              />
            </div>
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--color-foreground-muted)] flex items-center gap-2">
                  <ImageIcon size={14} className="text-[var(--color-brand-400)]" />
                  Imagem / Anexo (Opcional)
                </label>
                <div className="flex items-center gap-3">
                  <label className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-[var(--color-background)] border-2 border-dashed border-[var(--color-border)] hover:border-[var(--color-brand-500)]/50 rounded-xl cursor-pointer transition-all">
                    <input 
                      type="file" 
                      className="hidden" 
                      accept="image/*"
                      onChange={handleUpload}
                    />
                    {uploading ? (
                      <Loader2 className="animate-spin text-[var(--color-brand-400)]" size={20} />
                    ) : (
                      <ImageIcon size={20} className="text-[var(--color-foreground-muted)]" />
                    )}
                    <span className="text-sm text-[var(--color-foreground-muted)]">
                      {formDisparo.imagem_url ? "Alterar imagem" : "Clique para anexar imagem"}
                    </span>
                  </label>
                  {formDisparo.imagem_url && (
                    <button 
                      type="button"
                      onClick={() => setFormDisparo({ ...formDisparo, imagem_url: "" })}
                      className="p-3 text-red-400 hover:bg-red-400/10 rounded-xl transition-colors"
                    >
                      <Trash2 size={20} />
                    </button>
                  )}
                </div>
              </div>

              {formDisparo.imagem_url && (
                <div className="relative aspect-video w-full bg-[var(--color-background)] rounded-xl overflow-hidden border border-[var(--color-border)] group">
                  <img 
                    src={formDisparo.imagem_url.startsWith('http') ? formDisparo.imagem_url : `${apiBaseUrl}${formDisparo.imagem_url}`} 
                    alt="Preview" 
                    className="w-full h-full object-cover"
                    onError={(e) => (e.currentTarget.style.display = 'none')}
                  />
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="text-xs text-white font-medium">Prévia da Imagem</span>
                  </div>
                </div>
              )}
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--color-foreground-muted)] mb-1 flex items-center gap-2">
                <Calendar size={14} className="text-[var(--color-brand-400)]" />
                Programar Envio (Opcional)
              </label>
              <input 
                type="datetime-local"
                value={formDisparo.data_programada}
                onChange={(e) => setFormDisparo({ ...formDisparo, data_programada: e.target.value })}
                className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50"
              />
            </div>
            <ModalFooter onCancel={() => setModal(null)} saving={saving} label={formDisparo.data_programada ? "Agendar Disparo" : "Enviar Agora"} labelColor="bg-violet-600 hover:bg-violet-700" />
          </form>
        </ModalWrapper>
      )}
    </div>
  );
}

/* Sub-componentes internos */
function ModalWrapper({ title, icon, onClose, disabled, children }: {
  title: string; icon: React.ReactNode; onClose: () => void; disabled: boolean; children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => !disabled && onClose()} />
      <div className="relative bg-[var(--color-surface)] border border-[var(--color-border)] w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-between">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">{icon}{title}</h3>
          <button onClick={onClose} disabled={disabled} className="text-[var(--color-foreground-muted)] hover:text-white"><X size={24} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

function ModalFooter({ onCancel, saving, label, labelColor }: {
  onCancel: () => void; saving: boolean; label: string; labelColor?: string;
}) {
  const btnColor = labelColor || "bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)]";
  return (
    <div className="flex gap-3 pt-1">
      <button type="button" onClick={onCancel} disabled={saving} className="flex-1 py-2.5 bg-[var(--color-surface-hover)] hover:bg-[var(--color-border)] text-white rounded-xl font-semibold transition-all">
        Cancelar
      </button>
      <button type="submit" disabled={saving} className={`flex-1 py-2.5 ${btnColor} disabled:opacity-50 text-white rounded-xl font-bold transition-all shadow-lg`}>
        {saving ? "Processando..." : label}
      </button>
    </div>
  );
}
