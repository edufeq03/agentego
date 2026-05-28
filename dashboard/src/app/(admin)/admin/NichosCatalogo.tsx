"use client";

import { useState } from "react";
import { NICHOS_CATALOGO, NichoInfo } from "./nichos-data";
import { Eye, X, Copy, Check, Bot, Target, Layers } from "lucide-react";

const COR_MAP: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  blue:   { bg: "bg-blue-500/10",   border: "border-blue-500/30",   text: "text-blue-400",   badge: "bg-blue-500/20 text-blue-300 border-blue-500/30" },
  pink:   { bg: "bg-pink-500/10",   border: "border-pink-500/30",   text: "text-pink-400",   badge: "bg-pink-500/20 text-pink-300 border-pink-500/30" },
  orange: { bg: "bg-orange-500/10", border: "border-orange-500/30", text: "text-orange-400", badge: "bg-orange-500/20 text-orange-300 border-orange-500/30" },
  green:  { bg: "bg-green-500/10",  border: "border-green-500/30",  text: "text-green-400",  badge: "bg-green-500/20 text-green-300 border-green-500/30" },
  purple: { bg: "bg-purple-500/10", border: "border-purple-500/30", text: "text-purple-400", badge: "bg-purple-500/20 text-purple-300 border-purple-500/30" },
  slate:  { bg: "bg-slate-500/10",  border: "border-slate-500/30",  text: "text-slate-400",  badge: "bg-slate-500/20 text-slate-300 border-slate-500/30" },
};

function PromptModal({ nicho, onClose }: { nicho: NichoInfo; onClose: () => void }) {
  const [copied, setCopied] = useState(false);
  const cores = COR_MAP[nicho.cor] || COR_MAP.slate;

  function handleCopy() {
    navigator.clipboard.writeText(nicho.prompt_completo);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className={`p-6 border-b border-[var(--color-border)] flex items-center justify-between ${cores.bg}`}>
          <div className="flex items-center gap-3">
            <span className="text-3xl">{nicho.emoji}</span>
            <div>
              <h2 className="text-lg font-bold text-white">{nicho.nome_display}</h2>
              <p className={`text-sm ${cores.text}`}>{nicho.especialista} · {nicho.cargo_especialista}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${cores.badge} ${cores.border}`}
            >
              {copied ? <><Check size={12} /> Copiado!</> : <><Copy size={12} /> Copiar Prompt</>}
            </button>
            <button onClick={onClose} className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 block">Objetivo Principal</span>
            <p className={`text-sm font-semibold ${cores.text}`}>{nicho.objetivo_principal}</p>
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 block">Módulos Ativos</span>
            <div className="flex flex-wrap gap-2">
              {nicho.modulos.length === 0
                ? <span className="text-xs text-slate-500 italic">Sem módulos específicos</span>
                : nicho.modulos.map(m => (
                    <span key={m} className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase ${cores.badge} ${cores.border}`}>{m}</span>
                  ))
              }
            </div>
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 block">Prompt Completo do Especialista</span>
            <pre className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 text-xs text-slate-300 whitespace-pre-wrap leading-relaxed font-mono">
              {nicho.prompt_completo}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function NichosCatalogo() {
  const [selected, setSelected] = useState<NichoInfo | null>(null);

  return (
    <>
      <div className="space-y-6">
        {/* Header Info */}
        <div className="glass-panel p-5 flex items-start gap-4 border border-purple-500/20 bg-purple-500/5">
          <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 shrink-0 mt-0.5">
            <Bot size={20} />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">Especialistas por Nicho</h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Cada nicho possui um <strong className="text-purple-400">especialista associado</strong> no backend que define a personalidade, tom e objetivos do agente de IA.
              Ao criar uma nova empresa, o nicho do template selecionado ativa automaticamente o especialista correto.
              Higienização foi unificada com Beleza (mesmo fluxo de agendamento).
            </p>
          </div>
        </div>

        {/* Table */}
        <div className="glass-panel overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-[var(--color-surface)] border-b border-[var(--color-border)]">
                <th className="p-5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Nicho</th>
                <th className="p-5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Especialista</th>
                <th className="p-5 text-xs font-semibold text-slate-400 uppercase tracking-wider hidden md:table-cell">
                  <span className="flex items-center gap-1"><Target size={12} /> Objetivo do Fluxo</span>
                </th>
                <th className="p-5 text-xs font-semibold text-slate-400 uppercase tracking-wider hidden lg:table-cell">
                  <span className="flex items-center gap-1"><Layers size={12} /> Módulos</span>
                </th>
                <th className="p-5 text-xs font-semibold text-slate-400 uppercase tracking-wider hidden lg:table-cell">Prompt (Resumo)</th>
                <th className="p-5 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {NICHOS_CATALOGO.map((n) => {
                const cores = COR_MAP[n.cor] || COR_MAP.slate;
                return (
                  <tr key={n.id} className="hover:bg-white/[0.02] transition-colors group">
                    {/* Nicho */}
                    <td className="p-5">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl ${cores.bg} border ${cores.border} flex items-center justify-center text-xl shrink-0`}>
                          {n.emoji}
                        </div>
                        <div>
                          <span className="font-bold text-white block">{n.nome_display}</span>
                          <span className={`text-[10px] font-mono font-semibold ${cores.text}`}>{n.nicho}</span>
                        </div>
                      </div>
                    </td>

                    {/* Especialista */}
                    <td className="p-5">
                      <div className="flex flex-col">
                        <span className="font-semibold text-white text-sm">{n.especialista}</span>
                        <span className="text-[11px] text-slate-500 mt-0.5">{n.cargo_especialista}</span>
                      </div>
                    </td>

                    {/* Objetivo */}
                    <td className="p-5 hidden md:table-cell">
                      <span className={`text-xs px-2.5 py-1 rounded-full border font-semibold ${cores.badge} ${cores.border}`}>
                        {n.objetivo_principal}
                      </span>
                    </td>

                    {/* Módulos */}
                    <td className="p-5 hidden lg:table-cell">
                      <div className="flex flex-wrap gap-1">
                        {n.modulos.length === 0
                          ? <span className="text-xs text-slate-600 italic">—</span>
                          : n.modulos.map(m => (
                              <span key={m} className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400 uppercase font-semibold">
                                {m}
                              </span>
                            ))
                        }
                      </div>
                    </td>

                    {/* Prompt resumo */}
                    <td className="p-5 hidden lg:table-cell max-w-xs">
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{n.prompt_resumo}</p>
                    </td>

                    {/* Ação */}
                    <td className="p-5 text-right">
                      <button
                        onClick={() => setSelected(n)}
                        className={`flex items-center gap-1.5 ml-auto px-3 py-2 rounded-lg text-xs font-semibold border transition-all opacity-60 group-hover:opacity-100 ${cores.bg} ${cores.text} ${cores.border} hover:opacity-100`}
                      >
                        <Eye size={13} /> Ver Prompt
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {selected && <PromptModal nicho={selected} onClose={() => setSelected(null)} />}
    </>
  );
}
