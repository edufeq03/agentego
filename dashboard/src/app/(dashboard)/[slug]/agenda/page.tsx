"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { 
  Calendar as CalendarIcon, 
  Clock, 
  User, 
  Phone, 
  Check, 
  X, 
  Trash2, 
  Plus, 
  Filter, 
  AlertCircle, 
  CheckCircle,
  FileText
} from "lucide-react";
import api from "@/lib/api";

interface Agendamento {
  id: number;
  lead_id: string;
  lead_nome?: string;
  lead_telefone?: string;
  servico_id: string;
  servico_nome: string;
  servico_duracao: number;
  data: string;
  hora_inicio: string;
  hora_fim: string;
  status: 'confirmado' | 'pendente' | 'cancelado' | 'recusado';
  observacao?: string;
}

interface Lead {
  id: string;
  nome: string;
  telefone: string;
}

interface Servico {
  id: string;
  nome: string;
  duracao_min: number;
}

export default function AgendaPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [loading, setLoading] = useState(true);
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [statusFilter, setStatusFilter] = useState<string>("todos");

  // Modal states for manual booking
  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [servicos, setServicos] = useState<Servico[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState("");
  const [selectedServicoId, setSelectedServicoId] = useState("");
  const [bookDate, setBookDate] = useState("");
  const [availableSlots, setAvailableSlots] = useState<string[]>([]);
  const [bookTime, setBookTime] = useState("");
  const [bookObs, setBookObs] = useState("");
  const [slotsLoading, setSlotsLoading] = useState(false);

  // Selected Agendamento detail modal
  const [activeAgendamento, setActiveAgendamento] = useState<Agendamento | null>(null);

  useEffect(() => {
    fetchAgendamentos();
  }, [selectedDate]);

  useEffect(() => {
    if (isBookModalOpen) {
      fetchLeadsAndServices();
    }
  }, [isBookModalOpen]);

  // Recalculate slots when date or service changes
  useEffect(() => {
    if (bookDate && selectedServicoId) {
      fetchAvailableSlots();
    } else {
      setAvailableSlots([]);
    }
  }, [bookDate, selectedServicoId]);

  async function fetchAgendamentos() {
    try {
      setLoading(true);
      const res = await api.get(`dashboard/agenda/agendamentos?data=${selectedDate}`);
      setAgendamentos(res.data);
    } catch (err) {
      console.error("Erro ao carregar agendamentos:", err);
    } finally {
      setLoading(false);
    }
  }

  async function fetchLeadsAndServices() {
    try {
      // Fetch leads from database
      const leadRes = await api.get("dashboard/conversas");
      // Map lead details
      const uniqueLeads: Lead[] = leadRes.data.map((c: any) => ({
        id: c.lead_id,
        nome: c.lead_nome || "Sem Nome",
        telefone: c.telefone
      }));
      setLeads(uniqueLeads);

      // Fetch active services
      const servRes = await api.get("dashboard/agenda/servicos");
      setServicos(servRes.data.filter((s: any) => s.ativo));
    } catch (err) {
      console.error("Erro ao carregar leads/serviços:", err);
    }
  }

  async function fetchAvailableSlots() {
    try {
      setSlotsLoading(true);
      const res = await api.get(
        `dashboard/agenda/slots?servico_id=${selectedServicoId}&data=${bookDate}`
      );
      setAvailableSlots(res.data);
    } catch (err) {
      console.error("Erro ao carregar slots:", err);
    } finally {
      setSlotsLoading(false);
    }
  }

  async function handleUpdateStatus(id: number, newStatus: string) {
    try {
      await api.put(`dashboard/agenda/agendamentos/${id}/status`, { status: newStatus });
      fetchAgendamentos();
      if (activeAgendamento && activeAgendamento.id === id) {
        setActiveAgendamento({ ...activeAgendamento, status: newStatus as any });
      }
    } catch (err) {
      alert("Erro ao atualizar status do agendamento.");
    }
  }

  async function handleBookManual(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedLeadId || !selectedServicoId || !bookDate || !bookTime) {
      alert("Por favor, preencha todos os campos obrigatórios.");
      return;
    }

    try {
      await api.post("dashboard/agenda/agendamentos/manual", {
        lead_id: selectedLeadId,
        servico_id: selectedServicoId,
        data: bookDate,
        hora_inicio: bookTime,
        observacao: bookObs
      });
      setIsBookModalOpen(false);
      setSelectedLeadId("");
      setSelectedServicoId("");
      setBookDate("");
      setBookTime("");
      setBookObs("");
      fetchAgendamentos();
    } catch (err) {
      alert("Erro ao realizar agendamento manual. Verifique se o horário está disponível.");
    }
  }

  const filteredAgendamentos = agendamentos.filter((a) => {
    if (statusFilter === "todos") return true;
    return a.status === statusFilter;
  });

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-16">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Visualizar Agenda</h2>
          <p className="text-[var(--color-foreground-muted)] mt-1">
            Veja as solicitações, confirme horários e gerencie sua agenda diária.
          </p>
        </div>
        <button 
          onClick={() => {
            setBookDate(selectedDate);
            setIsBookModalOpen(true);
          }}
          className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-xl font-semibold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
        >
          <Plus size={18} />
          Agendar Cliente
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
        {/* Calendar Picker & Filters Left Column */}
        <div className="space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Selecionar Data</h3>
            <div className="relative">
              <CalendarIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" size={18} />
              <input 
                type="date" 
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all"
              />
            </div>
          </div>

          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Filtro de Status</h3>
            <div className="space-y-2">
              {[
                { id: "todos", label: "Todos" },
                { id: "confirmado", label: "Confirmados" },
                { id: "pendente", label: "Pendentes" },
                { id: "cancelado", label: "Cancelados / Recusados" }
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setStatusFilter(f.id)}
                  className={`w-full text-left px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    statusFilter === f.id 
                      ? "bg-[var(--color-brand-500)] text-white" 
                      : "text-[var(--color-foreground-muted)] hover:text-white hover:bg-[var(--color-surface-hover)]"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Schedule Slots / List Middle Columns */}
        <div className="lg:col-span-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden min-h-[400px]">
          <div className="p-6 border-b border-[var(--color-border)] flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Clock className="text-[var(--color-brand-400)]" />
              Compromissos para {selectedDate.split("-").reverse().join("/")}
            </h3>
            <span className="text-xs bg-[var(--color-surface-hover)] text-[var(--color-foreground-muted)] px-3 py-1.5 rounded-lg">
              {filteredAgendamentos.length} Encontrados
            </span>
          </div>

          {loading ? (
            <div className="text-center py-20 text-[var(--color-foreground-muted)]">Buscando compromissos...</div>
          ) : filteredAgendamentos.length === 0 ? (
            <div className="text-center py-20">
              <CalendarIcon className="mx-auto text-[var(--color-foreground-muted)] mb-4" size={48} />
              <p className="text-[var(--color-foreground-muted)] font-medium">Sem compromissos nesta data.</p>
            </div>
          ) : (
            <div className="divide-y divide-[var(--color-border)]">
              {filteredAgendamentos.map((a) => (
                <div 
                  key={a.id}
                  onClick={() => setActiveAgendamento(a)}
                  className="p-6 hover:bg-[var(--color-surface-hover)]/30 transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 group"
                >
                  <div className="flex items-start gap-4">
                    {/* Time Slot Indicator */}
                    <div className="bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl px-4 py-2.5 text-center min-w-[80px]">
                      <p className="text-sm font-bold text-white">{a.hora_inicio}</p>
                      <p className="text-[10px] text-[var(--color-foreground-muted)] mt-0.5">{a.hora_fim}</p>
                    </div>

                    <div className="space-y-1">
                      <h4 className="font-bold text-white group-hover:text-[var(--color-brand-400)] transition-colors">
                        {a.lead_nome || "Cliente sem Nome"}
                      </h4>
                      <p className="text-sm text-[var(--color-foreground-muted)]">
                        Serviço: <span className="text-white font-medium">{a.servico_nome}</span> ({a.servico_duracao} min)
                      </p>
                      {a.observacao && (
                        <p className="text-xs text-[var(--color-foreground-muted)] italic truncate max-w-md">
                          Obs: {a.observacao}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end md:self-center">
                    {/* Status Badge */}
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${
                      a.status === "confirmado" ? "bg-emerald-500/10 text-emerald-500" :
                      a.status === "pendente" ? "bg-amber-500/10 text-amber-500" :
                      "bg-red-500/10 text-red-500"
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        a.status === "confirmado" ? "bg-emerald-500" :
                        a.status === "pendente" ? "bg-amber-500" :
                        "bg-red-500"
                      }`} />
                      {a.status.toUpperCase()}
                    </span>

                    {/* Quick Action buttons */}
                    {a.status === "pendente" && (
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleUpdateStatus(a.id, "confirmado");
                          }}
                          className="p-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 rounded-lg transition-colors"
                          title="Confirmar"
                        >
                          <Check size={16} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleUpdateStatus(a.id, "recusar");
                          }}
                          className="p-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg transition-colors"
                          title="Recusar"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    )}

                    {a.status === "confirmado" && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm("Deseja realmente cancelar este agendamento confirmado?")) {
                            handleUpdateStatus(a.id, "cancelado");
                          }
                        }}
                        className="p-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                        title="Cancelar Agendamento"
                      >
                        <X size={16} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Booking Detail Modal */}
      {activeAgendamento && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setActiveAgendamento(null)} />
          <div className="relative bg-[var(--color-surface)] border border-[var(--color-border)] w-full max-w-md rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-[var(--color-border)] flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <FileText className="text-[var(--color-brand-400)]" />
                Detalhes do Agendamento
              </h3>
              <button 
                onClick={() => setActiveAgendamento(null)}
                className="text-[var(--color-foreground-muted)] hover:text-white"
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[var(--color-brand-500)]/10 flex items-center justify-center text-[var(--color-brand-400)]">
                    <User size={20} />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-foreground-muted)]">Cliente</p>
                    <p className="text-sm font-bold text-white">{activeAgendamento.lead_nome}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[var(--color-brand-500)]/10 flex items-center justify-center text-[var(--color-brand-400)]">
                    <Phone size={20} />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-foreground-muted)]">Telefone</p>
                    <p className="text-sm font-semibold text-white">{activeAgendamento.lead_telefone || "Sem telefone"}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[var(--color-brand-500)]/10 flex items-center justify-center text-[var(--color-brand-400)]">
                    <Clock size={20} />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-foreground-muted)]">Serviço / Horário</p>
                    <p className="text-sm font-semibold text-white">
                      {activeAgendamento.servico_nome} ({activeAgendamento.hora_inicio} às {activeAgendamento.hora_fim})
                    </p>
                  </div>
                </div>
              </div>

              {activeAgendamento.observacao && (
                <div className="p-3 bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl">
                  <p className="text-xs text-[var(--color-foreground-muted)] font-semibold">Observação do Cliente:</p>
                  <p className="text-xs text-white mt-1 leading-relaxed">{activeAgendamento.observacao}</p>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--color-border)]">
                {activeAgendamento.status === "pendente" && (
                  <>
                    <button
                      onClick={() => handleUpdateStatus(activeAgendamento.id, "recusar")}
                      className="flex-1 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl text-sm font-semibold transition-all"
                    >
                      Recusar
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(activeAgendamento.id, "confirmado")}
                      className="flex-1 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-sm font-semibold transition-all"
                    >
                      Confirmar
                    </button>
                  </>
                )}
                {activeAgendamento.status === "confirmado" && (
                  <button
                    onClick={() => {
                      if (confirm("Cancelar este agendamento?")) {
                        handleUpdateStatus(activeAgendamento.id, "cancelado");
                      }
                    }}
                    className="w-full py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-semibold transition-all"
                  >
                    Cancelar Agendamento
                  </button>
                )}
                {["cancelado", "recusado"].includes(activeAgendamento.status) && (
                  <p className="text-xs text-red-400 text-center w-full">Este agendamento foi cancelado/recusado.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Manual Booking Modal */}
      {isBookModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsBookModalOpen(false)} />
          <div className="relative bg-[var(--color-surface)] border border-[var(--color-border)] w-full max-w-md rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-[var(--color-border)] flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Plus className="text-[var(--color-brand-400)]" />
                Agendar Cliente Manualmente
              </h3>
              <button 
                onClick={() => setIsBookModalOpen(false)}
                className="text-[var(--color-foreground-muted)] hover:text-white"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleBookManual} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-sm text-white block">Selecionar Cliente (Lead)</label>
                <select
                  value={selectedLeadId}
                  onChange={(e) => setSelectedLeadId(e.target.value)}
                  required
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none"
                >
                  <option value="">Selecione um cliente...</option>
                  {leads.map((l) => (
                    <option key={l.id} value={l.id}>{l.nome} ({l.telefone})</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm text-white block">Serviço</label>
                <select
                  value={selectedServicoId}
                  onChange={(e) => setSelectedServicoId(e.target.value)}
                  required
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none"
                >
                  <option value="">Selecione o serviço...</option>
                  {servicos.map((s) => (
                    <option key={s.id} value={s.id}>{s.nome} ({s.duracao_min} min)</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm text-white block">Data</label>
                <input 
                  type="date"
                  value={bookDate}
                  onChange={(e) => setBookDate(e.target.value)}
                  required
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-sm text-white block">Escolher Horário Disponível</label>
                <select
                  value={bookTime}
                  disabled={slotsLoading || availableSlots.length === 0}
                  onChange={(e) => setBookTime(e.target.value)}
                  required
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none"
                >
                  {slotsLoading ? (
                    <option>Carregando horários...</option>
                  ) : availableSlots.length === 0 ? (
                    <option value="">Nenhum horário disponível para esta data</option>
                  ) : (
                    <>
                      <option value="">Selecione um horário...</option>
                      {availableSlots.map((time) => (
                        <option key={time} value={time}>{time}</option>
                      ))}
                    </>
                  )}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm text-white block">Observação (Opcional)</label>
                <input 
                  type="text"
                  value={bookObs}
                  onChange={(e) => setBookObs(e.target.value)}
                  placeholder="Ex: Cliente prefere atendimento na sala VIP..."
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--color-border)]">
                <button 
                  type="button" 
                  onClick={() => setIsBookModalOpen(false)}
                  className="px-4 py-2 bg-[var(--color-surface-hover)] text-white rounded-xl text-sm font-semibold transition-all"
                >
                  Cancelar
                </button>
                <button 
                  type="submit"
                  className="px-4 py-2 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-xl text-sm font-semibold transition-all"
                >
                  Confirmar Agendamento
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
