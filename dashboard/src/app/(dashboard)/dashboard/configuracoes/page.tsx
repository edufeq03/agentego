"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Save, CheckCircle2, Plus, Trash2, Users, Dumbbell, MapPin, Sparkles, Clock } from "lucide-react";

interface Professor {
  nome: string;
  especialidade: string;
  bio: string;
}

interface Instalacao {
  nome: string;
  descricao: string;
}

interface AulaDetalhe {
  nome: string;
  descricao: string;
  horario: string;
}

interface ConfigData {
  nome_agente: string;
  nome_empresa: string;
  planos: { basico: number; vip: number };
  horarios: { semana: string; sabado: string };
  endereco: string;
  pagamentos: string[];
  aulas_vip: string[];
  professores: Professor[];
  instalacoes: Instalacao[];
  detalhes_aulas: AulaDetalhe[];
}

export default function Configuracoes() {
  const [config, setConfig] = useState<ConfigData>({
    nome_agente: "",
    nome_empresa: "",
    planos: { basico: 0, vip: 0 },
    horarios: { semana: "", sabado: "" },
    endereco: "",
    pagamentos: [],
    aulas_vip: [],
    professores: [],
    instalacoes: [],
    detalhes_aulas: []
  });
  
  const [pagamentosStr, setPagamentosStr] = useState("");
  const [aulasVipStr, setAulasVipStr] = useState("");
  const [webhookToken, setWebhookToken] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await api.get("/dashboard/config");
        const { config: configData, webhook_token, base_url } = response.data;
        
        if (configData && Object.keys(configData).length > 0) {
          setConfig({
            ...configData,
            professores: configData.professores || [],
            instalacoes: configData.instalacoes || [],
            detalhes_aulas: configData.detalhes_aulas || []
          });
          setPagamentosStr(configData.pagamentos ? configData.pagamentos.join(", ") : "");
          setAulasVipStr(configData.aulas_vip ? configData.aulas_vip.join(", ") : "");
        }
        setWebhookToken(webhook_token || "");
        setBaseUrl(base_url || "");
      } catch (error) {
        console.error("Erro ao buscar configurações:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const copyWebhook = () => {
    const url = `${baseUrl}/webhook/${webhookToken}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    
    try {
      const configToSave = {
        ...config,
        pagamentos: pagamentosStr.split(",").map(s => s.trim()).filter(s => s),
        aulas_vip: aulasVipStr.split(",").map(s => s.trim()).filter(s => s)
      };
      
      await api.put("/dashboard/config", configToSave);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Erro ao salvar:", error);
      alert("Erro ao salvar configurações.");
    } finally {
      setSaving(false);
    }
  };

  // Funções para manipular as listas estruturadas
  const addProfessor = () => {
    setConfig({
      ...config,
      professores: [...config.professores, { nome: "", especialidade: "", bio: "" }]
    });
  };

  const removeProfessor = (index: number) => {
    const newProfessores = [...config.professores];
    newProfessores.splice(index, 1);
    setConfig({ ...config, professores: newProfessores });
  };

  const updateProfessor = (index: number, field: keyof Professor, value: string) => {
    const newProfessores = [...config.professores];
    newProfessores[index] = { ...newProfessores[index], [field]: value };
    setConfig({ ...config, professores: newProfessores });
  };

  const addInstalacao = () => {
    setConfig({
      ...config,
      instalacoes: [...config.instalacoes, { nome: "", descricao: "" }]
    });
  };

  const removeInstalacao = (index: number) => {
    const newInstalacoes = [...config.instalacoes];
    newInstalacoes.splice(index, 1);
    setConfig({ ...config, instalacoes: newInstalacoes });
  };

  const updateInstalacao = (index: number, field: keyof Instalacao, value: string) => {
    const newInstalacoes = [...config.instalacoes];
    newInstalacoes[index] = { ...newInstalacoes[index], [field]: value };
    setConfig({ ...config, instalacoes: newInstalacoes });
  };

  const addAula = () => {
    setConfig({
      ...config,
      detalhes_aulas: [...config.detalhes_aulas, { nome: "", descricao: "", horario: "" }]
    });
  };

  const removeAula = (index: number) => {
    const newAulas = [...config.detalhes_aulas];
    newAulas.splice(index, 1);
    setConfig({ ...config, detalhes_aulas: newAulas });
  };

  const updateAula = (index: number, field: keyof AulaDetalhe, value: string) => {
    const newAulas = [...config.detalhes_aulas];
    newAulas[index] = { ...newAulas[index], [field]: value };
    setConfig({ ...config, detalhes_aulas: newAulas });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--color-brand-500)]"></div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-20">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Agent Builder</h2>
          <p className="text-[var(--color-foreground-muted)] mt-1">
            Modele o cérebro do seu agente e configure as integrações.
          </p>
        </div>
        
        <button 
          onClick={handleSave}
          disabled={saving}
          className="hidden md:flex items-center gap-2 bg-gradient-to-r from-[var(--color-brand-600)] to-[var(--color-brand-400)] hover:from-[var(--color-brand-500)] hover:to-[var(--color-brand-300)] text-white px-8 py-3 rounded-xl font-medium transition-all shadow-lg shadow-[var(--color-brand-500)]/20 disabled:opacity-50"
        >
          {saving ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" /> : saved ? <CheckCircle2 size={20} /> : <Save size={20} />}
          {saving ? "Salvando..." : saved ? "Salvo!" : "Salvar Tudo"}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* 1. Identidade e Localização */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex items-center gap-2 text-white font-semibold text-lg border-b border-[var(--color-border)] pb-3">
              <Sparkles className="text-yellow-400" size={20} />
              Identidade do Agente
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)] uppercase tracking-wider">Nome da Academia</label>
                <input 
                  type="text" 
                  value={config.nome_empresa}
                  onChange={e => setConfig({...config, nome_empresa: e.target.value})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)] uppercase tracking-wider">Nome da IA (ex: Rosana)</label>
                <input 
                  type="text" 
                  value={config.nome_agente}
                  onChange={e => setConfig({...config, nome_agente: e.target.value})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-[var(--color-foreground-muted)] uppercase tracking-wider">Endereço Físico</label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" size={16} />
                <input 
                  type="text" 
                  value={config.endereco}
                  onChange={e => setConfig({...config, endereco: e.target.value})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 pl-10 pr-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                />
              </div>
            </div>
          </section>

          {/* 2. Time de Professores (Estruturado) */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
              <div className="flex items-center gap-2 text-white font-semibold text-lg">
                <Users className="text-blue-400" size={20} />
                Time de Professores
              </div>
              <button 
                onClick={addProfessor}
                type="button"
                className="text-xs flex items-center gap-1 text-[var(--color-brand-400)] hover:text-[var(--color-brand-300)] transition-colors"
              >
                <Plus size={14} /> Adicionar Professor
              </button>
            </div>

            <div className="space-y-4">
              {config.professores.map((prof, index) => (
                <div key={index} className="bg-white/5 rounded-xl p-4 border border-[var(--color-border)] relative group">
                  <button 
                    onClick={() => removeProfessor(index)}
                    className="absolute -top-2 -right-2 bg-red-500/80 hover:bg-red-500 p-1.5 rounded-full text-white opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={12} />
                  </button>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input 
                      placeholder="Nome do Professor"
                      value={prof.nome}
                      onChange={e => updateProfessor(index, 'nome', e.target.value)}
                      className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                    />
                    <input 
                      placeholder="Especialidade (ex: Musculação, Yoga)"
                      value={prof.especialidade}
                      onChange={e => updateProfessor(index, 'especialidade', e.target.value)}
                      className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                    />
                    <textarea 
                      placeholder="Breve biografia ou diferenciais..."
                      value={prof.bio}
                      onChange={e => updateProfessor(index, 'bio', e.target.value)}
                      className="md:col-span-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] h-16 resize-none"
                    />
                  </div>
                </div>
              ))}
              {config.professores.length === 0 && (
                <p className="text-center text-sm text-[var(--color-foreground-muted)] py-4">Nenhum professor cadastrado ainda.</p>
              )}
            </div>
          </section>

          {/* 3. Detalhes das Aulas (Estruturado) */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
              <div className="flex items-center gap-2 text-white font-semibold text-lg">
                <Clock className="text-purple-400" size={20} />
                Grade e Detalhes de Aulas
              </div>
              <button 
                onClick={addAula}
                type="button"
                className="text-xs flex items-center gap-1 text-[var(--color-brand-400)] hover:text-[var(--color-brand-300)] transition-colors"
              >
                <Plus size={14} /> Adicionar Aula
              </button>
            </div>

            <div className="space-y-4">
              {config.detalhes_aulas.map((aula, index) => (
                <div key={index} className="bg-white/5 rounded-xl p-4 border border-[var(--color-border)] relative group">
                  <button 
                    onClick={() => removeAula(index)}
                    className="absolute -top-2 -right-2 bg-red-500/80 hover:bg-red-500 p-1.5 rounded-full text-white opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={12} />
                  </button>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input 
                      placeholder="Nome da Aula (ex: Spinning)"
                      value={aula.nome}
                      onChange={e => updateAula(index, 'nome', e.target.value)}
                      className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                    />
                    <input 
                      placeholder="Horários (ex: Terças e Quintas às 19h)"
                      value={aula.horario}
                      onChange={e => updateAula(index, 'horario', e.target.value)}
                      className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                    />
                    <textarea 
                      placeholder="Descrição do que o aluno vai fazer na aula..."
                      value={aula.descricao}
                      onChange={e => updateAula(index, 'descricao', e.target.value)}
                      className="md:col-span-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] h-16 resize-none"
                    />
                  </div>
                </div>
              ))}
              {config.detalhes_aulas.length === 0 && (
                <p className="text-center text-sm text-[var(--color-foreground-muted)] py-4">Nenhuma aula detalhada ainda.</p>
              )}
            </div>
          </section>
        </div>

        {/* Sidebar: Configurações Rápidas */}
        <div className="space-y-8">
          {/* Planos */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex items-center gap-2 text-white font-semibold text-lg border-b border-[var(--color-border)] pb-3">
              <Dumbbell className="text-orange-400" size={20} />
              Mensalidades / Preços
            </div>
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)]">Plano Básico (R$)</label>
                <input 
                  type="number" 
                  value={config.planos?.basico || 0}
                  onChange={e => setConfig({...config, planos: {...(config.planos || {}), basico: Number(e.target.value)}})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)]">Plano VIP / Premium (R$)</label>
                <input 
                  type="number" 
                  value={config.planos?.vip || 0}
                  onChange={e => setConfig({...config, planos: {...(config.planos || {}), vip: Number(e.target.value)}})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                />
              </div>
            </div>
          </section>

          {/* Horários */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex items-center gap-2 text-white font-semibold text-lg border-b border-[var(--color-border)] pb-3">
              <Clock className="text-green-400" size={20} />
              Horário de Funcionamento
            </div>
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)]">Segunda a Sexta</label>
                <input 
                  type="text" 
                  value={config.horarios?.semana || ""}
                  onChange={e => setConfig({...config, horarios: {...(config.horarios || {}), semana: e.target.value}})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                  placeholder="Ex: 08:00 as 18:00"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)]">Sábados / Feriados</label>
                <input 
                  type="text" 
                  value={config.horarios?.sabado || ""}
                  onChange={e => setConfig({...config, horarios: {...(config.horarios || {}), sabado: e.target.value}})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                  placeholder="Ex: 08:00 as 14:00"
                />
              </div>
            </div>
          </section>

          {/* Instalações (Estruturado) */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
              <div className="flex items-center gap-2 text-white font-semibold text-lg">
                <MapPin className="text-emerald-400" size={20} />
                Instalações
              </div>
              <button 
                onClick={addInstalacao}
                type="button"
                className="text-[10px] flex items-center gap-1 text-[var(--color-brand-400)] hover:text-[var(--color-brand-300)]"
              >
                <Plus size={12} /> Adicionar
              </button>
            </div>
            <div className="space-y-3">
              {config.instalacoes.map((inst, index) => (
                <div key={index} className="space-y-1 relative group">
                   <button 
                    onClick={() => removeInstalacao(index)}
                    className="absolute -top-1 -right-1 bg-red-500/80 p-1 rounded-full text-white opacity-0 group-hover:opacity-100 transition-all z-10"
                  >
                    <Trash2 size={10} />
                  </button>
                  <input 
                    placeholder="Diferencial (ex: Piscina)"
                    value={inst.nome}
                    onChange={e => updateInstalacao(index, 'nome', e.target.value)}
                    className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                  />
                  <input 
                    placeholder="Descrição rápida..."
                    value={inst.descricao}
                    onChange={e => updateInstalacao(index, 'descricao', e.target.value)}
                    className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1 px-3 text-[11px] text-[var(--color-foreground-muted)] focus:outline-none focus:border-[var(--color-brand-500)]"
                  />
                </div>
              ))}
            </div>
          </section>

          {/* Configuração de Integração (Webhook) */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex items-center gap-2 text-white font-semibold text-lg border-b border-[var(--color-border)] pb-3">
              <Plus className="text-brand-400 rotate-45" size={20} />
              Integração Técnica
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)] uppercase tracking-wider">Webhook URL (Evolution API)</label>
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    readOnly
                    value={`${baseUrl}/webhook/${webhookToken}`}
                    className="flex-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-2 px-3 text-xs text-[var(--color-foreground-muted)] focus:outline-none"
                  />
                  <button 
                    onClick={copyWebhook}
                    className="bg-[var(--color-surface-hover)] hover:bg-[var(--color-surface-active)] border border-[var(--color-border)] rounded-lg px-3 text-xs text-white transition-colors min-w-[80px]"
                  >
                    {copied ? "Copiado!" : "Copiar"}
                  </button>
                </div>
                <p className="text-[10px] text-[var(--color-foreground-muted)] leading-relaxed">
                  Cole esta URL na configuração de Webhook da sua instância na Evolution API para habilitar o robô.
                </p>
              </div>
            </div>
          </section>

          {/* Save Mobile */}
          <button 
            onClick={handleSave}
            disabled={saving}
            className="w-full md:hidden flex items-center justify-center gap-2 bg-gradient-to-r from-[var(--color-brand-600)] to-[var(--color-brand-400)] text-white px-8 py-4 rounded-xl font-medium transition-all shadow-lg"
          >
            {saving ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" /> : <Save size={20} />}
            {saving ? "Salvando..." : "Salvar Configurações"}
          </button>
        </div>
      </div>
    </div>
  );
}
