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
  ShieldCheck,
  Trash2,
  ExternalLink
} from "lucide-react";

interface Empresa {
  id: string;
  nome: string;
  slug: string;
  ativo: boolean;
  valor_mensalidade: number;
  data_expiracao_teste: string;
  data_criacao: string;
  plano: string;
  limite_conversas_mes: number;
  conversas_mes_atual: number;
  tokens_input_mes: number;
  tokens_output_mes: number;
  custo_estimado_usd: number;
}

interface Template {
  id: string;
  nome_nicho: string;
  prompt_sistema: string;
  tom_voz: string;
  missao: string;
  objetivo: string;
  etapas_funil?: string[];
}

export default function AdminPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [activeTab, setActiveTab] = useState<"empresas" | "templates">("empresas");
  const [adminToken, setAdminToken] = useState("");
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");

  // Form State
  const [formData, setFormData] = useState({
    nome: "",
    slug: "",
    telefone_whatsapp: "",
    telefone_proprietario: "",
    valor_mensalidade: 197.00,
    dias_teste: 30,
    cupom_vendedor: "",
    template_id: "",
    email_admin: "",
    senha_admin: "",
    plano: "trial",
    limite_conversas_mes: 100
  });

  const [templateData, setTemplateData] = useState({
    nome_nicho: "",
    prompt_sistema: "",
    tom_voz: "",
    missao: "",
    objetivo: "",
    etapas_funil: "novo, curioso, interessado, agendado"
  });

  async function fetchData() {
    try {
      const [resEmpresas, resTemplates] = await Promise.all([
        api.get("admin/empresas", { headers: { "X-Admin-Token": adminToken } }),
        api.get("admin/templates", { headers: { "X-Admin-Token": adminToken } })
      ]);
      setEmpresas(resEmpresas.data);
      setTemplates(resTemplates.data);
      setIsAuthorized(true);
    } catch (err) {
      alert("Token de Admin inválido ou erro na busca.");
    }
  }

  async function handleCreateEmpresa(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("admin/empresas", formData, {
        headers: { "X-Admin-Token": adminToken }
      });
      alert("Empresa cadastrada com sucesso!");
      setShowModal(false);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erro ao cadastrar.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateTemplate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...templateData,
        etapas_funil: templateData.etapas_funil.split(",").map(s => s.trim().toLowerCase())
      };
      if (editingTemplate) {
        await api.put(`admin/templates/${editingTemplate.id}`, payload, {
          headers: { "X-Admin-Token": adminToken }
        });
        alert("Template atualizado com sucesso!");
      } else {
        await api.post("admin/templates", payload, {
          headers: { "X-Admin-Token": adminToken }
        });
        alert("Template criado com sucesso!");
      }
      setShowTemplateModal(false);
      setEditingTemplate(null);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erro ao criar template.");
    } finally {
      setLoading(false);
    }
  }

  async function toggleStatus(id: string) {
    try {
      await api.patch(`admin/empresas/${id}/status`, {}, {
        headers: { "X-Admin-Token": adminToken }
      });
      fetchData();
    } catch (err) {
      alert("Erro ao alterar status.");
    }
  }

  async function handleDeleteEmpresa(id: string, nome: string) {
    if (!confirm(`TEM CERTEZA? Isso apagará permanentemente a empresa "${nome}" e todos os seus dados.`)) {
      return;
    }

    try {
      await api.delete(`admin/empresas/${id}`, {
        headers: { "X-Admin-Token": adminToken }
      });
      fetchData();
    } catch (err) {
      alert("Erro ao excluir empresa.");
    }
  }

  async function handleDeleteTemplate(id: string, nome: string) {
    if (!confirm(`TEM CERTEZA? Isso apagará permanentemente o template "${nome}".`)) {
      return;
    }

    try {
      await api.delete(`admin/templates/${id}`, {
        headers: { "X-Admin-Token": adminToken }
      });
      fetchData();
    } catch (err) {
      alert("Erro ao excluir template. Certifique-se que o backend suporta esta operação.");
    }
  }

  async function handleImpersonate(id: string) {
    try {
      const response = await api.post(`admin/empresas/${id}/impersonate`, {}, {
        headers: { "X-Admin-Token": adminToken }
      });
      
      const { access_token, slug } = response.data;
      
      // Abre em uma nova aba passando o token via URL
      const url = `/${slug}?_imp=${access_token}`;
      window.open(url, "_blank");
    } catch (err) {
      alert("Erro ao acessar dashboard do cliente.");
    }
  }

  const filteredEmpresas = empresas.filter(emp => {
    const matchesSearch = emp.nome.toLowerCase().includes(searchTerm.toLowerCase()) || 
                         emp.slug.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" ? true : 
                         statusFilter === "active" ? emp.ativo : !emp.ativo;
    return matchesSearch && matchesStatus;
  });

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center p-6 text-white">
        <div className="glass-panel p-8 w-full max-w-md space-y-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="p-4 rounded-full bg-blue-500/10 text-blue-400">
              <ShieldCheck size={48} />
            </div>
            <h1 className="text-2xl font-bold">Acesso Restrito - ADM</h1>
            <p className="text-slate-400">Insira o seu Token Master para gerenciar a rede AgenteGo.</p>
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
              onClick={fetchData}
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
              <p className="text-slate-400">Gerencie o onboarding, faturamento e templates de nicho.</p>
            </div>
          </div>
          <div className="flex gap-3">
            {activeTab === "empresas" ? (
              <button 
                onClick={() => setShowModal(true)}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-semibold transition-all shadow-lg shadow-blue-600/20"
              >
                <Plus size={20} />
                Novo Cliente
              </button>
            ) : (
              <button 
                onClick={() => {
                  setEditingTemplate(null);
                  setTemplateData({
                    nome_nicho: "",
                    prompt_sistema: "",
                    tom_voz: "",
                    missao: "",
                    objetivo: "",
                    etapas_funil: "novo, curioso, interessado, agendado"
                  });
                  setShowTemplateModal(true);
                }}
                className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-xl font-semibold transition-all shadow-lg shadow-purple-600/20"
              >
                <Plus size={20} />
                Novo Template
              </button>
            )}
          </div>
        </header>

        {/* Tabs */}
        <div className="flex gap-4 border-b border-[var(--color-border)]">
          <button 
            onClick={() => setActiveTab("empresas")}
            className={`pb-4 px-2 font-bold transition-all border-b-2 ${activeTab === "empresas" ? "border-blue-500 text-blue-400" : "border-transparent text-slate-400 hover:text-white"}`}
          >
            Empresas ({empresas.length})
          </button>
          <button 
            onClick={() => setActiveTab("templates")}
            className={`pb-4 px-2 font-bold transition-all border-b-2 ${activeTab === "templates" ? "border-purple-500 text-purple-400" : "border-transparent text-slate-400 hover:text-white"}`}
          >
            Templates de Nicho ({templates.length})
          </button>
        </div>

        {activeTab === "empresas" ? (
          <div className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
              <div className="relative w-full md:w-96">
                <input 
                  type="text" 
                  placeholder="Buscar empresa ou slug..."
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-2 outline-none focus:border-blue-500 transition-all pl-10"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <Users className="absolute left-3 top-2.5 text-slate-500" size={18} />
              </div>
              <div className="flex gap-2 bg-[var(--color-surface)] p-1 rounded-xl border border-[var(--color-border)]">
                <button 
                  onClick={() => setStatusFilter("all")}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${statusFilter === 'all' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                >TODAS</button>
                <button 
                  onClick={() => setStatusFilter("active")}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${statusFilter === 'active' ? 'bg-green-600 text-white' : 'text-slate-400 hover:text-white'}`}
                >ATIVAS</button>
                <button 
                  onClick={() => setStatusFilter("inactive")}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${statusFilter === 'inactive' ? 'bg-red-600 text-white' : 'text-slate-400 hover:text-white'}`}
                >INATIVAS</button>
              </div>
            </div>

            <div className="glass-panel overflow-hidden">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-[var(--color-surface)] border-b border-[var(--color-border)]">
                    <th className="p-6 text-sm font-semibold text-slate-400">Empresa / Cliente</th>
                    <th className="p-6 text-sm font-semibold text-slate-400">URL / Slug</th>
                    <th className="p-6 text-sm font-semibold text-slate-400">Faturamento</th>
                    <th className="p-6 text-sm font-semibold text-slate-400">Status</th>
                    <th className="p-6 text-sm font-semibold text-slate-400 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-border)]">
                  {filteredEmpresas.map((emp) => (
                  <tr key={emp.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="p-6">
                      <div className="flex flex-col">
                        <span className="font-bold text-lg">{emp.nome}</span>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            emp.plano === 'trial' ? 'bg-yellow-500/20 text-yellow-500' :
                            emp.plano === 'starter' ? 'bg-blue-500/20 text-blue-500' :
                            emp.plano === 'pro' ? 'bg-green-500/20 text-green-500' :
                            'bg-purple-500/20 text-purple-400'
                          }`}>
                            {emp.plano}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {emp.conversas_mes_atual} / {emp.limite_conversas_mes} conv.
                          </span>
                        </div>
                        {/* Progress Bar */}
                        <div className="mt-2 h-1 w-32 bg-white/5 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all ${
                              (emp.conversas_mes_atual / emp.limite_conversas_mes) > 0.9 ? 'bg-red-500' :
                              (emp.conversas_mes_atual / emp.limite_conversas_mes) > 0.7 ? 'bg-yellow-500' :
                              'bg-blue-500'
                            }`}
                            style={{ width: `${Math.min(100, (emp.conversas_mes_atual / emp.limite_conversas_mes) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="p-6 text-blue-400 font-mono text-sm">
                      /{emp.slug}
                    </td>
                    <td className="p-6">
                      <div className="flex flex-col">
                        <div className="flex items-center gap-2">
                          <DollarSign size={14} className="text-green-400" />
                          <span className="font-bold">R$ {emp.valor_mensalidade.toFixed(2)}</span>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono mt-1">Custo IA: ${emp.custo_estimado_usd?.toFixed(2)}</span>
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
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => handleImpersonate(emp.id)}
                          className="p-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20"
                          title="Acessar Dashboard como Cliente"
                        >
                          <ExternalLink size={18} />
                        </button>
                        <button 
                          onClick={() => toggleStatus(emp.id)}
                          className={`p-2 rounded-lg transition-all border ${emp.ativo ? 'bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20' : 'bg-green-500/10 text-green-400 border-green-500/20 hover:bg-green-500/20'}`}
                        >
                          {emp.ativo ? <XCircle size={18} /> : <CheckCircle2 size={18} />}
                        </button>
                        <button 
                          onClick={() => handleDeleteEmpresa(emp.id, emp.nome)}
                          className="p-2 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500/20"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((t) => (
              <div key={t.id} className="glass-panel p-6 space-y-4 relative group">
                <div className="flex justify-between items-start">
                  <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                    <ShieldCheck size={24} />
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => {
                        setEditingTemplate(t);
                        setTemplateData({
                          nome_nicho: t.nome_nicho,
                          prompt_sistema: t.prompt_sistema,
                          tom_voz: t.tom_voz,
                          missao: t.missao,
                          objetivo: t.objetivo,
                          etapas_funil: t.etapas_funil ? t.etapas_funil.join(", ") : "novo, curioso, interessado, agendado"
                        });
                        setShowTemplateModal(true);
                      }}
                      className="p-1.5 hover:bg-purple-500/20 text-purple-400 rounded-lg transition-colors"
                      title="Editar Template"
                    >
                      <Settings size={18} />
                    </button>
                    <span className="text-xs font-bold bg-purple-500/20 px-2 py-1 rounded uppercase tracking-wider">Template</span>
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-bold">{t.nome_nicho}</h3>
                  <p className="text-slate-400 text-sm line-clamp-3 mt-1">{t.prompt_sistema}</p>
                </div>
                <div className="pt-4 flex flex-wrap gap-2">
                  <span className="text-[10px] px-2 py-0.5 bg-purple-500/10 rounded text-purple-300 border border-purple-500/20">TOM: {t.tom_voz || "Neutro"}</span>
                  {t.etapas_funil && t.etapas_funil.map(step => (
                    <span key={step} className="text-[10px] px-2 py-0.5 bg-blue-500/10 rounded text-blue-300 border border-blue-500/20">{step}</span>
                  ))}
                </div>
                <div className="pt-2">
                   <button 
                    onClick={() => handleDeleteTemplate(t.id, t.nome_nicho)}
                    className="flex items-center gap-1 text-[10px] text-red-400 hover:text-red-300 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={10} /> Excluir Template
                  </button>
                </div>
              </div>
            ))}
            {templates.length === 0 && (
              <div className="col-span-full py-12 text-center text-slate-500 glass-panel">
                Nenhum template cadastrado ainda. Comece criando o seu primeiro nicho!
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal Novo Cliente */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
          <div className="glass-panel w-full max-w-2xl my-auto">
            <div className="p-6 border-b border-[var(--color-border)] flex justify-between items-center bg-blue-600/10">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Plus className="text-blue-400" />
                Novo Cliente
              </h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">Fechar</button>
            </div>
            
            <form onSubmit={handleCreateEmpresa} className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="col-span-full space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Template de Nicho (Inteligência)</label>
                <select 
                  required
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.template_id}
                  onChange={(e) => setFormData({...formData, template_id: e.target.value})}
                >
                  <option value="">Selecione um Nicho...</option>
                  {templates.map(t => (
                    <option key={t.id} value={t.id}>{t.nome_nicho}</option>
                  ))}
                </select>
                <p className="text-[10px] text-slate-500">A IA deste cliente será inicializada com as regras deste template.</p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Nome da Empresa</label>
                <input required placeholder="Ex: Clínica Sorriso" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Slug (URL)</label>
                <input required placeholder="Ex: clinica-sorriso" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.slug} onChange={(e) => setFormData({...formData, slug: e.target.value.toLowerCase().replace(/ /g, "-")})} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">WhatsApp Unidade</label>
                <input required placeholder="5511999999999" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.telefone_whatsapp} onChange={(e) => setFormData({...formData, telefone_whatsapp: e.target.value})} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Mensalidade (R$)</label>
                <input type="number" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.valor_mensalidade} onChange={(e) => setFormData({...formData, valor_mensalidade: parseFloat(e.target.value)})} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Plano SaaS</label>
                <select className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.plano} onChange={(e) => {
                    const p = e.target.value;
                    const lim = p === 'starter' ? 500 : p === 'pro' ? 2000 : p === 'ilimitado' ? 999999 : 100;
                    setFormData({...formData, plano: p, limite_conversas_mes: lim});
                  }}>
                  <option value="trial">Trial (100 conversas)</option>
                  <option value="starter">Starter (500 conversas)</option>
                  <option value="pro">Pro (2.000 conversas)</option>
                  <option value="ilimitado">Ilimitado</option>
                </select>
              </div>

              <div className="col-span-full border-t border-white/5 pt-4">
                <h3 className="text-xs font-bold text-blue-400 uppercase tracking-[2px] mb-4">Credenciais de Acesso</h3>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">E-mail do Cliente</label>
                <input type="email" required placeholder="cliente@email.com" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.email_admin} onChange={(e) => setFormData({...formData, email_admin: e.target.value})} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Senha Inicial</label>
                <input type="password" required placeholder="••••••••" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-blue-500"
                  value={formData.senha_admin} onChange={(e) => setFormData({...formData, senha_admin: e.target.value})} />
              </div>

              <button type="submit" disabled={loading} className="col-span-full py-4 bg-blue-600 hover:bg-blue-700 rounded-xl font-bold transition-all flex items-center justify-center gap-2">
                {loading ? "Processando..." : "Ativar Empresa e Iniciar SaaS"}
                <ArrowRight size={20} />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal Novo Template */}
      {showTemplateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
          <div className="glass-panel w-full max-w-2xl my-auto">
            <div className="p-6 border-b border-[var(--color-border)] flex justify-between items-center bg-purple-600/10">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <ShieldCheck className="text-purple-400" />
                {editingTemplate ? `Editando: ${editingTemplate.nome_nicho}` : "Novo Template de Nicho"}
              </h2>
              <button onClick={() => { setShowTemplateModal(false); setEditingTemplate(null); }} className="text-slate-400 hover:text-white">Fechar</button>
            </div>
            
            <form onSubmit={handleCreateTemplate} className="p-8 space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Nome do Nicho</label>
                <input required placeholder="Ex: Imobiliária, Clínica de Estética..." className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-purple-500"
                  value={templateData.nome_nicho} onChange={(e) => setTemplateData({...templateData, nome_nicho: e.target.value})} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Prompt de Sistema (O Cérebro)</label>
                <textarea required rows={4} placeholder="Você é um assistente especializado em..." className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-purple-500"
                  value={templateData.prompt_sistema} onChange={(e) => setTemplateData({...templateData, prompt_sistema: e.target.value})} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider text-xs">Tom de Voz</label>
                  <input placeholder="Ex: Amigável" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-2 outline-none focus:border-purple-500"
                    value={templateData.tom_voz} onChange={(e) => setTemplateData({...templateData, tom_voz: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider text-xs">Missão</label>
                  <input placeholder="Ex: Vender pacotes" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-2 outline-none focus:border-purple-500"
                    value={templateData.missao} onChange={(e) => setTemplateData({...templateData, missao: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider text-xs">Objetivo</label>
                  <input placeholder="Ex: Agendar avaliação" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-2 outline-none focus:border-purple-500"
                    value={templateData.objetivo} onChange={(e) => setTemplateData({...templateData, objetivo: e.target.value})} />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Etapas do Funil (Separadas por vírgula)</label>
                <input required placeholder="Ex: Lead, Qualificado, Visita, Proposta, Venda" className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-3 outline-none focus:border-purple-500"
                  value={templateData.etapas_funil} onChange={(e) => setTemplateData({...templateData, etapas_funil: e.target.value})} />
                <p className="text-[10px] text-slate-500 italic">Essas serão as fases que aparecerão no gráfico do cliente.</p>
              </div>

              <button type="submit" disabled={loading} className="w-full py-4 bg-purple-600 hover:bg-purple-700 rounded-xl font-bold transition-all flex items-center justify-center gap-2">
                {loading ? "Processando..." : editingTemplate ? "Salvar Alterações" : "Salvar Template Mestre"}
                <CheckCircle2 size={20} />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
