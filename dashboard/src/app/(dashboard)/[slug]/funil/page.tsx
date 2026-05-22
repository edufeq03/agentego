"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import api from "@/lib/api";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, 
  PieChart, Pie, Legend 
} from "recharts";
import { BrainCircuit, MessageSquareText, Filter, Lightbulb } from "lucide-react";

interface FunilData {
  name: string;
  value: number;
  fill: string;
}

interface IntencaoData {
  name: string;
  value: number;
}

const COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f97316", "#10b981"];

export default function FunilInsights() {
  const params = useParams();
  const slug = params?.slug as string;

  const [funilData, setFunilData] = useState<FunilData[]>([]);
  const [intencoesData, setIntencoesData] = useState<IntencaoData[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeMenuTab, setActiveMenuTab] = useState<"funil" | "insights">("funil");

  useEffect(() => {
    async function fetchData() {
      if (!slug) return;
      try {
        setLoading(true);
        const [funilRes, intencoesRes] = await Promise.all([
          api.get("dashboard/funil"),
          api.get("dashboard/intencoes")
        ]);
        setFunilData(funilRes.data || []);
        setIntencoesData(intencoesRes.data || []);
      } catch (error) {
        console.error("Erro ao carregar dados de resultados:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [slug]);

  const calcularConversao = (index: number) => {
    if (index === 0 || !funilData[index - 1] || funilData[index - 1].value === 0) return "100%";
    const conversao = (funilData[index].value / funilData[index - 1].value) * 100;
    return `${Math.round(conversao)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/40 p-6 rounded-2xl border border-slate-800 backdrop-blur-md">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Métricas & Insights</h2>
          <p className="text-slate-400 text-sm">
            Acompanhe o funil de conversão de leads e os principais assuntos buscados pelos clientes.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveMenuTab("funil")}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeMenuTab === "funil"
                ? "bg-[var(--color-brand-500)] text-white shadow-lg shadow-[var(--color-brand-500)]/20"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            📊 Funil de Vendas
          </button>
          <button
            onClick={() => setActiveMenuTab("insights")}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeMenuTab === "insights"
                ? "bg-[var(--color-brand-500)] text-white shadow-lg shadow-[var(--color-brand-500)]/20"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            💡 Insights da IA
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--color-brand-500)]"></div>
        </div>
      ) : activeMenuTab === "funil" ? (
        /* FUNIL DE VENDAS VIEW */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chart */}
          <div className="glass-panel p-6 h-[380px] flex flex-col justify-between">
            <h3 className="text-lg font-semibold text-white mb-2">Visualização do Funil</h3>
            <div className="flex-1 w-full min-h-[240px]">
              {funilData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={funilData}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
                    <XAxis type="number" stroke="var(--color-foreground-muted)" fontSize={10} hide />
                    <YAxis 
                      dataKey="name" 
                      type="category" 
                      stroke="var(--color-foreground-muted)" 
                      fontSize={11}
                      width={120}
                      tick={{ fill: "white" }}
                    />
                    <Tooltip
                      cursor={{ fill: "rgba(255, 255, 255, 0.05)" }}
                      contentStyle={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)", borderRadius: "0.5rem", color: "white" }}
                    />
                    <Bar dataKey="value" barSize={24} radius={[0, 4, 4, 0]}>
                      {funilData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-[var(--color-foreground-muted)]">
                  Sem dados do funil cadastrados no momento.
                </div>
              )}
            </div>
          </div>

          {/* Tabela de Conversão */}
          <div className="glass-panel p-0 overflow-hidden h-[380px] flex flex-col border border-slate-800">
            <div className="p-4 border-b border-[var(--color-border)]">
              <h3 className="text-lg font-semibold text-white">Taxa de Conversão</h3>
            </div>
            <div className="p-0 overflow-y-auto flex-1">
              {funilData.length > 0 ? (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-[var(--color-surface-hover)]">
                      <th className="p-3 text-xs font-semibold text-[var(--color-foreground-muted)] uppercase tracking-wider">Estágio</th>
                      <th className="p-3 text-xs font-semibold text-[var(--color-foreground-muted)] uppercase tracking-wider">Leads</th>
                      <th className="p-3 text-xs font-semibold text-[var(--color-foreground-muted)] uppercase tracking-wider">Conversão</th>
                    </tr>
                  </thead>
                  <tbody>
                    {funilData.map((item, index) => (
                      <tr key={item.name} className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-hover)]/50 transition-colors">
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.fill }}></div>
                            <span className="font-medium text-white text-sm">{item.name}</span>
                          </div>
                        </td>
                        <td className="p-3 text-white text-base font-bold">{item.value}</td>
                        <td className="p-3">
                          {index < funilData.length - 1 ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-[var(--color-brand-500)]/10 text-[var(--color-brand-400)]">
                              {calcularConversao(index + 1)}
                            </span>
                          ) : (
                            <span className="text-[var(--color-foreground-muted)] text-xs">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="flex h-full items-center justify-center text-[var(--color-foreground-muted)] p-8">
                  Nenhum registro para calcular conversão.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* INSIGHTS DA IA VIEW */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gráfico de Intenções */}
          <div className="glass-panel p-6 h-[400px] flex flex-col">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-[var(--color-brand-500)]/10 text-[var(--color-brand-400)]">
                <BrainCircuit size={18} />
              </div>
              <h3 className="text-lg font-semibold text-white">Top Intenções (7 dias)</h3>
            </div>
            
            <div className="flex-1 w-full min-h-[220px]">
              {intencoesData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={intencoesData}
                      cx="50%"
                      cy="45%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {intencoesData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)", borderRadius: "0.5rem", color: "white" }}
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-[var(--color-foreground-muted)]">
                  Sem dados suficientes para gerar o gráfico.
                </div>
              )}
            </div>
          </div>

          {/* Detalhamento das Buscas */}
          <div className="glass-panel p-0 flex flex-col h-[400px] overflow-hidden border border-slate-800">
            <div className="p-4 border-b border-[var(--color-border)]">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-[var(--color-brand-500)]/10 text-[var(--color-brand-400)]">
                  <MessageSquareText size={18} />
                </div>
                <h3 className="text-lg font-semibold text-white">Detalhamento das Buscas</h3>
              </div>
            </div>
            
            <div className="p-4 space-y-3 overflow-y-auto flex-1">
              {intencoesData.length > 0 ? (
                intencoesData.map((item, index) => {
                  const total = intencoesData.reduce((acc, curr) => acc + curr.value, 0);
                  const percent = total > 0 ? Math.round((item.value / total) * 100) : 0;
                  
                  return (
                    <div key={item.name} className="bg-[var(--color-surface-hover)]/30 rounded-lg p-3 border border-[var(--color-border)]">
                      <div className="flex justify-between items-center mb-1.5">
                        <div className="flex items-center gap-2">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                          <span className="font-medium text-white text-sm">{item.name}</span>
                        </div>
                        <span className="text-xs text-[var(--color-foreground-muted)]">{item.value} msgs ({percent}%)</span>
                      </div>
                      <div className="w-full bg-[var(--color-surface)] rounded-full h-1.5">
                        <div 
                          className="h-1.5 rounded-full" 
                          style={{ width: `${percent}%`, backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-[var(--color-foreground-muted)] text-center py-8 text-sm">Nenhuma intenção detectada ainda.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
