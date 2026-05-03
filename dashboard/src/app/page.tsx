"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Users, UserPlus, Flame, CalendarCheck } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface VisaoGeralData {
  cards: {
    total_leads: number;
    leads_recentes: number;
    leads_interessados: number;
    visitas: number;
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

  const stats = [
    { name: "Total de Leads", value: data.cards.total_leads, icon: Users, color: "text-blue-400" },
    { name: "Novos (7 dias)", value: data.cards.leads_recentes, icon: UserPlus, color: "text-green-400" },
    { name: "Interessados", value: data.cards.leads_interessados, icon: Flame, color: "text-orange-400" },
    { name: "Visitas Agendadas", value: data.cards.visitas, icon: CalendarCheck, color: "text-purple-400" },
  ];

  return (
    <div className="space-y-8">
      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="glass-panel p-6 card-hover">
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

      {/* Chart */}
      <div className="glass-panel p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Mensagens Recebidas (Últimos 7 dias)</h2>
        <div className="h-[400px] w-full">
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
    </div>
  );
}
