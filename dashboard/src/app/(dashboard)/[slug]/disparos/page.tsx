"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Zap, Check, AlertCircle, Save, Info, Plus, Trash2, ToggleLeft, ToggleRight, Hourglass, Sparkles, Loader2 } from "lucide-react";

interface ReengagementStep {
  step: number;
  delay_hours: number;
  prompt: string;
}

export default function ReengagementConfigPage() {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Inactivity Trigger States
  const [inactEnabled, setInactEnabled] = useState(false);
  const [inactSteps, setInactSteps] = useState<ReengagementStep[]>([]);

  // Pending Fields Trigger States
  const [pendEnabled, setPendEnabled] = useState(false);
  const [pendSteps, setPendSteps] = useState<ReengagementStep[]>([]);

  useEffect(() => {
    fetchConfig();
  }, []);

  async function fetchConfig() {
    try {
      setLoading(true);
      const response = await api.get("dashboard/marketing/reengagement");
      const data = response.data;
      
      setInactEnabled(data.reengagement_inactivity_enabled);
      setInactSteps(data.reengagement_inactivity_steps || []);
      
      setPendEnabled(data.reengagement_pending_enabled);
      setPendSteps(data.reengagement_pending_steps || []);
    } catch (error: any) {
      console.error("Erro ao carregar configurações de reengajamento:", error);
      setErrorMsg("Não foi possível carregar as configurações de disparos sequenciais.");
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

      // Higienizar prompts removendo espaços extras
      const sanitizedInact = inactSteps.map(s => ({ ...s, prompt: s.prompt.trim() }));
      const sanitizedPend = pendSteps.map(s => ({ ...s, prompt: s.prompt.trim() }));

      // Validação básica: impedir prompts vazios
      if (inactEnabled && sanitizedInact.some(s => !s.prompt)) {
        setErrorMsg("Por favor, preencha as instruções de IA para todas as abordagens de inatividade.");
        return;
      }
      if (pendEnabled && sanitizedPend.some(s => !s.prompt)) {
        setErrorMsg("Por favor, preencha as instruções de IA para todas as abordagens de triagem incompleta.");
        return;
      }

      const payload = {
        reengagement_inactivity_enabled: inactEnabled,
        reengagement_inactivity_steps: sanitizedInact,
        
        reengagement_pending_enabled: pendEnabled,
        reengagement_pending_steps: sanitizedPend,
      };

      await api.post("dashboard/marketing/reengagement", payload);
      showToast("Esteiras de reengajamento salvas com sucesso!");
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

  // --- Dynamic Step Modifiers ---

  function handleAddInactStep() {
    const nextNum = inactSteps.length + 1;
    const defaultDelays = [2, 6, 24, 48, 72];
    const delay = defaultDelays[inactSteps.length] || 24;
    setInactSteps([
      ...inactSteps,
      { step: nextNum, delay_hours: delay, prompt: "" }
    ]);
  }

  function handleRemoveInactStep(index: number) {
    if (inactSteps.length <= 1) return;
    const updated = inactSteps
      .filter((_, i) => i !== index)
      .map((s, i) => ({ ...s, step: i + 1 }));
    setInactSteps(updated);
  }

  function handleUpdateInactStep(index: number, field: keyof ReengagementStep, value: any) {
    const updated = [...inactSteps];
    updated[index] = { ...updated[index], [field]: value };
    setInactSteps(updated);
  }

  function handleAddPendStep() {
    const nextNum = pendSteps.length + 1;
    const defaultDelays = [1, 4, 12, 24];
    const delay = defaultDelays[pendSteps.length] || 12;
    setPendSteps([
      ...pendSteps,
      { step: nextNum, delay_hours: delay, prompt: "" }
    ]);
  }

  function handleRemovePendStep(index: number) {
    if (pendSteps.length <= 1) return;
    const updated = pendSteps
      .filter((_, i) => i !== index)
      .map((s, i) => ({ ...s, step: i + 1 }));
    setPendSteps(updated);
  }

  function handleUpdatePendStep(index: number, field: keyof ReengagementStep, value: any) {
    const updated = [...pendSteps];
    updated[index] = { ...updated[index], [field]: value };
    setPendSteps(updated);
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[300px] gap-3">
        <Loader2 className="animate-spin h-10 w-10 text-[var(--color-brand-500)]" />
        <span className="text-sm font-medium text-[var(--color-foreground-muted)]">Carregando construtor de cadência...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Zap className="text-[var(--color-brand-500)] fill-[var(--color-brand-500)]/15 h-7 w-7 animate-pulse" /> Disparos da IA (Cadência de Reengajamento)
          </h2>
          <p className="text-[var(--color-foreground-muted)] mt-1 max-w-3xl">
            Configure esteiras de reengajamento automatizadas. Defina uma sequência de mensagens com diferentes tempos de silêncio para contatar leads frios de forma dinâmica e humanizada.
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
          
          {/* Card A: Inactivity Cadence */}
          <div className="glass-panel p-6 border border-white/5 hover:border-white/10 transition-all duration-300">
            <div className="space-y-5">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-orange-950/40 border border-orange-500/25 text-orange-400">
                    <Hourglass className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">Reengajamento por Inatividade</h3>
                    <p className="text-[10px] text-[var(--color-foreground-muted)]">Disparado em passos quando o lead some</p>
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

              <div className={`space-y-6 transition-all duration-300 ${inactEnabled ? "opacity-100" : "opacity-40 pointer-events-none select-none"}`}>
                
                {/* Timeline vertical sequence */}
                <div className="relative pl-8 space-y-6">
                  {/* Timeline dotted connection line */}
                  {inactSteps.length > 1 && (
                    <div className="absolute left-[15px] top-6 bottom-6 w-[1.5px] border-l border-dashed border-white/15" />
                  )}

                  {inactSteps.map((step, idx) => (
                    <div key={idx} className="relative bg-white/[0.02] border border-white/5 rounded-xl p-4 space-y-3 hover:border-white/10 transition-all duration-200">
                      
                      {/* Step marker dot */}
                      <div className="absolute -left-[23.5px] top-5 h-[12px] w-[12px] rounded-full border border-orange-500 bg-zinc-950 flex items-center justify-center">
                        <div className="h-1.5 w-1.5 rounded-full bg-orange-500" />
                      </div>

                      {/* Header Row of step */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-orange-400 uppercase tracking-wider">Abordagem {step.step}</span>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <select
                            value={step.delay_hours}
                            onChange={(e) => handleUpdateInactStep(idx, "delay_hours", Number(e.target.value))}
                            className="bg-zinc-900 border border-white/10 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-orange-500 transition-all"
                          >
                            <option value="1">Aguardar 1h</option>
                            <option value="2">Aguardar 2h</option>
                            <option value="4">Aguardar 4h</option>
                            <option value="6">Aguardar 6h</option>
                            <option value="12">Aguardar 12h</option>
                            <option value="24">Aguardar 24h</option>
                            <option value="48">Aguardar 48h</option>
                          </select>

                          {inactSteps.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleRemoveInactStep(idx)}
                              className="text-white/40 hover:text-red-400 transition-colors p-1"
                              title="Remover etapa"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Prompt script */}
                      <textarea
                        placeholder="Roteiro de abordagem para esta etapa específica..."
                        value={step.prompt}
                        onChange={(e) => handleUpdateInactStep(idx, "prompt", e.target.value)}
                        rows={3}
                        className="w-full bg-black/25 border border-white/5 rounded-lg px-3 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-orange-500 transition-all"
                      />
                    </div>
                  ))}
                </div>

                {/* Add Step Control */}
                <button
                  type="button"
                  onClick={handleAddInactStep}
                  className="w-full py-2.5 border border-dashed border-white/10 hover:border-orange-500/30 hover:bg-orange-500/[0.02] rounded-xl text-xs font-semibold text-orange-400/90 flex items-center justify-center gap-1.5 transition-all"
                >
                  <Plus className="h-3.5 w-3.5" /> Adicionar Abordagem Sequencial
                </button>

                <div className="flex gap-2 p-3 bg-blue-950/20 border border-blue-500/15 rounded-lg text-[10px] text-blue-400">
                  <Info className="h-4 w-4 shrink-0" />
                  <span>
                    Dica: O robô consultará o histórico recente e gerará um texto único para quebrar o silêncio de acordo com as diretrizes da etapa correspondente.
                  </span>
                </div>

              </div>
            </div>
          </div>

          {/* Card B: Pending Fields Cadence */}
          <div className="glass-panel p-6 border border-white/5 hover:border-white/10 transition-all duration-300">
            <div className="space-y-5">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-950/40 border border-purple-500/25 text-purple-400">
                    <Sparkles className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">Triagem Incompleta (Campos Pendentes)</h3>
                    <p className="text-[10px] text-[var(--color-foreground-muted)]">Cobre dados de triagem em passos cadenciados</p>
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

              <div className={`space-y-6 transition-all duration-300 ${pendEnabled ? "opacity-100" : "opacity-40 pointer-events-none select-none"}`}>
                
                {/* Timeline vertical sequence */}
                <div className="relative pl-8 space-y-6">
                  {/* Timeline dotted connection line */}
                  {pendSteps.length > 1 && (
                    <div className="absolute left-[15px] top-6 bottom-6 w-[1.5px] border-l border-dashed border-white/15" />
                  )}

                  {pendSteps.map((step, idx) => (
                    <div key={idx} className="relative bg-white/[0.02] border border-white/5 rounded-xl p-4 space-y-3 hover:border-white/10 transition-all duration-200">
                      
                      {/* Step marker dot */}
                      <div className="absolute -left-[23.5px] top-5 h-[12px] w-[12px] rounded-full border border-purple-500 bg-zinc-950 flex items-center justify-center">
                        <div className="h-1.5 w-1.5 rounded-full bg-purple-500" />
                      </div>

                      {/* Header Row of step */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-purple-400 uppercase tracking-wider">Abordagem {step.step}</span>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <select
                            value={step.delay_hours}
                            onChange={(e) => handleUpdatePendStep(idx, "delay_hours", Number(e.target.value))}
                            className="bg-zinc-900 border border-white/10 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-purple-500 transition-all"
                          >
                            <option value="0.5">Aguardar 30min</option>
                            <option value="1">Aguardar 1h</option>
                            <option value="2">Aguardar 2h</option>
                            <option value="4">Aguardar 4h</option>
                            <option value="6">Aguardar 6h</option>
                            <option value="12">Aguardar 12h</option>
                            <option value="24">Aguardar 24h</option>
                          </select>

                          {pendSteps.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleRemovePendStep(idx)}
                              className="text-white/40 hover:text-red-400 transition-colors p-1"
                              title="Remover etapa"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Prompt script */}
                      <textarea
                        placeholder="Roteiro para solicitar os dados em falta..."
                        value={step.prompt}
                        onChange={(e) => handleUpdatePendStep(idx, "prompt", e.target.value)}
                        rows={3}
                        className="w-full bg-black/25 border border-white/5 rounded-lg px-3 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-purple-500 transition-all"
                      />
                    </div>
                  ))}
                </div>

                {/* Add Step Control */}
                <button
                  type="button"
                  onClick={handleAddPendStep}
                  className="w-full py-2.5 border border-dashed border-white/10 hover:border-purple-500/30 hover:bg-purple-500/[0.02] rounded-xl text-xs font-semibold text-purple-400/90 flex items-center justify-center gap-1.5 transition-all"
                >
                  <Plus className="h-3.5 w-3.5" /> Adicionar Abordagem Sequencial
                </button>

                <div className="flex gap-2 p-3 bg-purple-950/20 border border-purple-500/15 rounded-lg text-[10px] text-purple-400">
                  <Info className="h-4 w-4 shrink-0" />
                  <span>
                    Dica: Use a tag <code className="bg-purple-950 px-1 py-0.5 rounded text-white font-mono font-bold">{"{campos_pendentes}"}</code> na sua instrução. Ela será preenchida automaticamente com as informações faltantes de triagem no WhatsApp.
                  </span>
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
            Salvar Esteiras de Reengajamento
          </button>
        </div>

      </form>
    </div>
  );
}
