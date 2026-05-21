"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Share2, Plus, Trash2, Copy, Check, Megaphone, Target, Percent, Sparkles, AlertCircle } from "lucide-react";

interface Campanha {
  id: string;
  codigo_ref: string;
  nome: string;
  origem: string;
  descricao?: string;
  criado_em: string;
  leads_gerados: number;
  leads_convertidos: number;
  taxa_conversao: number;
}

export default function MarketingPage() {
  const [campanhas, setCampanhas] = useState<Campanha[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Form Fields
  const [nome, setNome] = useState("");
  const [codigoRef, setCodigoRef] = useState("");
  const [origem, setOrigem] = useState("facebook");
  const [descricao, setDescricao] = useState("");

  // Link Generator State
  const [selectedCampaignCode, setSelectedCampaignCode] = useState("");
  const [customText, setCustomText] = useState("Olá! Tenho interesse em fazer uma cotação.");
  const [generatedLink, setGeneratedLink] = useState("");
  const [copiedLink, setCopiedLink] = useState(false);
  const [whatsappNumber, setWhatsappNumber] = useState("");

  useEffect(() => {
    fetchCampanhas();
    fetchCompanyWhatsapp();
  }, []);

  useEffect(() => {
    if (selectedCampaignCode && whatsappNumber) {
      const cleanNum = whatsappNumber.replace(/\D/g, "");
      const fullText = `${customText} [REF: ${selectedCampaignCode}]`;
      const encodedText = encodeURIComponent(fullText);
      setGeneratedLink(`https://wa.me/${cleanNum}?text=${encodedText}`);
    } else {
      setGeneratedLink("");
    }
  }, [selectedCampaignCode, customText, whatsappNumber]);

  async function fetchCampanhas() {
    try {
      setLoading(true);
      const response = await api.get("dashboard/marketing/campanhas");
      setCampanhas(response.data);
      if (response.data.length > 0 && !selectedCampaignCode) {
        setSelectedCampaignCode(response.data[0].codigo_ref);
      }
    } catch (err: any) {
      console.error("Erro ao buscar campanhas:", err);
    } finally {
      setLoading(false);
    }
  }

  async function fetchCompanyWhatsapp() {
    try {
      const response = await api.get("whatsapp/status");
      if (response.data && response.data.number) {
        setWhatsappNumber(response.data.number);
      } else {
        // Fallback para buscar dados da empresa caso o whatsapp não esteja conectado
        const profile = await api.get("auth/me");
        if (profile.data && profile.data.empresa) {
          setWhatsappNumber(profile.data.empresa.telefone_whatsapp || "");
        }
      }
    } catch (err) {
      console.error("Erro ao buscar telefone:", err);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!nome.trim() || !codigoRef.trim()) {
      setErrorMsg("Por favor, preencha todos os campos obrigatórios.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg("");
      setSuccessMsg("");

      const response = await api.post("dashboard/marketing/campanhas", {
        nome: nome.trim(),
        codigo_ref: codigoRef.trim().toUpperCase(),
        origem: origem.trim(),
        descricao: descricao.trim() || undefined,
      });

      if (response.data.status === "ok") {
        setSuccessMsg("Campanha criada com sucesso!");
        setNome("");
        setCodigoRef("");
        setDescricao("");
        setOrigem("facebook");
        fetchCampanhas();
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Erro ao criar campanha. Verifique o código de referência.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Deseja realmente excluir esta campanha? Leads com essa tag continuarão com o histórico, mas a métrica deixará de ser consolidada.")) {
      return;
    }

    try {
      await api.delete(`dashboard/marketing/campanhas/${id}`);
      fetchCampanhas();
    } catch (err) {
      console.error("Erro ao excluir campanha:", err);
    }
  }

  function handleCopy() {
    if (!generatedLink) return;
    navigator.clipboard.writeText(generatedLink);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  }

  // Calculate Metrics
  const totalLeadsGerados = campanhas.reduce((acc, c) => acc + c.leads_gerados, 0);
  const totalLeadsConvertidos = campanhas.reduce((acc, c) => acc + c.leads_convertidos, 0);
  const taxaConversaoMedia = totalLeadsGerados > 0 
    ? Math.round((totalLeadsConvertidos / totalLeadsGerados) * 100) 
    : 0;

  const melhorCampanha = [...campanhas]
    .filter(c => c.leads_gerados > 0)
    .sort((a, b) => b.taxa_conversao - a.taxa_conversao)[0];

  if (loading && campanhas.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--color-brand-500)]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Share2 className="text-[var(--color-brand-500)] h-7 w-7" /> Gestão de Marketing & ROI
        </h2>
        <p className="text-[var(--color-foreground-muted)] mt-1">
          Cadastre campanhas de anúncios do Facebook, Instagram, Google ou Parceiros e acompanhe em tempo real a taxa de conversão das vendas.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-6 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-[var(--color-foreground-muted)]">Leads de Anúncios</p>
            <p className="text-3xl font-extrabold text-white">{totalLeadsGerados}</p>
            <p className="text-xs text-[var(--color-foreground-muted)]">Total capturado via tags</p>
          </div>
          <div className="bg-[rgba(59,130,246,0.1)] p-3 rounded-xl">
            <Target className="h-6 w-6 text-blue-400" />
          </div>
        </div>

        <div className="glass-panel p-6 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-[var(--color-foreground-muted)]">Conversão Geral</p>
            <p className="text-3xl font-extrabold text-white">{taxaConversaoMedia}%</p>
            <p className="text-xs text-[var(--color-foreground-muted)]">Leads convertidos no funil</p>
          </div>
          <div className="bg-[rgba(16,185,129,0.1)] p-3 rounded-xl">
            <Percent className="h-6 w-6 text-emerald-400" />
          </div>
        </div>

        <div className="glass-panel p-6 flex items-center justify-between">
          <div className="space-y-1 w-[70%]">
            <p className="text-sm font-medium text-[var(--color-foreground-muted)]">Melhor Campanha</p>
            <p className="text-xl font-bold text-white truncate">
              {melhorCampanha ? melhorCampanha.nome : "Nenhuma ativa"}
            </p>
            <p className="text-xs text-[var(--color-foreground-muted)]">
              {melhorCampanha ? `${melhorCampanha.taxa_conversao}% de conversão` : "Aguardando dados"}
            </p>
          </div>
          <div className="bg-[rgba(245,158,11,0.1)] p-3 rounded-xl">
            <Sparkles className="h-6 w-6 text-amber-400" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Creator Form */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Plus className="text-[var(--color-brand-500)] h-5 w-5" /> Nova Campanha de Anúncios
          </h3>
          
          <form onSubmit={handleCreate} className="space-y-4">
            {errorMsg && (
              <div className="bg-red-950/40 border border-red-500/30 text-red-300 p-3 rounded-lg flex items-center gap-2 text-sm">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}
            
            {successMsg && (
              <div className="bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 p-3 rounded-lg flex items-center gap-2 text-sm">
                <Check className="h-4 w-4 shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Código de Referência</label>
                <input
                  type="text"
                  placeholder="Ex: FB-MOTO-01"
                  value={codigoRef}
                  onChange={(e) => setCodigoRef(e.target.value.replace(/[^a-zA-Z0-9_-]/g, ""))}
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] uppercase"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Origem / Canal</label>
                <select
                  value={origem}
                  onChange={(e) => setOrigem(e.target.value)}
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                >
                  <option value="facebook">Facebook Ads</option>
                  <option value="instagram">Instagram Ads</option>
                  <option value="google">Google Ads</option>
                  <option value="parceiro">Link de Parceiro</option>
                  <option value="site">Site / Blog</option>
                  <option value="outro">Outro / Geral</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Nome da Campanha</label>
              <input
                type="text"
                placeholder="Ex: Campanha Facebook Fazer 250 - Maio"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Foco / Instruções para o Robô (Opcional)</label>
              <textarea
                rows={2}
                placeholder="Ex: Anúncio focado em seguro de moto Yamaha Fazer 250. Comece perguntando sobre a moto."
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white text-sm font-semibold py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 transition duration-200 disabled:opacity-50"
            >
              <Plus className="h-4 w-4" /> {submitting ? "Criando..." : "Criar Campanha"}
            </button>
          </form>
        </div>

        {/* Dynamic WhatsApp Link Generator */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Megaphone className="text-[var(--color-brand-500)] h-5 w-5" /> Gerador de Links WhatsApp Ads
          </h3>

          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Selecione a Campanha</label>
                <select
                  value={selectedCampaignCode}
                  onChange={(e) => setSelectedCampaignCode(e.target.value)}
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                >
                  {campanhas.map((c) => (
                    <option key={c.id} value={c.codigo_ref}>
                      {c.codigo_ref} - {c.nome}
                    </option>
                  ))}
                  {campanhas.length === 0 && (
                    <option value="">Nenhuma campanha cadastrada</option>
                  )}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Telefone de Atendimento</label>
                <input
                  type="text"
                  placeholder="Ex: 5519996737713"
                  value={whatsappNumber}
                  onChange={(e) => setWhatsappNumber(e.target.value.replace(/\D/g, ""))}
                  className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Mensagem Inicial do Cliente</label>
              <textarea
                rows={2}
                placeholder="Mensagem padrão que o cliente enviará ao clicar..."
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] resize-none"
              />
            </div>

            {generatedLink ? (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Link Pronto (Anúncios/Links)</label>
                <div className="flex items-center gap-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-2 overflow-hidden">
                  <span className="text-xs text-slate-300 select-all truncate grow font-mono px-2">
                    {generatedLink}
                  </span>
                  <button
                    onClick={handleCopy}
                    className="bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white p-2 rounded-lg transition duration-200"
                    title="Copiar Link"
                  >
                    {copiedLink ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </button>
                </div>
                <p className="text-[10px] text-[var(--color-foreground-muted)] italic">
                  * A tag <span className="font-mono text-slate-300 font-bold">[REF: {selectedCampaignCode}]</span> foi acoplada ao final do texto para que nosso sistema identifique o lead imediatamente!
                </p>
              </div>
            ) : (
              <div className="text-xs text-amber-300 bg-amber-950/20 border border-amber-500/20 p-3 rounded-lg flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>
                  {!selectedCampaignCode 
                    ? "Cadastre pelo menos uma campanha para poder gerar links de anúncios."
                    : "Por favor, digite o telefone de atendimento (DDI + DDD + Número) no campo acima para gerar o link."}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Campaigns list Table */}
      <div className="glass-panel p-0 overflow-hidden">
        <div className="p-4 border-b border-[var(--color-border)] flex justify-between items-center bg-[var(--color-surface)]">
          <div>
            <h3 className="text-lg font-semibold text-white">Resultados das Campanhas (ROI)</h3>
            <p className="text-xs text-[var(--color-foreground-muted)]">Lista de campanhas cadastradas e seus respectivos rendimentos.</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-[var(--color-surface-hover)] border-b border-[var(--color-border)]">
                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Campanha</th>
                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Foco / Diretrizes</th>
                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Código REF</th>
                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Origem</th>
                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-center">Leads Gerados</th>
                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-center">Leads Convertidos</th>
                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-center">Taxa Conversão</th>
                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {campanhas.map((c) => (
                <tr key={c.id} className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface)] transition duration-150">
                  <td className="p-4 font-semibold text-white">{c.nome}</td>
                  <td className="p-4 text-slate-300 max-w-[220px] truncate" title={c.descricao || "Nenhum"}>
                    {c.descricao || <span className="text-slate-500 italic">Padrão</span>}
                  </td>
                  <td className="p-4 font-mono text-xs"><span className="bg-slate-800 text-slate-300 py-1 px-2.5 rounded-md font-bold uppercase">{c.codigo_ref}</span></td>
                  <td className="p-4 capitalize">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      c.origem === 'facebook' ? 'bg-blue-900/50 text-blue-300' :
                      c.origem === 'instagram' ? 'bg-pink-900/50 text-pink-300' :
                      c.origem === 'google' ? 'bg-amber-900/50 text-amber-300' : 'bg-slate-800 text-slate-300'
                    }`}>
                      {c.origem}
                    </span>
                  </td>
                  <td className="p-4 text-center font-bold text-slate-200">{c.leads_gerados}</td>
                  <td className="p-4 text-center font-bold text-slate-200">{c.leads_convertidos}</td>
                  <td className="p-4 text-center font-extrabold text-[var(--color-brand-400)]">{c.taxa_conversao}%</td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => handleDelete(c.id)}
                      className="text-red-400 hover:text-red-300 p-1 bg-red-950/20 hover:bg-red-950/60 rounded-lg transition duration-200"
                      title="Excluir Campanha"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {campanhas.length === 0 && (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-[var(--color-foreground-muted)]">
                    Nenhuma campanha cadastrada ainda. Utilize o formulário acima para criar sua primeira campanha!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
