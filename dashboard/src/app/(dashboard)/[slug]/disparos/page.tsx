"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Zap, Check, AlertCircle, Save, Info, HelpCircle, ToggleLeft, ToggleRight, Hourglass, Sparkles, Loader2 } from "lucide-react";

export default function ReengagementConfigPage() {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Inactivity Trigger States
  const [inactEnabled, setInactEnabled] = useState(false);
  const [inactDelay, setInactDelay] = useState(2);
  const [inactPrompt, setInactPrompt] = useState("");

  // Pending Fields Trigger States
  const [pendEnabled, setPendEnabled] = useState(false);
  const [pendDelay, setPendDelay] = useState(1);
  const [pendPrompt, setPendPrompt] = useState("");

  useEffect(() => {
    fetchConfig();
  }, []);

  async function fetchConfig() {
    try {
      setLoading(true);
      const response = await api.get("dashboard/marketing/reengagement");
      const data = response.data;
      
      setInactEnabled(data.reengagement_inactivity_enabled);
      setInactDelay(data.reengagement_inactivity_delay_hours);
      setInactPrompt(data.reengagement_inactivity_prompt);
      
      setPendEnabled(data.reengagement_pending_enabled);
      setPendDelay(data.reengagement_pending_delay_hours);
      setPendPrompt(data.reengagement_pending_prompt);
    } catch (error: any) {
      console.error("Erro ao carregar configurações de reengajamento:", error);
      setErrorMsg("Não foi possível carregar as configurações de disparo automático.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      setSubmitting(true);
      setErrorMsg("");
      setSuccessMsg("");

      const payload = {
        reengagement_inactivity_enabled: inactEnabled,
        reengagement_inactivity_delay_hours: Number(inactDelay),
        reengagement_inactivity_prompt: inactPrompt.trim(),
        
        reengagement_pending_enabled: pendEnabled,
        reengagement_pending_delay_hours: Number(pendDelay),
        reengagement_pending_prompt: pendPrompt.trim(),
      };

      await api.post("dashboard/marketing/reengagement", payload);
      showToast("Configurações de reengajamento salvas com sucesso!");
    } catch (error: any) {
      console.error("Erro ao salvar configurações:", error);
      setErrorMsg("Ocorreu um erro ao salvar as configurações no servidor.");
    } finally {
      setSubmitting(false);
    }
  }

  function showToast(msg: string) {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 4000);
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[300px] gap-3">
        <Loader2 className="animate-spin h-10 w-10 text-[var(--color-brand-500)]" />
        <span className="text-sm font-medium text-[var(--color-foreground-muted)]">Carregando painel de inteligência...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Zap className="text-[var(--color-brand-500)] fill-[var(--color-brand-500)]/15 h-7 w-7" /> Disparos da IA (Reengajamento Automatizado)
          </h2>
          <p className="text-[var(--color-foreground-muted)] mt-1 max-w-3xl">
            Aumente suas conversões recuperando leads frios no WhatsApp. Nossa IA acompanha o histórico e envia mensagens personalizadas e humanizadas de acompanhamento no tempo ideal.
          </p>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="flex items-center gap-3 p-4 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-emerald-400 animate-fadeIn">
          <Check className="h-5 w-5 shrink-0" />
          <span className="text-sm font-medium">{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center gap-3 p-4 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400 animate-fadeIn">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span className="text-sm font-medium">{errorMsg}</span>
        </div>
      )}

      {/* Configuration Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Card A: Inactivity */}
          <div className="glass-panel p-6 flex flex-col justify-between border border-white/5 hover:border-white/10 transition-all duration-300">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-orange-950/40 border border-orange-500/25 text-orange-400">
                    <Hourglass className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">Reengajamento por Inatividade</h3>
                    <p className="text-[10px] text-[var(--color-foreground-muted)]">Ativado após período de silêncio do lead</p>
                  </div>
                </div>
                
                <button
                  type="button"
                  onClick={() => setInactEnabled(!inactEnabled)}
                  className="focus:outline-none transition-transform active:scale-95"
                >
                  {inactEnabled ? (
                    <ToggleRight className="h-9 w-9 text-[var(--color-brand-500)]" />
                  ) : (
                    <ToggleLeft className="h-9 w-9 text-[var(--color-foreground-muted)]" />
                  )}
                </button>
              </div>

              <div className={`space-y-4 transition-all duration-300 ${inactEnabled ? "opacity-100" : "opacity-45 pointer-events-none select-none"}`}>
                
                {/* Delay hours */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-white/90 flex items-center gap-1">
                    Tempo de Espera para Disparo
                  </label>
                  <select
                    value={inactDelay}
                    onChange={(e) => setInactDelay(Number(e.target.value))}
                    className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] transition-all [&>option]:bg-zinc-950"
                  >
                    <option value="1">1 hora sem resposta</option>
                    <option value="2">2 horas sem resposta</option>
                    <option value="4">4 horas sem resposta</option>
                    <option value="8">8 horas sem resposta</option>
                    <option value="24">24 horas sem resposta</option>
                    <option value="48">48 horas sem resposta</option>
                  </select>
                </div>

                {/* IA Prompt instructions */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-white/90 flex items-center gap-1.5">
                    Instrução de Abordagem para a IA <Sparkles className="h-3 w-3 text-purple-400" />
                  </label>
                  <textarea
                    placeholder="Descreva como o robô deve quebrar o silêncio de forma amigável..."
                    value={inactPrompt}
                    onChange={(e) => setInactPrompt(e.target.value)}
                    rows={5}
                    className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] transition-all"
                  />
                  <div className="flex gap-2 p-3 bg-blue-950/20 border border-blue-500/15 rounded-lg text-[10px] text-blue-400 mt-1">
                    <Info className="h-4 w-4 shrink-0" />
                    <span>
                      Dica: A IA tem acesso total ao histórico da conversa recente e gerará um texto personalizado, garantindo que a abordagem faça total sentido no contexto.
                    </span>
                  </div>
                </div>

              </div>
            </div>
          </div>

          {/* Card B: Pending Action */}
          <div className="glass-panel p-6 flex flex-col justify-between border border-white/5 hover:border-white/10 transition-all duration-300">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-950/40 border border-purple-500/25 text-purple-400">
                    <Sparkles className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">Triagem Incompleta (Campos Pendentes)</h3>
                    <p className="text-[10px] text-[var(--color-foreground-muted)]">Cobrança focada nos dados que restam coletar</p>
                  </div>
                </div>
                
                <button
                  type="button"
                  onClick={() => setPendEnabled(!pendEnabled)}
                  className="focus:outline-none transition-transform active:scale-95"
                >
                  {pendEnabled ? (
                    <ToggleRight className="h-9 w-9 text-[var(--color-brand-500)]" />
                  ) : (
                    <ToggleLeft className="h-9 w-9 text-[var(--color-foreground-muted)]" />
                  )}
                </button>
              </div>

              <div className={`space-y-4 transition-all duration-300 ${pendEnabled ? "opacity-100" : "opacity-45 pointer-events-none select-none"}`}>
                
                {/* Delay hours */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-white/90 flex items-center gap-1">
                    Tempo de Espera para Cobrança
                  </label>
                  <select
                    value={pendDelay}
                    onChange={(e) => setPendDelay(Number(e.target.value))}
                    className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] transition-all [&>option]:bg-zinc-950"
                  >
                    <option value="0.5">30 minutos sem concluir triagem</option>
                    <option value="1">1 hora sem concluir triagem</option>
                    <option value="2">2 horas sem concluir triagem</option>
                    <option value="4">4 horas sem concluir triagem</option>
                  </select>
                </div>

                {/* IA Prompt instructions */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-white/90 flex items-center gap-1.5">
                    Instrução de Cobrança para a IA <Sparkles className="h-3 w-3 text-purple-400" />
                  </label>
                  <textarea
                    placeholder="Oriente a IA a cobrar amigavelmente as informações que faltam..."
                    value={pendPrompt}
                    onChange={(e) => setPendPrompt(e.target.value)}
                    rows={5}
                    className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] transition-all"
                  />
                  <div className="flex gap-2 p-3 bg-purple-950/20 border border-purple-500/15 rounded-lg text-[10px] text-purple-400 mt-1">
                    <HelpCircle className="h-4 w-4 shrink-0" />
                    <span>
                      Dica: Inclua <code className="bg-purple-950 px-1 py-0.5 rounded text-white font-mono font-bold">{"{campos_pendentes}"}</code> na sua instrução. O sistema substituirá dinamicamente pelos campos que faltam (ex: Nome, Idade) antes de passar a regra para a IA.
                    </span>
                  </div>
                </div>

              </div>
            </div>
          </div>

        </div>

        {/* Global Save Controls */}
        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-3 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white text-sm font-semibold rounded-xl flex items-center gap-2 shadow-lg shadow-[var(--color-brand-500)]/20 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] active:scale-[0.99] transition-all"
          >
            {submitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Salvar Configurações de Disparo
          </button>
        </div>

      </form>
    </div>
  );
}
