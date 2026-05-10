"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { 
  Users, 
  Plus, 
  Settings, 
  CheckCircle2, 
  XCircle, 
  Calendar, 
  DollarSign, 
  Tag, 
  ArrowRight,
  ShieldCheck
} from "lucide-react";

interface Empresa {
  id: string;
  nome: string;
  slug: string;
  ativo: boolean;
  valor_mensalidade: number;
  data_expiracao_teste: string;
  data_criacao: string;
}

export default function AdminPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [adminToken, setAdminToken] = useState("");
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    nome: "",
    slug: "",
    telefone_whatsapp: "",
    telefone_proprietario: "",
    valor_mensalidade: 197.00,
    dias_teste: 30,
    cupom_vendedor: ""
  });

  async function fetchEmpresas() {
    try {
      const response = await api.get("/api/admin/empresas", {
        headers: { "X-Admin-Token": adminToken }
      });
      setEmpresas(response.data);
      setIsAuthorized(true);
    } catch (err) {
      alert("Token de Admin inválido ou erro na busca.");
    }
  }

  async function handleCreateEmpresa(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/api/admin/empresas", formData, {
        headers: { "X-Admin-Token": adminToken }
      });
      alert("Academia cadastrada com sucesso!");
      setShowModal(false);
      fetchEmpresas();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erro ao cadastrar.");
    } finally {
      setLoading(false);
    }
  }

  async function toggleStatus(id: string) {
    try {
      await api.patch(`/api/admin/empresas/${id}/status`, {}, {
        headers: { "X-Admin-Token": adminToken }
      });
      fetchEmpresas();
    } catch (err) {
      alert("Erro ao alterar status.");
    }
  }

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center p-6 text-white">
        <div className="glass-panel p-8 w-full max-w-md space-y-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="p-4 rounded-full bg-blue-500/10 text-blue-400">
              <ShieldCheck size={48} />
            </div>
            <h1 className="text-2xl font-bold">Acesso Restrito - ADM</h1>
            <p className="text-slate-400">Insira o seu Token Master para gerenciar a rede AtendIA.</p>
          </div>
          <div className="space-y-4">
            <input 
              type="password"
              placeholder="Digite o Token Master..."
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-all"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
            />
            <button 
              onClick={fetchEmpresas}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-semibold transition-all"
            >
              Entrar na Central
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)] p-6 md:p-12 text-white">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-600/20">
              <Users size={32} />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Central do Franqueador</h1>
              <p className="text-slate-400">Gerencie o onboarding e o faturamento das suas academias.</p>
            </div>
          </div>
          <button 
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-semibold transition-all shadow-lg shadow-blue-600/20"
          >
            <Plus size={20} />
            Novo Cliente
          </button>
        </header>

        {/* Tabela de Empresas */}
        <div className="glass-panel overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-[var(--color-surface)] border-b border-[var(--color-border)]">
                <th className="p-6 text-sm font-semibold text-slate-400">Academia</th>
                <th className="p-6 text-sm font-semibold text-slate-400">URL / Slug</th>
                <th className="p-6 text-sm font-semibold text-slate-400">Mensalidade</th>
                <th className="p-6 text-sm font-semibold text-slate-400">Expiração Teste</th>
                <th className="p-6 text-sm font-semibold text-slate-400">Status</th>
                <th className="p-6 text-sm font-semibold text-slate-400 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {empresas.map((emp) => (
                <tr key={emp.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="p-6">
                    <span className="font-bold text-lg">{emp.nome}</span>
                  </td>
                  <td className="p-6 text-blue-400 font-mono text-sm">
                    /{emp.slug}
                  </td>
                  <td className="p-6">
                    <div className="flex items-center gap-2">
                      <DollarSign size={16} className="text-green-400" />
                      <span>R$ {emp.valor_mensalidade.toFixed(2)}</span>
                    </div>
                  </td>
                  <td className="p-6">
                    <div className="flex items-center gap-2 text-slate-400 text-sm">
                      <Calendar size={16} />
                      <span>{emp.data_expiracao_teste ? new Date(emp.data_expiracao_teste).toLocaleDateString() : "Ilimitado"}</span>
                    </div>
                  </td>
                  <td className="p-6">
                    {emp.ativo ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-xs font-bold border border-green-500/20">
                        <CheckCircle2 size={12} /> ATIVO
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/10 text-red-400 text-xs font-bold border border-red-500/20">
                        <XCircle size={12} /> INATIVO
                      </span>
                    )}
                  </td>
                  <td className="p-6 text-right">
                    <button 
                      onClick={() => toggleStatus(emp.id)}
                      className="p-2 hover:bg-white/10 rounded-lg text-slate-400 transition-colors"
                      title={emp.ativo ? "Desativar" : "Ativar"}
                    >
                      <Settings size={20} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de Onboarding */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-2xl overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-[var(--color-border)] flex justify-between items-center bg-blue-600/10">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Plus className="text-blue-400" />
                Cadastrar Novo Cliente
              </h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">Feche</button>
            </div>
            
            <form onSubmit={handleCreateEmpresa} className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Nome da Academia</label>
                <input 
                  required
                  placeholder="Ex: Prime Fit Studio"
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.nome}
                  onChange={(e) => setFormData({...formData, nome: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Slug (URL)</label>
                <input 
                  required
                  placeholder="Ex: primefit"
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.slug}
                  onChange={(e) => setFormData({...formData, slug: e.target.value.toLowerCase().replace(/ /g, "-")})}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">WhatsApp da Unidade</label>
                <input 
                  required
                  placeholder="Ex: 5511999999999"
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.telefone_whatsapp}
                  onChange={(e) => setFormData({...formData, telefone_whatsapp: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">WhatsApp do Proprietário</label>
                <input 
                  placeholder="Ex: 5511888888888"
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.telefone_proprietario}
                  onChange={(e) => setFormData({...formData, telefone_proprietario: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Valor Mensal (R$)</label>
                <input 
                  type="number"
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.valor_mensalidade}
                  onChange={(e) => setFormData({...formData, valor_mensalidade: parseFloat(e.target.value)})}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Dias de Teste Grátis</label>
                <input 
                  type="number"
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.dias_teste}
                  onChange={(e) => setFormData({...formData, dias_teste: parseInt(e.target.value)})}
                />
              </div>

              <div className="col-span-full space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Tag size={14} /> Cupom de Vendedor
                </label>
                <input 
                  placeholder="Ex: VENDEDOR_JOAO"
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.cupom_vendedor}
                  onChange={(e) => setFormData({...formData, cupom_vendedor: e.target.value})}
                />
              </div>

              <div className="col-span-full pt-4">
                <button 
                  type="submit"
                  disabled={loading}
                  className="w-full py-4 bg-blue-600 hover:bg-blue-700 rounded-xl font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? "Processando..." : "Criar Academia e Ativar SaaS"}
                  <ArrowRight size={20} />
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
