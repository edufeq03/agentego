"use client";

import { useState, useEffect } from "react";
import { useParams as useNextParams } from "next/navigation";
import { 
  Clock, 
  Settings, 
  ShieldAlert, 
  Trash2, 
  Plus, 
  Calendar, 
  X, 
  Smartphone, 
  CheckCircle,
  Save
} from "lucide-react";
import api from "@/lib/api";

interface Disponibilidade {
  dia_semana: number;
  hora_inicio: string;
  hora_fim: string;
  intervalo_min: number;
  ativo: boolean;
}

interface Bloqueio {
  id: string;
  data: string;
  hora_inicio: string;
  hora_fim: string;
  motivo: string;
}

const DIAS_SEMANA = [
  "Segunda-feira",
  "Terça-feira",
  "Quarta-feira",
  "Quinta-feira",
  "Sexta-feira",
  "Sábado",
  "Domingo"
];

export default function ConfigAgendaPage() {
  const params = useNextParams();
  const slug = params?.slug as string;

  const [loading, setLoading] = useState(true);
  
  // States - Operating hours
  const [disponibilidades, setDisponibilidades] = useState<Disponibilidade[]>([]);
  
  // States - Settings
  const [aprovacaoManual, setAprovacaoManual] = useState(true);
  const [whatsappProfissional, setWhatsappProfissional] = useState("");
  const [lembreteClienteMin, setLembreteClienteMin] = useState(120);
  const [lembreteProfissionalHora, setLembreteProfissionalHora] = useState("08:00");
  const [aprovacaoTimeoutMin, setAprovacaoTimeoutMin] = useState(60);

  // States - Blocks
  const [bloqueios, setBloqueios] = useState<Bloqueio[]>([]);
  const [isBlockModalOpen, setIsBlockModalOpen] = useState(false);
  const [blockData, setBlockData] = useState("");
  const [blockHoraInicio, setBlockHoraInicio] = useState("09:00");
  const [blockHoraFim, setBlockHoraFim] = useState("18:00");
  const [blockMotivo, setBlockMotivo] = useState("");

  useEffect(() => {
    fetchConfigs();
  }, []);

  async function fetchConfigs() {
    try {
      setLoading(true);
      // Load availability
      const dispRes = await api.get("dashboard/agenda/disponibilidade");
      const fetchedDisp: Disponibilidade[] = dispRes.data;
      
      // Populate defaults for missing days
      const finalDisp: Disponibilidade[] = [];
      for (let i = 0; i < 7; i++) {
        const found = fetchedDisp.find(d => d.dia_semana === i);
        if (found) {
          finalDisp.push(found);
        } else {
          finalDisp.push({
            dia_semana: i,
            hora_inicio: "09:00",
            hora_fim: "18:00",
            intervalo_min: 30,
            ativo: i < 5 // Segunda a Sexta ativo por padrão
          });
        }
      }
      setDisponibilidades(finalDisp);

      // Load config
      const confRes = await api.get("dashboard/agenda/config");
      const c = confRes.data;
      setAprovacaoManual(c.aprovacao_manual ?? true);
      setWhatsappProfissional(c.whatsapp_profissional ?? c.whatsapp_professional ?? "");
      setLembreteClienteMin(c.lembrete_cliente_min ?? 120);
      setLembreteProfissionalHora(c.lembrete_profissional_hora ?? "08:00");
      setAprovacaoTimeoutMin(c.aprovacao_timeout_min ?? 60);

      // Load blocks
      const blockRes = await api.get("dashboard/agenda/bloqueios");
      setBloqueios(blockRes.data);

    } catch (err) {
      console.error("Erro ao carregar dados de configuração:", err);
    } finally {
      setLoading(false);
    }
  }

  function handleDispChange(index: number, field: keyof Disponibilidade, value: any) {
    const updated = [...disponibilidades];
    updated[index] = { ...updated[index], [field]: value };
    setDisponibilidades(updated);
  }

  async function handleSaveDisp() {
    try {
      await api.post("dashboard/agenda/disponibilidade", disponibilidades);
      alert("Horários de funcionamento salvos com sucesso!");
    } catch (err) {
      alert("Erro ao salvar horários de funcionamento.");
    }
  }

  async function handleSaveGeneral() {
    try {
      await api.put("dashboard/agenda/config", {
        aprovacao_manual: aprovacaoManual,
        whatsapp_profissional: whatsappProfissional,
        lembrete_cliente_min: lembreteClienteMin,
        lembrete_profissional_hora: lembreteProfissionalHora,
        aprovacao_timeout_min: aprovacaoTimeoutMin
      });
      alert("Configurações gerais salvas com sucesso!");
    } catch (err) {
      alert("Erro ao salvar configurações gerais.");
    }
  }

  async function handleCreateBlock(e: React.FormEvent) {
    e.preventDefault();
    if (!blockData) return;
    try {
      await api.post("dashboard/agenda/bloqueios", {
        data: blockData,
        hora_inicio: blockHoraInicio,
        hora_fim: blockHoraFim,
        motivo: blockMotivo
      });
      setIsBlockModalOpen(false);
      setBlockData("");
      setBlockMotivo("");
      // reload blocks
      const blockRes = await api.get("dashboard/agenda/bloqueios");
      setBloqueios(blockRes.data);
    } catch (err) {
      alert("Erro ao criar bloqueio de horário.");
    }
  }

  async function handleDeleteBlock(id: string) {
    if (!confirm("Deseja remover este bloqueio de horário?")) return;
    try {
      await api.delete(`dashboard/agenda/bloqueios/${id}`);
      setBloqueios(bloqueios.filter(b => b.id !== id));
    } catch (err) {
      alert("Erro ao excluir bloqueio.");
    }
  }

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-16">
      <div>
        <h2 className="text-3xl font-bold text-white tracking-tight">Configurações da Agenda</h2>
        <p className="text-[var(--color-foreground-muted)] mt-1">
          Gerencie horários de funcionamento, regras de aprovação e bloqueios específicos.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-[var(--color-foreground-muted)]">Carregando configurações...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 1. HORÁRIOS DE ATENDIMENTO */}
          <div className="lg:col-span-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-4">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Clock className="text-[var(--color-brand-400)]" size={20} />
                Horários de Atendimento Semanal
              </h3>
              <button 
                onClick={handleSaveDisp}
                className="flex items-center gap-2 px-4 py-2 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-xl font-semibold transition-all"
              >
                <Save size={16} />
                Salvar Horários
              </button>
            </div>

            <div className="space-y-4">
              {disponibilidades.map((d, index) => (
                <div 
                  key={index}
                  className={`grid grid-cols-1 md:grid-cols-4 items-center gap-4 p-4 rounded-xl transition-colors ${
                    d.ativo ? "bg-[var(--color-surface-hover)]/30 border border-[var(--color-border)]" : "opacity-50 border border-transparent"
                  }`}
                >
                  {/* Ativo checkbox & Dia da semana */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox"
                      id={`day-${index}`}
                      checked={d.ativo}
                      onChange={(e) => handleDispChange(index, "ativo", e.target.checked)}
                      className="w-5 h-5 accent-[var(--color-brand-500)] rounded bg-[var(--color-background)] border border-[var(--color-border)]"
                    />
                    <label htmlFor={`day-${index}`} className="text-sm font-semibold text-white cursor-pointer select-none">
                      {DIAS_SEMANA[index]}
                    </label>
                  </div>

                  {/* Hora Início */}
                  <div className="space-y-1">
                    <label className="text-xs text-[var(--color-foreground-muted)] block">Hora Início</label>
                    <input 
                      type="time"
                      value={d.hora_inicio}
                      disabled={!d.ativo}
                      onChange={(e) => handleDispChange(index, "hora_inicio", e.target.value)}
                      className="w-full bg-[var(--color-background)] disabled:opacity-50 border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none"
                    />
                  </div>

                  {/* Hora Fim */}
                  <div className="space-y-1">
                    <label className="text-xs text-[var(--color-foreground-muted)] block">Hora Término</label>
                    <input 
                      type="time"
                      value={d.hora_fim}
                      disabled={!d.ativo}
                      onChange={(e) => handleDispChange(index, "hora_fim", e.target.value)}
                      className="w-full bg-[var(--color-background)] disabled:opacity-50 border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none"
                    />
                  </div>

                  {/* Intervalo */}
                  <div className="space-y-1">
                    <label className="text-xs text-[var(--color-foreground-muted)] block">Intervalo Geração (Minutos)</label>
                    <select
                      value={d.intervalo_min}
                      disabled={!d.ativo}
                      onChange={(e) => handleDispChange(index, "intervalo_min", parseInt(e.target.value))}
                      className="w-full bg-[var(--color-background)] disabled:opacity-50 border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none"
                    >
                      <option value={15}>15 min</option>
                      <option value={20}>20 min</option>
                      <option value={30}>30 min</option>
                      <option value={45}>45 min</option>
                      <option value={60}>60 min</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 2. REGRAS GERAIS E BLOQUEIOS */}
          <div className="space-y-8">
            {/* CONFIGURAÇÕES GERAIS */}
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-4">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <Settings className="text-[var(--color-brand-400)]" size={20} />
                  Regras de Automação
                </h3>
                <button 
                  onClick={handleSaveGeneral}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-lg text-sm font-semibold transition-all"
                >
                  Salvar
                </button>
              </div>

              <div className="space-y-5">
                {/* Aprovação manual toggle */}
                <div className="flex items-start justify-between gap-4 p-3 bg-[var(--color-surface-hover)]/30 border border-[var(--color-border)] rounded-xl">
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-white">Aprovação Manual</p>
                    <p className="text-xs text-[var(--color-foreground-muted)] leading-relaxed">
                      Novos agendamentos entram como pendente e aguardam resposta do profissional via WhatsApp.
                    </p>
                  </div>
                  <input 
                    type="checkbox"
                    checked={aprovacaoManual}
                    onChange={(e) => setAprovacaoManual(e.target.checked)}
                    className="w-5 h-5 accent-[var(--color-brand-500)] rounded mt-1 shrink-0"
                  />
                </div>

                {/* WhatsApp do profissional */}
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-white flex items-center gap-1.5">
                    <Smartphone size={16} className="text-[var(--color-brand-400)]" />
                    WhatsApp do Profissional
                  </label>
                  <input 
                    type="text" 
                    value={whatsappProfissional}
                    onChange={(e) => setWhatsappProfissional(e.target.value)}
                    placeholder="Ex: 5511999998888"
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-3 text-sm text-white focus:outline-none focus:ring-1 focus:ring-[var(--color-brand-500)]"
                  />
                  <p className="text-xs text-[var(--color-foreground-muted)]">
                    Telefone que receberá as solicitações e enviará comandos para aceitar ou recusar.
                  </p>
                </div>

                {/* Timeout para aprovação */}
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-white block">Timeout de Aprovação (Minutos)</label>
                  <input 
                    type="number" 
                    value={aprovacaoTimeoutMin}
                    onChange={(e) => setAprovacaoTimeoutMin(parseInt(e.target.value) || 60)}
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-3 text-sm text-white focus:outline-none"
                  />
                  <p className="text-xs text-[var(--color-foreground-muted)]">
                    Tempo limite antes que uma solicitação pendente expire e libere o slot.
                  </p>
                </div>

                {/* Lembrete ao cliente */}
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-white block">Lembrete ao Cliente (Antes do horário)</label>
                  <select
                    value={lembreteClienteMin}
                    onChange={(e) => setLembreteClienteMin(parseInt(e.target.value))}
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-3 text-sm text-white focus:outline-none"
                  >
                    <option value={30}>30 min antes</option>
                    <option value={60}>1 hora antes</option>
                    <option value={120}>2 horas antes</option>
                    <option value={180}>3 horas antes</option>
                    <option value={1440}>1 dia antes</option>
                  </select>
                </div>

                {/* Resumo Diário */}
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-white block">Horário do Resumo de Agendamentos</label>
                  <input 
                    type="time" 
                    value={lembreteProfissionalHora}
                    onChange={(e) => setLembreteProfissionalHora(e.target.value)}
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-3 text-sm text-white focus:outline-none"
                  />
                  <p className="text-xs text-[var(--color-foreground-muted)]">
                    Horário em que o profissional receberá a listagem com a agenda de hoje.
                  </p>
                </div>
              </div>
            </div>

            {/* BLOQUEIOS DE HORÁRIOS */}
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-4">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <ShieldAlert className="text-[var(--color-brand-400)]" size={20} />
                  Bloqueios de Horário
                </h3>
                <button 
                  onClick={() => setIsBlockModalOpen(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm font-semibold transition-all hover:bg-red-500/20"
                >
                  <Plus size={16} />
                  Novo Bloqueio
                </button>
              </div>

              {bloqueios.length === 0 ? (
                <p className="text-sm text-[var(--color-foreground-muted)] text-center py-4">Nenhum horário bloqueado.</p>
              ) : (
                <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                  {bloqueios.map((b) => (
                    <div 
                      key={b.id}
                      className="flex items-center justify-between p-3 bg-red-500/5 border border-red-500/10 rounded-xl"
                    >
                      <div>
                        <p className="text-sm font-semibold text-white">{b.motivo || "Folga/Bloqueio"}</p>
                        <p className="text-xs text-[var(--color-foreground-muted)] mt-1">
                          {b.data.split("-").reverse().join("/")} | {b.hora_inicio} - {b.hora_fim}
                        </p>
                      </div>
                      <button 
                        onClick={() => handleDeleteBlock(b.id)}
                        className="p-1.5 text-[var(--color-foreground-muted)] hover:text-red-400 rounded-lg"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal - Novo Bloqueio */}
      {isBlockModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsBlockModalOpen(false)} />
          <div className="relative bg-[var(--color-surface)] border border-[var(--color-border)] w-full max-w-md rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-[var(--color-border)] flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Calendar className="text-[var(--color-brand-400)]" />
                Bloquear Horário
              </h3>
              <button 
                onClick={() => setIsBlockModalOpen(false)}
                className="text-[var(--color-foreground-muted)] hover:text-white"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleCreateBlock} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-sm text-white block">Data</label>
                <input 
                  type="date"
                  value={blockData}
                  onChange={(e) => setBlockData(e.target.value)}
                  required
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-3 text-sm text-white focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-sm text-white block">Hora Início</label>
                  <input 
                    type="time"
                    value={blockHoraInicio}
                    onChange={(e) => setBlockHoraInicio(e.target.value)}
                    required
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-3 text-sm text-white focus:outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm text-white block">Hora Término</label>
                  <input 
                    type="time"
                    value={blockHoraFim}
                    onChange={(e) => setBlockHoraFim(e.target.value)}
                    required
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-3 text-sm text-white focus:outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-sm text-white block">Motivo / Descrição</label>
                <input 
                  type="text"
                  value={blockMotivo}
                  onChange={(e) => setBlockMotivo(e.target.value)}
                  placeholder="Ex: Feriado, Consulta Médica..."
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2 px-3 text-sm text-white focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--color-border)]">
                <button 
                  type="button" 
                  onClick={() => setIsBlockModalOpen(false)}
                  className="px-4 py-2 bg-[var(--color-surface-hover)] text-white rounded-xl text-sm font-semibold transition-all"
                >
                  Cancelar
                </button>
                <button 
                  type="submit"
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-semibold transition-all"
                >
                  Bloquear Horário
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
