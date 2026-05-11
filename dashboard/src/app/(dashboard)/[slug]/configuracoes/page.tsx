"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Save, CheckCircle2, Plus, Trash2, Users, Dumbbell, MapPin, Sparkles, Clock } from "lucide-react";

interface Conhecimento {
  categoria: string;
  conteudo: string;
}

interface ConfigData {
  nome_agente: string;
  nome_empresa: string;
  endereco: string;
  horarios: { semana: string; sabado: string };
  faq: { pergunta: string; resposta: string }[];
  conhecimento: Conhecimento[];
  regras_comportamento: string[];
  timezone: string;
  // Campos legados mantidos para compatibilidade durante migração
  planos?: { basico: number; vip: number };
}

export default function Configuracoes() {
  const [config, setConfig] = useState<ConfigData>({
    nome_agente: "",
    nome_empresa: "",
    endereco: "",
    horarios: { semana: "", sabado: "" },
    faq: [],
    conhecimento: [],
    regras_comportamento: [],
    timezone: "America/Sao_Paulo"
  });
  
  const [webhookToken, setWebhookToken] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await api.get("dashboard/config");
        const { config: configData, webhook_token, base_url } = response.data;
        
        console.log("DADOS RECEBIDOS DA API:", configData);

        if (configData && Object.keys(configData).length > 0) {
          setConfig({
            ...configData,
            nome_agente: configData.nome_agente || "",
            nome_empresa: configData.nome_empresa || "",
            endereco: configData.endereco || "",
            horarios: {
              semana: configData.horarios?.semana || "",
              sabado: configData.horarios?.sabado || ""
            },
            faq: configData.faq || [],
            conhecimento: configData.conhecimento || [],
            regras_comportamento: configData.regras_comportamento || [],
            timezone: configData.timezone || "America/Sao_Paulo"
          });
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
      await api.put("dashboard/config", config);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Erro ao salvar:", error);
      alert("Erro ao salvar configurações.");
    } finally {
      setSaving(false);
    }
  };

  const addConhecimento = () => {
    setConfig({
      ...config,
      conhecimento: [...config.conhecimento, { categoria: "", conteudo: "" }]
    });
  };

  const removeConhecimento = (index: number) => {
    const newItems = [...config.conhecimento];
    newItems.splice(index, 1);
    setConfig({ ...config, conhecimento: newItems });
  };

  const updateConhecimento = (index: number, field: keyof Conhecimento, value: string) => {
    const newItems = [...config.conhecimento];
    newItems[index] = { ...newItems[index], [field]: value };
    setConfig({ ...config, conhecimento: newItems });
  };

  const addFAQ = () => {
    setConfig({
      ...config,
      faq: [...config.faq, { pergunta: "", resposta: "" }]
    });
  };

  const removeFAQ = (index: number) => {
    const newItems = [...config.faq];
    newItems.splice(index, 1);
    setConfig({ ...config, faq: newItems });
  };

  const updateFAQ = (index: number, field: 'pergunta' | 'resposta', value: string) => {
    const newItems = [...config.faq];
    newItems[index] = { ...newItems[index], [field]: value };
    setConfig({ ...config, faq: newItems });
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

          {/* 2. Base de Conhecimento Dinâmica */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
              <div className="flex items-center gap-2 text-white font-semibold text-lg">
                <Plus className="text-blue-400" size={20} />
                Base de Conhecimento
              </div>
              <button 
                onClick={addConhecimento}
                type="button"
                className="text-xs flex items-center gap-1 text-[var(--color-brand-400)] hover:text-[var(--color-brand-300)] transition-colors"
              >
                <Plus size={14} /> Adicionar Tópico
              </button>
            </div>

            <div className="space-y-4">
              {config.conhecimento.map((item, index) => (
                <div key={index} className="bg-white/5 rounded-xl p-4 border border-[var(--color-border)] relative group">
                  <button 
                    onClick={() => removeConhecimento(index)}
                    className="absolute -top-2 -right-2 bg-red-500/80 hover:bg-red-500 p-1.5 rounded-full text-white opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={12} />
                  </button>
                  <div className="space-y-3">
                    <input 
                      placeholder="Título do Tópico (ex: Preços, Diferenciais, Equipe)"
                      value={item.categoria}
                      onChange={e => updateConhecimento(index, 'categoria', e.target.value)}
                      className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white font-bold focus:outline-none focus:border-[var(--color-brand-500)]"
                    />
                    <textarea 
                      placeholder="Descreva aqui as informações que o robô deve saber sobre este tópico..."
                      value={item.conteudo}
                      onChange={e => updateConhecimento(index, 'conteudo', e.target.value)}
                      className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] h-24 resize-none"
                    />
                  </div>
                </div>
              ))}
              {config.conhecimento.length === 0 && (
                <p className="text-center text-sm text-[var(--color-foreground-muted)] py-4">Sua base de conhecimento está vazia. Adicione tópicos para o robô aprender!</p>
              )}
            </div>
          </section>

          {/* 3. Perguntas Frequentes (FAQ) */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
              <div className="flex items-center gap-2 text-white font-semibold text-lg">
                <Users className="text-purple-400" size={20} />
                Perguntas Frequentes (FAQ)
              </div>
              <button 
                onClick={addFAQ}
                type="button"
                className="text-xs flex items-center gap-1 text-[var(--color-brand-400)] hover:text-[var(--color-brand-300)] transition-colors"
              >
                <Plus size={14} /> Adicionar Pergunta
              </button>
            </div>

            <div className="space-y-4">
              {config.faq.map((item, index) => (
                <div key={index} className="bg-white/5 rounded-xl p-4 border border-[var(--color-border)] relative group">
                  <button 
                    onClick={() => removeFAQ(index)}
                    className="absolute -top-2 -right-2 bg-red-500/80 hover:bg-red-500 p-1.5 rounded-full text-white opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={12} />
                  </button>
                  <div className="space-y-2">
                    <input 
                      placeholder="Pergunta que o cliente costuma fazer"
                      value={item.pergunta}
                      onChange={e => updateFAQ(index, 'pergunta', e.target.value)}
                      className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                    />
                    <textarea 
                      placeholder="Resposta que o robô deve dar"
                      value={item.resposta}
                      onChange={e => updateFAQ(index, 'resposta', e.target.value)}
                      className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] h-16 resize-none"
                    />
                  </div>
                </div>
              ))}
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
                  onChange={e => setConfig({...config, planos: { basico: Number(e.target.value), vip: config.planos?.vip || 0 }})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)]">Plano VIP / Premium (R$)</label>
                <input 
                  type="number" 
                  value={config.planos?.vip || 0}
                  onChange={e => setConfig({...config, planos: { basico: config.planos?.basico || 0, vip: Number(e.target.value) }})}
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
                  onChange={e => setConfig({...config, horarios: { semana: e.target.value, sabado: config.horarios?.sabado || "" }})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                  placeholder="Ex: 08:00 as 18:00"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)]">Sábados / Feriados</label>
                <input 
                  type="text" 
                  value={config.horarios?.sabado || ""}
                  onChange={e => setConfig({...config, horarios: { semana: config.horarios?.semana || "", sabado: e.target.value }})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                  placeholder="Ex: 08:00 as 14:00"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--color-foreground-muted)] uppercase tracking-wider">Fuso Horário (Timezone)</label>
                <select 
                  value={config.timezone}
                  onChange={e => setConfig({...config, timezone: e.target.value})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                >
                  <option value="America/Sao_Paulo">Brasília (GMT-3)</option>
                  <option value="America/Manaus">Manaus (GMT-4)</option>
                  <option value="America/New_York">New York (GMT-5)</option>
                  <option value="Europe/London">London (GMT+0)</option>
                </select>
              </div>
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
