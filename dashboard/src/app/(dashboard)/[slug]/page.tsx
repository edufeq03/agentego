"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Users, UserPlus, Flame, CalendarCheck, Clock, Moon, PauseCircle } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface VisaoGeralData {
  nicho: string;
  cards: {
    total_leads: number;
    leads_recentes: number;
    leads_interessados: number;
    visitas: number;
    pausados: number;
    horario_comercial_pct: number;
    fora_horario_pct: number;
    total_mensagens_analisadas: number;
  };
  grafico_conversas: { dia: string; mensagens: number }[];
}

export default function Home() {
  const [data, setData] = useState<VisaoGeralData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await api.get("/dashboard/visao-geral");
        setData(response.data);
      } catch (error) {
        console.error("Erro ao buscar dados:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--color-brand-500)]"></div>
      </div>
    );
  }

  if (!data) return <div>Erro ao carregar dados.</div>;

  const isCorretora = data.nicho === "corretora";
  const stats = [
    { name: "Total de Leads", value: data.cards.total_leads, icon: Users, color: "text-blue-400" },
    { name: "Novos (7 dias)", value: data.cards.leads_recentes, icon: UserPlus, color: "text-green-400" },
    { name: isCorretora ? "Leads Triados" : "Interessados", value: data.cards.leads_interessados, icon: Flame, color: "text-orange-400" },
    { name: isCorretora ? "Cotações / Triagem" : "Visitas", value: data.cards.visitas, icon: CalendarCheck, color: "text-purple-400" },
    { name: "Aguardando Humano", value: data.cards.pausados, icon: PauseCircle, color: "text-red-400" },
  ];

  return (
    <div className="space-y-6">
      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="glass-panel p-4 card-hover">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-xl bg-white/5 ${stat.color}`}>
                  <Icon size={24} />
                </div>
                <div>
                  <p className="text-sm font-medium text-[var(--color-foreground-muted)]">{stat.name}</p>
                  <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="glass-panel p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-white mb-6">Mensagens Recebidas (Últimos 7 dias)</h2>
          <div className="h-[250px] w-full">
            {data.grafico_conversas.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.grafico_conversas} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorMsgs" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-brand-500)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--color-brand-500)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                  <XAxis 
                    dataKey="dia" 
                    stroke="var(--color-foreground-muted)" 
                    tickFormatter={(val) => new Date(val).toLocaleDateString('pt-BR', {day: '2-digit', month: '2-digit'})} 
                    tickMargin={10}
                  />
                  <YAxis stroke="var(--color-foreground-muted)" tickFormatter={(val) => Math.round(val).toString()} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '0.5rem', color: 'white' }}
                    itemStyle={{ color: 'var(--color-brand-400)' }}
                    labelFormatter={(val) => new Date(val).toLocaleDateString('pt-BR')}
                  />
                  <Area type="monotone" dataKey="mensagens" stroke="var(--color-brand-500)" strokeWidth={3} fillOpacity={1} fill="url(#colorMsgs)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-[var(--color-foreground-muted)]">
                Sem dados suficientes para gerar o gráfico.
              </div>
            )}
          </div>
        </div>

        {/* Métrica de Horários */}
        <div className="glass-panel p-6 flex flex-col">
          <h2 className="text-lg font-semibold text-white mb-2">Comportamento de Horário</h2>
          <p className="text-sm text-[var(--color-foreground-muted)] mb-8">
            Análise de {data.cards.total_mensagens_analisadas} mensagens nos últimos 7 dias.
          </p>

          <div className="flex-1 flex flex-col justify-center gap-6">
            <div className="bg-[var(--color-surface-hover)] p-5 rounded-2xl border border-[var(--color-border)] relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <Clock size={64} />
              </div>
              <div className="flex items-center gap-3 mb-2">
                <Clock className="text-yellow-400" size={20} />
                <span className="font-medium text-[var(--color-foreground-muted)]">Horário Comercial</span>
              </div>
              <div className="text-4xl font-bold text-white">{data.cards.horario_comercial_pct}%</div>
              <p className="text-xs text-[var(--color-foreground-muted)] mt-2">Seg a Sex, 08h às 18h</p>
            </div>

            <div className="bg-[var(--color-surface-hover)] p-5 rounded-2xl border border-[var(--color-border)] relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <Moon size={64} />
              </div>
              <div className="flex items-center gap-3 mb-2">
                <Moon className="text-indigo-400" size={20} />
                <span className="font-medium text-[var(--color-foreground-muted)]">Fora do Horário</span>
              </div>
              <div className="text-4xl font-bold text-white">{data.cards.fora_horario_pct}%</div>
              <p className="text-xs text-[var(--color-foreground-muted)] mt-2">Noites e Finais de Semana</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
