"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Save, CheckCircle2 } from "lucide-react";

interface ConfigData {
  nome_agente: string;
  nome_empresa: string;
  planos: { basico: number; vip: number };
  horarios: { semana: string; sabado: string };
  endereco: string;
  pagamentos: string[];
  aulas_vip: string[];
}

export default function Configuracoes() {
  const [config, setConfig] = useState<ConfigData>({
    nome_agente: "",
    nome_empresa: "",
    planos: { basico: 0, vip: 0 },
    horarios: { semana: "", sabado: "" },
    endereco: "",
    pagamentos: [],
    aulas_vip: []
  });
  
  const [pagamentosStr, setPagamentosStr] = useState("");
  const [aulasStr, setAulasStr] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await api.get("/dashboard/config");
        const data = response.data;
        if (data && Object.keys(data).length > 0) {
          setConfig(data);
          setPagamentosStr(data.pagamentos ? data.pagamentos.join(", ") : "");
          setAulasStr(data.aulas_vip ? data.aulas_vip.join(", ") : "");
        }
      } catch (error) {
        console.error("Erro ao buscar configurações:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    
    try {
      const configToSave = {
        ...config,
        pagamentos: pagamentosStr.split(",").map(s => s.trim()).filter(s => s),
        aulas_vip: aulasStr.split(",").map(s => s.trim()).filter(s => s)
      };
      
      await api.put("/dashboard/config", configToSave);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Erro ao salvar:", error);
      alert("Erro ao salvar configurações.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--color-brand-500)]"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-10">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Configurações do Agente</h2>
          <p className="text-[var(--color-foreground-muted)] mt-1">
            Ajuste a personalidade do bot, preços, horários e serviços oferecidos.
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Identidade */}
        <div className="glass-panel p-6">
          <h3 className="text-lg font-semibold text-white mb-4 border-b border-[var(--color-border)] pb-2">Identidade</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-foreground-muted)]">Nome da Empresa</label>
              <input 
                type="text" 
                value={config.nome_empresa}
                onChange={e => setConfig({...config, nome_empresa: e.target.value})}
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-foreground-muted)]">Nome do Agente (Robô)</label>
              <input 
                type="text" 
                value={config.nome_agente}
                onChange={e => setConfig({...config, nome_agente: e.target.value})}
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                required
              />
            </div>
          </div>
        </div>

        {/* Planos */}
        <div className="glass-panel p-6">
          <h3 className="text-lg font-semibold text-white mb-4 border-b border-[var(--color-border)] pb-2">Planos e Preços (R$)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-foreground-muted)]">Plano Básico (Mensalidade)</label>
              <input 
                type="number" 
                value={config.planos.basico}
                onChange={e => setConfig({...config, planos: {...config.planos, basico: Number(e.target.value)}})}
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-foreground-muted)]">Plano VIP (Mensalidade)</label>
              <input 
                type="number" 
                value={config.planos.vip}
                onChange={e => setConfig({...config, planos: {...config.planos, vip: Number(e.target.value)}})}
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                required
              />
            </div>
          </div>
        </div>

        {/* Horários */}
        <div className="glass-panel p-6">
          <h3 className="text-lg font-semibold text-white mb-4 border-b border-[var(--color-border)] pb-2">Horários e Endereço</h3>
          <div className="grid grid-cols-1 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-foreground-muted)]">Endereço Completo</label>
              <input 
                type="text" 
                value={config.endereco}
                onChange={e => setConfig({...config, endereco: e.target.value})}
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                required
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--color-foreground-muted)]">Segunda a Sexta (Ex: 08:00 as 22:00)</label>
                <input 
                  type="text" 
                  value={config.horarios.semana}
                  onChange={e => setConfig({...config, horarios: {...config.horarios, semana: e.target.value}})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--color-foreground-muted)]">Sábados (Ex: 09:00 as 13:00)</label>
                <input 
                  type="text" 
                  value={config.horarios.sabado}
                  onChange={e => setConfig({...config, horarios: {...config.horarios, sabado: e.target.value}})}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        {/* Serviços */}
        <div className="glass-panel p-6">
          <h3 className="text-lg font-semibold text-white mb-4 border-b border-[var(--color-border)] pb-2">Serviços e Pagamentos</h3>
          <div className="grid grid-cols-1 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-foreground-muted)]">Aulas VIP (separadas por vírgula)</label>
              <textarea 
                value={aulasStr}
                onChange={e => setAulasStr(e.target.value)}
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)] h-20 resize-none"
                placeholder="Ex: Spinning, Zumba, Funcional"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-foreground-muted)]">Formas de Pagamento (separadas por vírgula)</label>
              <input 
                type="text" 
                value={pagamentosStr}
                onChange={e => setPagamentosStr(e.target.value)}
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 px-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                placeholder="Ex: Pix, Cartão de Crédito, Dinheiro, Gympass"
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-4">
          <button 
            type="submit" 
            disabled={saving}
            className="flex items-center gap-2 bg-gradient-to-r from-[var(--color-brand-600)] to-[var(--color-brand-400)] hover:from-[var(--color-brand-500)] hover:to-[var(--color-brand-300)] text-white px-8 py-3 rounded-xl font-medium transition-all shadow-lg shadow-[var(--color-brand-500)]/20 disabled:opacity-50"
          >
            {saving ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : saved ? (
              <><CheckCircle2 size={20} /> Salvo com Sucesso!</>
            ) : (
              <><Save size={20} /> Salvar Configurações</>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
