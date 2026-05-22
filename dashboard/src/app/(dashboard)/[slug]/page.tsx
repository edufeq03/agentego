"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { 
  Users, UserPlus, Flame, CalendarCheck, Clock, Moon, PauseCircle, 
  ShoppingBag, DollarSign, TrendingUp, Utensils, ChefHat, Sparkles 
} from "lucide-react";
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend 
} from "recharts";

interface VisaoGeralData {
  nicho: string;
  cards: {
    // Campos genericos
    total_leads?: number;
    leads_recentes?: number;
    leads_interessados?: number;
    visitas?: number;
    pausados: number;
    horario_comercial_pct?: number;
    fora_horario_pct?: number;
    total_mensagens_analisadas?: number;
    // Campos lanchonete
    total_pedidos?: number;
    pedidos_fila?: number;
    faturamento_total?: number;
    ticket_medio?: number;
    mesas_ativas?: number;
    dist_delivery?: number;
    dist_mesa?: number;
    dist_balcao?: number;
  };
  grafico_conversas: { dia: string; mensagens: number }[];
}

const COLORS = ["#3b82f6", "#8b5cf6", "#ec4899"];

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

  if (!data) return <div className="text-white text-center py-12">Erro ao carregar dados.</div>;

  const isLanchonete = data.nicho === "lanchonete";

  // Configurar os cards de acordo com o nicho
  const stats = isLanchonete 
    ? [
        { 
          name: "Total de Pedidos", 
          value: data.cards.total_pedidos ?? 0, 
          icon: ShoppingBag, 
          color: "text-blue-400" 
        },
        { 
          name: "Fila de Produção", 
          value: data.cards.pedidos_fila ?? 0, 
          icon: Flame, 
          color: "text-orange-400" 
        },
        { 
          name: "Faturamento", 
          value: `R$ ${(data.cards.faturamento_total ?? 0).toFixed(2)}`, 
          icon: DollarSign, 
          color: "text-emerald-400" 
        },
        { 
          name: "Ticket Médio", 
          value: `R$ ${(data.cards.ticket_medio ?? 0).toFixed(2)}`, 
          icon: TrendingUp, 
          color: "text-yellow-400" 
        },
        { 
          name: "Mesas Ativas", 
          value: data.cards.mesas_ativas ?? 0, 
          icon: ChefHat, 
          color: "text-purple-400" 
        },
      ]
    : [
        { name: "Total de Leads", value: data.cards.total_leads ?? 0, icon: Users, color: "text-blue-400" },
        { name: "Novos (7 dias)", value: data.cards.leads_recentes ?? 0, icon: UserPlus, color: "text-green-400" },
        { 
          name: data.nicho === "corretora" ? "Leads Triados" : "Interessados", 
          value: data.cards.leads_interessados ?? 0, 
          icon: Flame, 
          color: "text-orange-400" 
        },
        { 
          name: data.nicho === "corretora" ? "Cotações / Triagem" : "Visitas", 
          value: data.cards.visitas ?? 0, 
          icon: CalendarCheck, 
          color: "text-purple-400" 
        },
        { name: "Aguardando Humano", value: data.cards.pausados, icon: PauseCircle, color: "text-red-400" },
      ];

  const pizzaData = isLanchonete 
    ? [
        { name: "🛵 Delivery", value: data.cards.dist_delivery ?? 0 },
        { name: "🍽️ Mesa", value: data.cards.dist_mesa ?? 0 },
        { name: "🛍️ Balcão", value: data.cards.dist_balcao ?? 0 },
      ].filter(item => item.value > 0)
    : [];

  return (
    <div className="space-y-6">
      {/* Top Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="glass-panel p-5 card-hover">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-2xl bg-white/5 ${stat.color} shadow-inner`}>
                  <Icon size={24} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-[var(--color-foreground-muted)] uppercase tracking-wider">{stat.name}</p>
                  <p className="text-2xl font-black text-white mt-1.5 tracking-tight">{stat.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart Card */}
        <div className="glass-panel p-6 lg:col-span-2">
          <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
            {isLanchonete ? (
              <>
                <TrendingUp size={20} className="text-emerald-400" />
                Faturamento Diário (Últimos 7 dias)
              </>
            ) : (
              <>
                <ShoppingBag size={20} className="text-blue-400" />
                Mensagens Recebidas (Últimos 7 dias)
              </>
            )}
          </h2>
          
          <div className="h-[270px] w-full">
            {data.grafico_conversas.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.grafico_conversas} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
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
                    fontSize={11}
                    tickFormatter={(val) => new Date(val).toLocaleDateString("pt-BR", {day: "2-digit", month: "2-digit"})} 
                    tickMargin={10}
                  />
                  <YAxis 
                    stroke="var(--color-foreground-muted)" 
                    fontSize={11}
                    tickFormatter={(val) => isLanchonete ? `R$ ${val}` : Math.round(val).toString()} 
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)", borderRadius: "0.75rem", color: "white" }}
                    itemStyle={{ color: "var(--color-brand-400)" }}
                    labelFormatter={(val) => new Date(val).toLocaleDateString("pt-BR")}
                    formatter={(val: any) => isLanchonete ? [`R$ ${parseFloat(val).toFixed(2)}`, "Faturamento"] : [val, "Mensagens"]}
                  />
                  <Area type="monotone" dataKey="mensagens" stroke="var(--color-brand-500)" strokeWidth={3} fillOpacity={1} fill="url(#colorMsgs)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-[var(--color-foreground-muted)]">
                Sem faturamento ou conversas registradas nos últimos 7 dias.
              </div>
            )}
          </div>
        </div>

        {/* Right Side Column */}
        {isLanchonete ? (
          /* Lanchonete: Canais de Venda PieChart */
          <div className="glass-panel p-6 flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Utensils size={20} className="text-purple-400" />
                Canais de Venda
              </h2>
              <p className="text-xs text-[var(--color-foreground-muted)] mb-4">
                Percentual de pedidos por modalidade de atendimento.
              </p>
            </div>

            <div className="flex-1 w-full min-h-[200px] flex items-center justify-center">
              {pizzaData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pizzaData}
                      cx="50%"
                      cy="45%"
                      innerRadius={50}
                      outerRadius={75}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pizzaData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)", borderRadius: "0.5rem", color: "white" }}
                      formatter={(val) => [`${val}%`, "Proporção"]}
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center text-[var(--color-foreground-muted)] text-sm">
                  Sem vendas registradas para exibir gráfico de canais.
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Generico / Outros: Comportamento de Horario */
          <div className="glass-panel p-6 flex flex-col">
            <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <Clock size={20} className="text-yellow-400" />
              Comportamento de Horário
            </h2>
            <p className="text-xs text-[var(--color-foreground-muted)] mb-8">
              Análise de {data.cards.total_mensagens_analisadas} mensagens nos últimos 7 dias.
            </p>

            <div className="flex-1 flex flex-col justify-center gap-6">
              <div className="bg-[var(--color-surface-hover)] p-5 rounded-2xl border border-[var(--color-border)] relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                  <Clock size={64} />
                </div>
                <div className="flex items-center gap-3 mb-2">
                  <Clock className="text-yellow-400" size={20} />
                  <span className="font-semibold text-white/90 text-sm">Horário Comercial</span>
                </div>
                <div className="text-4xl font-black text-white">{data.cards.horario_comercial_pct}%</div>
                <p className="text-xs text-[var(--color-foreground-muted)] mt-2">Seg a Sex, 08h às 18h</p>
              </div>

              <div className="bg-[var(--color-surface-hover)] p-5 rounded-2xl border border-[var(--color-border)] relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                  <Moon size={64} />
                </div>
                <div className="flex items-center gap-3 mb-2">
                  <Moon className="text-indigo-400" size={20} />
                  <span className="font-semibold text-white/90 text-sm">Fora do Horário</span>
                </div>
                <div className="text-4xl font-black text-white">{data.cards.fora_horario_pct}%</div>
                <p className="text-xs text-[var(--color-foreground-muted)] mt-2">Noites e Finais de Semana</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
