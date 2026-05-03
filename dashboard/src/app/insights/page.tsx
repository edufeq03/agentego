"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { BrainCircuit, MessageSquareText } from "lucide-react";

interface IntencaoData {
  name: string;
  value: number;
}

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f97316', '#10b981'];

export default function Insights() {
  const [data, setData] = useState<IntencaoData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await api.get("/dashboard/intencoes");
        setData(response.data);
      } catch (error) {
        console.error("Erro ao buscar dados de intenções:", error);
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

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Insights da IA</h2>
        <p className="text-[var(--color-foreground-muted)] mt-1">
          Descubra o que os seus clientes mais buscam quando conversam com a Rosana.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Gráfico de Intenções */}
        <div className="glass-panel p-6 h-[450px] flex flex-col">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-[var(--color-brand-500)]/10 text-[var(--color-brand-400)]">
              <BrainCircuit size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white">Top Intenções (Últimos 7 dias)</h3>
          </div>
          
          <div className="flex-1 w-full">
            {data.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    innerRadius={80}
                    outerRadius={120}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '0.5rem', color: 'white' }}
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

        {/* Tabela de Intenções */}
        <div className="glass-panel p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-[var(--color-brand-500)]/10 text-[var(--color-brand-400)]">
              <MessageSquareText size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white">Detalhamento das Buscas</h3>
          </div>
          
          <div className="space-y-4">
            {data.length > 0 ? (
              data.map((item, index) => {
                const total = data.reduce((acc, curr) => acc + curr.value, 0);
                const percent = Math.round((item.value / total) * 100);
                
                return (
                  <div key={item.name} className="bg-[var(--color-surface-hover)]/30 rounded-lg p-4 border border-[var(--color-border)]">
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                        <span className="font-medium text-white">{item.name}</span>
                      </div>
                      <span className="text-sm text-[var(--color-foreground-muted)]">{item.value} msgs ({percent}%)</span>
                    </div>
                    <div className="w-full bg-[var(--color-surface)] rounded-full h-2">
                      <div 
                        className="h-2 rounded-full" 
                        style={{ width: `${percent}%`, backgroundColor: COLORS[index % COLORS.length] }}
                      ></div>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-[var(--color-foreground-muted)] text-center py-8">Nenhuma intenção detectada ainda.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
