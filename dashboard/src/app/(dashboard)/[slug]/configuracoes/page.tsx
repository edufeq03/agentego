"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Save, CheckCircle2, Plus, Trash2, Users, CreditCard, MapPin, Sparkles, Clock, CalendarCheck, Tag, DollarSign, Calendar, Info, ShieldAlert, X } from "lucide-react";

interface Conhecimento {
  categoria: string;
  conteudo: string;
}

interface Professor {
  nome: string;
  especialidade: string;
  descricao: string;
}

interface Aula {
  nome: string;
  dias_horarios: string;
  professor: string;
  descricao: string;
}

interface ConfigData {
  nome_agente: string;
  nome_empresa: string;
  endereco: string;
  horarios: { semana: string; sabado: string; domingo?: string };
  faq: { pergunta: string; resposta: string }[];
  conhecimento: Conhecimento[];
  planos_detalhados: { nome: string; valor: number; periodicidade: string; descricao: string }[];
  regras_comportamento: string[];
  timezone: string;
  telefones_ignorados?: string[];
  professores?: Professor[];
  aulas?: Aula[];
  // Campos legados mantidos para compatibilidade
  planos?: { basico: number; vip: number };
  aviso_vencimento_1?: number;
  aviso_vencimento_2?: number;
  aviso_vencimento_3?: number;
}

export default function Configuracoes() {
  const [config, setConfig] = useState<ConfigData>({
    nome_agente: "",
    nome_empresa: "",
    endereco: "",
    horarios: { semana: "", sabado: "", domingo: "" },
    faq: [],
    conhecimento: [],
    planos_detalhados: [],
    regras_comportamento: [],
    timezone: "America/Sao_Paulo",
    telefones_ignorados: [],
    aviso_vencimento_1: 7,
    aviso_vencimento_2: 3,
    aviso_vencimento_3: 0,
    professores: [],
    aulas: []
  });
  
  const [newIgnoredPhone, setNewIgnoredPhone] = useState("");
  const [webhookToken, setWebhookToken] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [telefoneProprietario, setTelefoneProprietario] = useState("");
  const [nicho, setNicho] = useState("generico");
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
        setNicho(response.data.nicho || "generico");

        if (configData && Object.keys(configData).length > 0) {
          setConfig({
            ...configData,
            nome_agente: configData.nome_agente || "",
            nome_empresa: configData.nome_empresa || "",
            endereco: configData.endereco || "",
            horarios: {
              semana: configData.horarios?.semana || "",
              sabado: configData.horarios?.sabado || "",
              domingo: configData.horarios?.domingo || ""
            },
            faq: Array.isArray(configData.faq) ? configData.faq : [],
            conhecimento: Array.isArray(configData.conhecimento) ? configData.conhecimento : [],
            planos_detalhados: Array.isArray(configData.planos_detalhados) ? configData.planos_detalhados : [],
            regras_comportamento: Array.isArray(configData.regras_comportamento) ? configData.regras_comportamento : [],
            timezone: configData.timezone || "America/Sao_Paulo",
            telefones_ignorados: Array.isArray(configData.telefones_ignorados) ? configData.telefones_ignorados : [],
            aviso_vencimento_1: configData.aviso_vencimento_1 ?? 7,
            aviso_vencimento_2: configData.aviso_vencimento_2 ?? 3,
            aviso_vencimento_3: configData.aviso_vencimento_3 ?? 0,
            professores: Array.isArray(configData.professores) ? configData.professores : [],
            aulas: Array.isArray(configData.aulas) ? configData.aulas : []
          });
        }
        setWebhookToken(webhook_token || "");
        setBaseUrl(base_url || "");
        setTelefoneProprietario(response.data.telefone_proprietario || "");
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
      await api.put("dashboard/config", {
        config: config,
        telefone_proprietario: telefoneProprietario
      });
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

  const addProfessor = () => {
    setConfig({
      ...config,
      professores: [...(config.professores || []), { nome: "", especialidade: "", descricao: "" }]
    });
  };

  const removeProfessor = (index: number) => {
    const newItems = [...(config.professores || [])];
    newItems.splice(index, 1);
    setConfig({ ...config, professores: newItems });
  };

  const updateProfessor = (index: number, field: keyof Professor, value: string) => {
    const newItems = [...(config.professores || [])];
    newItems[index] = { ...newItems[index], [field]: value };
    setConfig({ ...config, professores: newItems });
  };

  const addAula = () => {
    setConfig({
      ...config,
      aulas: [...(config.aulas || []), { nome: "", dias_horarios: "", professor: "", descricao: "" }]
    });
  };

  const removeAula = (index: number) => {
    const newItems = [...(config.aulas || [])];
    newItems.splice(index, 1);
    setConfig({ ...config, aulas: newItems });
  };

  const updateAula = (index: number, field: keyof Aula, value: string) => {
    const newItems = [...(config.aulas || [])];
    newItems[index] = { ...newItems[index], [field]: value };
    setConfig({ ...config, aulas: newItems });
  };

  const addPlano = () => {
    setConfig({
      ...config,
      planos_detalhados: [...(config.planos_detalhados || []), { nome: "", valor: 0, periodicidade: "mensal", descricao: "" }]
    });
  };

  const removePlano = (index: number) => {
    const newItems = [...config.planos_detalhados];
    newItems.splice(index, 1);
    setConfig({ ...config, planos_detalhados: newItems });
  };

  const updatePlano = (index: number, field: string, value: any) => {
    const newItems = [...config.planos_detalhados];
    newItems[index] = { ...newItems[index], [field]: value };
    setConfig({ ...config, planos_detalhados: newItems });
  };

  const parseTime = (val: string) => {
    if (!val || !val.includes(' as ')) return { start: "", end: "" };
    const [start, end] = val.split(' as ');
    return { start, end };
  };

  const updateTime = (day: 'semana' | 'sabado' | 'domingo', type: 'start' | 'end', val: string) => {
    const current = parseTime(config.horarios[day] || "");
    const updated = { ...current, [type]: val };
    const newStr = updated.start && updated.end ? `${updated.start} as ${updated.end}` : "";
    setConfig(prev => ({ ...prev, horarios: { ...prev.horarios, [day]: newStr } }));
  };

  const addIgnoredPhone = () => {
    if (!newIgnoredPhone.trim()) return;
    const phone = newIgnoredPhone.trim().replace(/\D/g, ""); // Apenas números
    if (!phone) return;
    const current = config.telefones_ignorados || [];
    if (!current.includes(phone)) {
      setConfig({ ...config, telefones_ignorados: [...current, phone] });
    }
    setNewIgnoredPhone("");
  };

  const removeIgnoredPhone = (phone: string) => {
    const current = config.telefones_ignorados || [];
    setConfig({ ...config, telefones_ignorados: current.filter(p => p !== phone) });
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
                <label className="text-xs font-medium text-[var(--color-foreground-muted)] uppercase tracking-wider">Nome da Empresa</label>
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
              {Array.isArray(config.conhecimento) && config.conhecimento.map((item, index) => (
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

          {/* Seção Condicional para Nicho Academia: Professores e Grade de Aulas */}
          {nicho === "academia" && (
            <>
              {/* Gestão de Professores e Equipe */}
              <section className="glass-panel p-6 space-y-6">
                <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
                  <div className="flex items-center gap-2 text-white font-semibold text-lg">
                    <Users className="text-emerald-400" size={20} />
                    Gestão de Professores e Equipe
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
                  {(config.professores || []).map((prof, index) => (
                    <div key={index} className="bg-white/5 rounded-xl p-4 border border-[var(--color-border)] relative group">
                      <button 
                        onClick={() => removeProfessor(index)}
                        className="absolute -top-2 -right-2 bg-red-500/80 hover:bg-red-500 p-1.5 rounded-full text-white opacity-0 group-hover:opacity-100 transition-all z-10 animate-in fade-in"
                      >
                        <Trash2 size={12} />
                      </button>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Nome Completo</label>
                          <input 
                            placeholder="Ex: Ricardo Silva"
                            value={prof.nome}
                            onChange={e => updateProfessor(index, 'nome', e.target.value)}
                            className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white font-semibold focus:outline-none focus:border-[var(--color-brand-500)]"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Especialidade / Foco</label>
                          <input 
                            placeholder="Ex: Musculação e Hipertrofia"
                            value={prof.especialidade}
                            onChange={e => updateProfessor(index, 'especialidade', e.target.value)}
                            className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                          />
                        </div>
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Breve Descrição / Bio</label>
                        <textarea 
                          placeholder="Ex: Formado em Ed. Física pela UNICAMP, especialista em reabilitação."
                          value={prof.descricao}
                          onChange={e => updateProfessor(index, 'descricao', e.target.value)}
                          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] h-16 resize-none"
                        />
                      </div>
                    </div>
                  ))}
                  {(config.professores || []).length === 0 && (
                    <p className="text-center text-sm text-[var(--color-foreground-muted)] py-4">Nenhum professor cadastrado. Adicione professores para o agente saber quem são!</p>
                  )}
                </div>
              </section>

              {/* Grade de Aulas e Modalidades */}
              <section className="glass-panel p-6 space-y-6">
                <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
                  <div className="flex items-center gap-2 text-white font-semibold text-lg">
                    <CalendarCheck className="text-cyan-400" size={20} />
                    Grade de Aulas e Modalidades
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
                  {(config.aulas || []).map((aula, index) => (
                    <div key={index} className="bg-white/5 rounded-xl p-4 border border-[var(--color-border)] relative group">
                      <button 
                        onClick={() => removeAula(index)}
                        className="absolute -top-2 -right-2 bg-red-500/80 hover:bg-red-500 p-1.5 rounded-full text-white opacity-0 group-hover:opacity-100 transition-all z-10 animate-in fade-in"
                      >
                        <Trash2 size={12} />
                      </button>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Nome da Aula / Modalidade</label>
                          <input 
                            placeholder="Ex: Crossfit, Zumba, Pilates"
                            value={aula.nome}
                            onChange={e => updateAula(index, 'nome', e.target.value)}
                            className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white font-semibold focus:outline-none focus:border-[var(--color-brand-500)]"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Dias e Horários</label>
                          <input 
                            placeholder="Ex: Ter e Qui às 19h, Sáb às 10h"
                            value={aula.dias_horarios}
                            onChange={e => updateAula(index, 'dias_horarios', e.target.value)}
                            className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Professor / Instrutor</label>
                          <select 
                            value={aula.professor}
                            onChange={e => updateAula(index, 'professor', e.target.value)}
                            className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] appearance-none cursor-pointer"
                          >
                            <option value="">Selecione um professor...</option>
                            {(config.professores || []).filter(p => p.nome).map((p, i) => (
                              <option key={i} value={p.nome}>{p.nome}</option>
                            ))}
                            {/* Fallback caso digite um nome livre */}
                            {aula.professor && !(config.professores || []).some(p => p.nome === aula.professor) && (
                              <option value={aula.professor}>{aula.professor}</option>
                            )}
                          </select>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Detalhes Adicionais (Requisitos, vagas, etc.)</label>
                        <textarea 
                          placeholder="Ex: Necessário agendamento prévio. Capacidade máxima: 15 alunos."
                          value={aula.descricao}
                          onChange={e => updateAula(index, 'descricao', e.target.value)}
                          className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] h-16 resize-none"
                        />
                      </div>
                    </div>
                  ))}
                  {(config.aulas || []).length === 0 && (
                    <p className="text-center text-sm text-[var(--color-foreground-muted)] py-4">Nenhuma aula cadastrada. Adicione modalidades para o robô poder apresentá-las!</p>
                  )}
                </div>
              </section>
            </>
          )}
        </div>

        {/* Sidebar: Configurações Rápidas */}
        <div className="space-y-8">
          {/* 4. Planos e Mensalidades (Dinamizado) */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
              <div className="flex items-center gap-2 text-white font-semibold text-lg">
                <CreditCard className="text-orange-400" size={20} />
                Planos e Mensalidades
              </div>
              <button 
                onClick={addPlano}
                type="button"
                className="text-xs flex items-center gap-1 text-[var(--color-brand-400)] hover:text-[var(--color-brand-300)] transition-colors bg-white/5 px-2 py-1 rounded-lg border border-white/10"
              >
                <Plus size={14} /> Adicionar Plano
              </button>
            </div>
            
            <div className="space-y-4">
              {config.planos_detalhados?.map((plano, index) => (
                <div key={index} className="bg-white/5 rounded-2xl p-5 border border-white/10 relative group hover:bg-white/10 transition-all">
                  <button 
                    onClick={() => removePlano(index)}
                    className="absolute top-4 right-4 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white p-2 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={16} />
                  </button>
                  
                  <div className="space-y-4">
                    {/* Nome do Plano */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wider">
                        <Tag size={12} className="text-orange-400" />
                        Nome do Plano
                      </div>
                      <input 
                        placeholder="Ex: Plano Semestral VIP"
                        value={plano.nome}
                        onChange={e => updatePlano(index, 'nome', e.target.value)}
                        className="w-full bg-slate-900/50 border border-white/5 rounded-xl py-2.5 px-4 text-white font-semibold focus:outline-none focus:border-orange-500/50 transition-colors"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      {/* Valor */}
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wider">
                          <DollarSign size={12} className="text-green-400" />
                          Valor
                        </div>
                        <div className="relative">
                          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm font-bold">R$</span>
                          <input 
                            type="number"
                            value={plano.valor}
                            onChange={e => updatePlano(index, 'valor', Number(e.target.value))}
                            className="w-full bg-slate-900/50 border border-white/5 rounded-xl py-2.5 pl-10 pr-4 text-white font-bold focus:outline-none focus:border-green-500/50 transition-colors"
                          />
                        </div>
                      </div>

                      {/* Ciclo */}
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wider">
                          <Calendar size={12} className="text-blue-400" />
                          Ciclo
                        </div>
                        <select 
                          value={plano.periodicidade}
                          onChange={e => updatePlano(index, 'periodicidade', e.target.value)}
                          className="w-full bg-slate-900/50 border border-white/5 rounded-xl py-2.5 px-4 text-white focus:outline-none focus:border-blue-500/50 transition-colors appearance-none cursor-pointer"
                        >
                          <option value="mensal">Mensal</option>
                          <option value="trimestral">Trimestral</option>
                          <option value="semestral">Semestral</option>
                          <option value="anual">Anual</option>
                        </select>
                      </div>
                    </div>

                    {/* Observação */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wider">
                        <Info size={12} className="text-purple-400" />
                        Destaque / Observação
                      </div>
                      <input 
                        placeholder="Ex: Recorrência no cartão (Sem ocupar limite)"
                        value={plano.descricao}
                        onChange={e => updatePlano(index, 'descricao', e.target.value)}
                        className="w-full bg-slate-900/50 border border-white/5 rounded-xl py-2.5 px-4 text-sm text-slate-300 focus:outline-none focus:border-purple-500/50 transition-colors"
                      />
                    </div>
                  </div>
                </div>
              ))}
              
              {(!config.planos_detalhados || config.planos_detalhados.length === 0) && (
                <div className="flex flex-col items-center justify-center py-12 px-4 rounded-2xl border-2 border-dashed border-white/5 bg-white/[0.02]">
                  <CreditCard className="text-slate-700 mb-3" size={40} />
                  <p className="text-slate-500 text-sm font-medium">Nenhum plano cadastrado</p>
                  <p className="text-slate-600 text-[10px] uppercase tracking-widest mt-1">Adicione planos para seu agente oferecer</p>
                </div>
              )}
            </div>
          </section>

          {/* Horários */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex items-center gap-2 text-white font-semibold text-lg border-b border-[var(--color-border)] pb-3">
              <Clock className="text-green-400" size={20} />
              Horário de Funcionamento
            </div>
            <div className="space-y-2">
              {/* Segunda a Sexta */}
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 group hover:bg-white/10 transition-all">
                <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                  <Clock size={12} className="text-green-400" />
                  Segunda a Sexta
                </div>
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
                  <input 
                    type="time" 
                    value={parseTime(config.horarios?.semana || "").start}
                    onChange={e => updateTime('semana', 'start', e.target.value)}
                    className="w-full bg-slate-900/50 border border-white/5 rounded-lg py-2 px-2 text-white text-xs focus:outline-none focus:border-green-500/50 transition-colors"
                  />
                  <span className="text-[10px] text-slate-600 font-bold uppercase">as</span>
                  <input 
                    type="time" 
                    value={parseTime(config.horarios?.semana || "").end}
                    onChange={e => updateTime('semana', 'end', e.target.value)}
                    className="w-full bg-slate-900/50 border border-white/5 rounded-lg py-2 px-2 text-white text-xs focus:outline-none focus:border-green-500/50 transition-colors"
                  />
                </div>
              </div>

              {/* Sábados */}
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 group hover:bg-white/10 transition-all">
                <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                  <Clock size={12} className="text-blue-400" />
                  Sábados
                </div>
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
                  <input 
                    type="time" 
                    value={parseTime(config.horarios?.sabado || "").start}
                    onChange={e => updateTime('sabado', 'start', e.target.value)}
                    className="w-full bg-slate-900/50 border border-white/5 rounded-lg py-2 px-2 text-white text-xs focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                  <span className="text-[10px] text-slate-600 font-bold uppercase">as</span>
                  <input 
                    type="time" 
                    value={parseTime(config.horarios?.sabado || "").end}
                    onChange={e => updateTime('sabado', 'end', e.target.value)}
                    className="w-full bg-slate-900/50 border border-white/5 rounded-lg py-2 px-2 text-white text-xs focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>
              </div>

              {/* Domingos / Feriados */}
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 group hover:bg-white/10 transition-all">
                <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                  <Clock size={12} className="text-purple-400" />
                  Domingos / Feriados
                </div>
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
                  <input 
                    type="time" 
                    value={parseTime(config.horarios?.domingo || "").start}
                    onChange={e => updateTime('domingo', 'start', e.target.value)}
                    className="w-full bg-slate-900/50 border border-white/5 rounded-lg py-2 px-2 text-white text-xs focus:outline-none focus:border-purple-500/50 transition-colors"
                  />
                  <span className="text-[10px] text-slate-600 font-bold uppercase">as</span>
                  <input 
                    type="time" 
                    value={parseTime(config.horarios?.domingo || "").end}
                    onChange={e => updateTime('domingo', 'end', e.target.value)}
                    className="w-full bg-slate-900/50 border border-white/5 rounded-lg py-2 px-2 text-white text-xs focus:outline-none focus:border-purple-500/50 transition-colors"
                  />
                </div>
                <p className="text-[9px] text-slate-600 italic mt-2">Deixe em branco se estiver fechado.</p>
              </div>

              <div className="space-y-1 pt-4">
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
          </section>          {/* Telefones Ignorados (Blacklist) */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex items-center gap-2 text-white font-semibold text-lg border-b border-[var(--color-border)] pb-3">
              <ShieldAlert className="text-red-400" size={20} />
              Telefones Ignorados (Blacklist)
            </div>
            <div className="space-y-4">
              <p className="text-xs text-slate-500 italic">
                O robô ignorará qualquer mensagem vinda destes números. Útil para spam, testes ou números internos.
              </p>
              <div className="space-y-2">
                <input 
                  type="text" 
                  placeholder="Ex: 5511999999999"
                  value={newIgnoredPhone}
                  onChange={e => setNewIgnoredPhone(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && addIgnoredPhone()}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-red-500/50"
                />
                <div className="flex justify-end">
                  <button 
                    onClick={addIgnoredPhone}
                    className="bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 px-6 py-2 rounded-lg text-sm font-medium transition-all"
                  >
                    Adicionar Número
                  </button>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {(config.telefones_ignorados || []).map(phone => (
                  <div key={phone} className="flex items-center gap-2 bg-slate-900 border border-white/5 rounded-full px-3 py-1 text-xs text-slate-300">
                    <span>{phone}</span>
                    <button 
                      onClick={() => removeIgnoredPhone(phone)}
                      className="text-slate-500 hover:text-red-400 transition-colors"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
                {(config.telefones_ignorados || []).length === 0 && (
                  <span className="text-[10px] text-slate-600">Nenhum número na lista negra.</span>
                )}
              </div>
            </div>
          </section>

          {/* Avisos de Vencimento */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex items-center gap-2 text-white font-semibold text-lg border-b border-[var(--color-border)] pb-3">
              <CalendarCheck className="text-blue-400" size={20} />
              Avisos de Vencimento
            </div>
            <p className="text-xs text-[var(--color-foreground-muted)]">
              Configure com quantos dias de antecedência o sistema deve avisar o aluno sobre o vencimento.
            </p>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="text-[10px] font-medium text-[var(--color-foreground-muted)] uppercase">Aviso 1</label>
                <div className="relative">
                  <input 
                    type="number" 
                    value={config.aviso_vencimento_1}
                    onChange={e => setConfig({...config, aviso_vencimento_1: Number(e.target.value)})}
                    className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-3 text-white text-center focus:outline-none focus:border-[var(--color-brand-500)]"
                  />
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[8px] text-[var(--color-foreground-muted)]">dias</span>
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-medium text-[var(--color-foreground-muted)] uppercase">Aviso 2</label>
                <div className="relative">
                  <input 
                    type="number" 
                    value={config.aviso_vencimento_2}
                    onChange={e => setConfig({...config, aviso_vencimento_2: Number(e.target.value)})}
                    className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-3 text-white text-center focus:outline-none focus:border-[var(--color-brand-500)]"
                  />
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[8px] text-[var(--color-foreground-muted)]">dias</span>
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-medium text-[var(--color-foreground-muted)] uppercase">Aviso 3</label>
                <div className="relative">
                  <input 
                    type="number" 
                    value={config.aviso_vencimento_3}
                    onChange={e => setConfig({...config, aviso_vencimento_3: Number(e.target.value)})}
                    className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-3 text-white text-center focus:outline-none focus:border-[var(--color-brand-500)]"
                  />
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[8px] text-[var(--color-foreground-muted)]">dias</span>
                </div>
              </div>
            </div>
            <p className="text-[10px] italic text-[var(--color-foreground-muted)]">
              Dica: Use 0 para avisar no dia exato do vencimento.
            </p>
          </section>
          {/* Relatório de Performance */}
          <section className="glass-panel p-6 space-y-6">
            <div className="flex items-center gap-2 text-white font-semibold text-lg border-b border-[var(--color-border)] pb-3">
              <Users className="text-green-400" size={20} />
              Relatório de Performance
            </div>
            <p className="text-xs text-[var(--color-foreground-muted)]">
              O relatório semanal é enviado automaticamente toda segunda-feira às 09:00 para o telefone do proprietário.
            </p>

            <div className="space-y-1 pb-4">
              <label className="text-[10px] font-medium text-[var(--color-foreground-muted)] uppercase tracking-wider">Seu Telefone (WhatsApp)</label>
              <div className="relative">
                <Users className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" size={16} />
                <input 
                  type="text" 
                  value={telefoneProprietario}
                  onChange={e => setTelefoneProprietario(e.target.value)}
                  placeholder="Ex: 5511999999999"
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 pl-10 pr-4 text-white text-sm focus:outline-none focus:border-[var(--color-brand-500)]"
                />
              </div>
            </div>

            <button 
              onClick={async () => {
                if (!telefoneProprietario) {
                  alert("Por favor, preencha o seu telefone de WhatsApp primeiro.");
                  return;
                }
                try {
                  // Salva automaticamente antes de disparar, para garantir que o número atualizado seja usado
                  await api.put("dashboard/config", {
                    config: config,
                    telefone_proprietario: telefoneProprietario
                  });
                  
                  const res = await api.post("dashboard/relatorio-semanal/enviar-agora");
                  alert("Relatório enviado com sucesso para o seu WhatsApp!");
                } catch (e) {
                  alert("Erro ao enviar relatório. Verifique se o seu telefone de proprietário está configurado corretamente.");
                }
              }}
              className="w-full flex items-center justify-center gap-2 bg-[var(--color-surface-hover)] hover:bg-[var(--color-surface-active)] border border-[var(--color-border)] text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all"
            >
              <Users size={16} /> Enviar Relatório Agora (Teste)
            </button>
          </section>

          {/* Save Mobile */}
          <button 
            onClick={handleSave}
            disabled={saving}
            className="w-full md:hidden flex items-center justify-center gap-2 bg-gradient-to-r from-[var(--color-brand-600)] to-[var(--color-brand-400)] text-white px-8 py-4 rounded-xl font-medium transition-all shadow-lg"
          >
            {saving ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" /> : <Save size={20} />}
            {saving ? "Salvando..." : "Salvar Tudo"}
          </button>
        </div>
      </div>
    </div>
  );
}
