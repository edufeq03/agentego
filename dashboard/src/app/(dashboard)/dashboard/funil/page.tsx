"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface FunilData {
  name: string;
  value: number;
  fill: string;
}

export default function Funil() {
  const [data, setData] = useState<FunilData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await api.get("/dashboard/funil");
        setData(response.data);
      } catch (error) {
        console.error("Erro ao buscar dados do funil:", error);
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

  const calcularConversao = (index: number) => {
    if (index === 0 || data[index - 1].value === 0) return "100%";
    const conversao = (data[index].value / data[index - 1].value) * 100;
    return `${Math.round(conversao)}%`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Funil de Vendas</h2>
          <p className="text-[var(--color-foreground-muted)] mt-1">
            Acompanhe a evolução dos leads desde o primeiro contato até o agendamento da visita.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart */}
        <div className="glass-panel p-4 h-[400px]">
          <h3 className="text-lg font-semibold text-white mb-4">Visualização do Funil</h3>
          <ResponsiveContainer width="100%" height="80%">
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis type="number" stroke="var(--color-foreground-muted)" fontSize={12} />
              <YAxis 
                dataKey="name" 
                type="category" 
                stroke="var(--color-foreground-muted)" 
                fontSize={12}
                width={100}
              />
              <Tooltip
                cursor={{ fill: "rgba(255, 255, 255, 0.05)" }}
                contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '0.5rem', color: 'white' }}
              />
              <Bar dataKey="value" barSize={30} radius={[0, 4, 4, 0]}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Tabela de Conversão */}
        <div className="glass-panel p-0 overflow-hidden h-[400px]">
          <div className="p-4 border-b border-[var(--color-border)]">
            <h3 className="text-lg font-semibold text-white">Taxa de Conversão</h3>
          </div>
          <div className="p-0 overflow-y-auto h-[calc(400px-60px)]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--color-surface-hover)]">
                  <th className="p-3 text-xs font-semibold text-[var(--color-foreground-muted)] uppercase tracking-wider">Estágio</th>
                  <th className="p-3 text-xs font-semibold text-[var(--color-foreground-muted)] uppercase tracking-wider">Leads</th>
                  <th className="p-3 text-xs font-semibold text-[var(--color-foreground-muted)] uppercase tracking-wider">Conversão</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item, index) => (
                  <tr key={item.name} className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-hover)]/50 transition-colors">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.fill }}></div>
                        <span className="font-medium text-white text-sm">{item.name}</span>
                      </div>
                    </td>
                    <td className="p-3 text-white text-base font-bold">{item.value}</td>
                    <td className="p-3">
                      {index < data.length - 1 ? (
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
          </div>
        </div>
      </div>
    </div>
  );
}
