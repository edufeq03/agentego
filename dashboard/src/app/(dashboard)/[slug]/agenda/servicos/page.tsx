"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { 
  Plus, 
  Trash2, 
  Edit3, 
  Clock, 
  DollarSign, 
  Tag, 
  Layers, 
  X, 
  CheckCircle2, 
  AlertCircle 
} from "lucide-react";
import api from "@/lib/api";

interface Servico {
  id: string;
  nome: string;
  descricao: string;
  duracao_min: number;
  preco: number | null;
  ativo: boolean;
  cor: string;
  ordem: number;
}

export default function ServicosPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [servicos, setServicos] = useState<Servico[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [isOpen, setIsOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  
  // Form states
  const [nome, setNome] = useState("");
  const [descricao, setDescricao] = useState("");
  const [duracaoMin, setDuracaoMin] = useState(30);
  const [preco, setPreco] = useState<string>("");
  const [ativo, setAtivo] = useState(true);
  const [cor, setCor] = useState("#3b82f6");
  const [ordem, setOrdem] = useState(0);

  const coresPreset = [
    "#3b82f6", // Azul
    "#10b981", // Verde
    "#f59e0b", // Amarelo/Laranja
    "#ef4444", // Vermelho
    "#8b5cf6", // Roxo
    "#ec4899", // Rosa
    "#06b6d4", // Ciano
    "#6b7280"  // Cinza
  ];

  useEffect(() => {
    fetchServicos();
  }, []);

  async function fetchServicos() {
    try {
      const res = await api.get("dashboard/agenda/servicos");
      setServicos(res.data);
    } catch (err) {
      console.error("Erro ao carregar serviços:", err);
    } finally {
      setLoading(false);
    }
  }

  function handleOpenNew() {
    setEditId(null);
    setNome("");
    setDescricao("");
    setDuracaoMin(30);
    setPreco("");
    setAtivo(true);
    setCor("#3b82f6");
    setOrdem(0);
    setIsOpen(true);
  }

  function handleOpenEdit(s: Servico) {
    setEditId(s.id);
    setNome(s.nome);
    setDescricao(s.descricao || "");
    setDuracaoMin(s.duracao_min);
    setPreco(s.preco !== null ? s.preco.toString() : "");
    setAtivo(s.ativo);
    setCor(s.cor || "#3b82f6");
    setOrdem(s.ordem);
    setIsOpen(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload = {
      nome,
      descricao,
      duracao_min: duracaoMin,
      preco: preco ? parseFloat(preco) : null,
      ativo,
      cor,
      ordem
    };

    try {
      if (editId) {
        await api.put(`dashboard/agenda/servicos/${editId}`, payload);
      } else {
        await api.post("dashboard/agenda/servicos", payload);
      }
      setIsOpen(false);
      fetchServicos();
    } catch (err) {
      alert("Erro ao salvar serviço. Verifique os dados.");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Tem certeza que deseja excluir este serviço?")) return;
    try {
      await api.delete(`dashboard/agenda/servicos/${id}`);
      fetchServicos();
    } catch (err) {
      alert("Erro ao excluir serviço.");
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Serviços</h2>
          <p className="text-[var(--color-foreground-muted)] mt-1">
            Cadastre os serviços oferecidos e configure a duração e valores.
          </p>
        </div>
        <button 
          onClick={handleOpenNew}
          className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-xl font-semibold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
        >
          <Plus size={18} />
          Adicionar Serviço
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-[var(--color-foreground-muted)]">Carregando serviços...</div>
      ) : servicos.length === 0 ? (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-12 text-center">
          <Layers className="mx-auto text-[var(--color-foreground-muted)] mb-4" size={48} />
          <h3 className="text-lg font-bold text-white">Nenhum serviço cadastrado</h3>
          <p className="text-[var(--color-foreground-muted)] mt-1 max-w-md mx-auto">
            Comece cadastrando seu primeiro serviço para que seus clientes possam agendar horários online.
          </p>
          <button 
            onClick={handleOpenNew}
            className="mt-6 px-4 py-2 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-xl font-semibold transition-all"
          >
            Cadastrar Serviço
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {servicos.map((s) => (
            <div 
              key={s.id} 
              className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 relative flex flex-col justify-between hover:border-[var(--color-brand-500)]/50 transition-all group"
            >
              {/* Card Color Indicator Top */}
              <div 
                className="absolute top-0 left-0 right-0 h-2 rounded-t-2xl" 
                style={{ backgroundColor: s.cor || "#3b82f6" }}
              />

              <div className="pt-2">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-xl font-bold text-white truncate">{s.nome}</h3>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                    s.ativo ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                  }`}>
                    {s.ativo ? "Ativo" : "Inativo"}
                  </span>
                </div>
                <p className="text-sm text-[var(--color-foreground-muted)] mt-2 line-clamp-2 h-10">
                  {s.descricao || "Sem descrição disponível."}
                </p>

                <div className="grid grid-cols-2 gap-4 mt-6">
                  <div className="flex items-center gap-2 text-sm text-[var(--color-foreground-muted)]">
                    <Clock size={16} className="text-[var(--color-brand-400)]" />
                    <span>{s.duracao_min} min</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-[var(--color-foreground-muted)]">
                    <DollarSign size={16} className="text-[var(--color-brand-400)]" />
                    <span>{s.preco !== null ? `R$ ${s.preco.toFixed(2)}` : "Gratuito"}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 border-t border-[var(--color-border)] mt-6 pt-4">
                <button 
                  onClick={() => handleOpenEdit(s)}
                  className="p-2 text-[var(--color-foreground-muted)] hover:text-white hover:bg-[var(--color-surface-hover)] rounded-lg transition-colors"
                  title="Editar"
                >
                  <Edit3 size={18} />
                </button>
                <button 
                  onClick={() => handleDelete(s.id)}
                  className="p-2 text-[var(--color-foreground-muted)] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                  title="Excluir"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal / Slider Side Panel for Add/Edit */}
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsOpen(false)} />
          <div className="relative bg-[var(--color-surface)] border border-[var(--color-border)] w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-[var(--color-border)] flex items-center justify-between">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Tag className="text-[var(--color-brand-400)]" />
                {editId ? "Editar Serviço" : "Novo Serviço"}
              </h3>
              <button 
                onClick={() => setIsOpen(false)}
                className="text-[var(--color-foreground-muted)] hover:text-white"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-white block">Nome do Serviço</label>
                <input 
                  type="text" 
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  placeholder="Ex: Consulta Geral, Corte de Cabelo..."
                  required
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-4 text-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-white block">Descrição (Opcional)</label>
                <textarea 
                  value={descricao}
                  onChange={(e) => setDescricao(e.target.value)}
                  placeholder="Diga mais sobre o serviço..."
                  rows={3}
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-4 text-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-white block">Duração (Minutos)</label>
                  <input 
                    type="number" 
                    value={duracaoMin}
                    onChange={(e) => setDuracaoMin(parseInt(e.target.value) || 15)}
                    min={5}
                    max={480}
                    required
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-4 text-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-white block">Preço R$ (Opcional)</label>
                  <input 
                    type="number" 
                    step="0.01"
                    value={preco}
                    onChange={(e) => setPreco(e.target.value)}
                    placeholder="Ex: 150.00"
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-4 text-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-white block">Cor de Exibição</label>
                <div className="flex flex-wrap gap-2.5">
                  {coresPreset.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setCor(c)}
                      className={`w-8 h-8 rounded-full border-2 transition-all ${
                        cor === c ? "border-white scale-110 shadow-lg" : "border-transparent opacity-80 hover:opacity-100"
                      }`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-white block">Ordem</label>
                  <input 
                    type="number" 
                    value={ordem}
                    onChange={(e) => setOrdem(parseInt(e.target.value) || 0)}
                    required
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-4 text-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all"
                  />
                </div>
                <div className="space-y-2 flex flex-col justify-end pb-1.5">
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      id="ativo"
                      checked={ativo}
                      onChange={(e) => setAtivo(e.target.checked)}
                      className="w-5 h-5 accent-[var(--color-brand-500)] rounded bg-[var(--color-background)] border border-[var(--color-border)]"
                    />
                    <label htmlFor="ativo" className="text-sm font-semibold text-white cursor-pointer select-none">
                      Serviço Ativo
                    </label>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--color-border)]">
                <button 
                  type="button" 
                  onClick={() => setIsOpen(false)}
                  className="px-5 py-2.5 bg-[var(--color-surface-hover)] hover:bg-[var(--color-border)] text-white rounded-xl font-semibold transition-all"
                >
                  Cancelar
                </button>
                <button 
                  type="submit"
                  className="px-5 py-2.5 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-xl font-semibold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
                >
                  {editId ? "Salvar Alterações" : "Criar Serviço"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
