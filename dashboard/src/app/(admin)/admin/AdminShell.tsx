"use client";
import { useState } from "react";
import {
  Users, ShieldCheck, LayoutGrid, BarChart3,
  Menu, X, Smartphone, ChevronRight
} from "lucide-react";

const NAV = [
  { id: "empresas",  label: "Empresas",            icon: Users,        color: "text-blue-400" },
  { id: "templates", label: "Templates de Nicho",   icon: ShieldCheck,  color: "text-purple-400" },
  { id: "nichos",    label: "Catálogo de Nichos",   icon: LayoutGrid,   color: "text-pink-400" },
];

interface Props {
  activeTab: "empresas" | "templates" | "nichos";
  setActiveTab: (t: "empresas" | "templates" | "nichos") => void;
  empresasCount: number;
  templatesCount: number;
  children: React.ReactNode;
  kpis: { empresas: number; ativas: number; mrr: number; custo: number };
}

export default function AdminShell({ activeTab, setActiveTab, empresasCount, templatesCount, children, kpis }: Props) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navItems = NAV.map(n => ({
    ...n,
    badge: n.id === "empresas" ? empresasCount : n.id === "templates" ? templatesCount : undefined
  }));

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* ── Sidebar ── */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 flex flex-col bg-[#161b27] border-r border-white/[0.06] transform transition-transform duration-300 md:relative md:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-white/[0.06] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Smartphone size={16} className="text-white" />
            </div>
            <div>
              <p className="font-bold text-sm text-white leading-tight">AgenteGo</p>
              <p className="text-[10px] text-slate-500 leading-tight">Central do Franqueador</p>
            </div>
          </div>
          <button className="md:hidden text-slate-400 hover:text-white" onClick={() => setSidebarOpen(false)}>
            <X size={18} />
          </button>
        </div>

        {/* KPI mini cards */}
        <div className="p-4 border-b border-white/[0.06] space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-500">Empresas Ativas</span>
            <span className="font-bold text-green-400">{kpis.ativas} / {kpis.empresas}</span>
          </div>
          <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all" style={{ width: kpis.empresas ? `${(kpis.ativas / kpis.empresas) * 100}%` : "0%" }} />
          </div>
          <div className="flex justify-between text-xs pt-1">
            <span className="text-slate-500">MRR</span>
            <span className="font-bold text-white">R$ {kpis.mrr.toLocaleString("pt-BR")}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-500">Custo IA</span>
            <span className="font-bold text-yellow-400">${kpis.custo.toFixed(2)}</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <p className="px-3 pt-2 pb-1 text-[10px] font-bold uppercase tracking-widest text-slate-600">Menu</p>
          {navItems.map(item => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => { setActiveTab(item.id as any); setSidebarOpen(false); }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${active ? "bg-white/10 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"}`}
              >
                <div className="flex items-center gap-3">
                  <Icon size={17} className={active ? item.color : "text-slate-600 group-hover:text-slate-400"} />
                  {item.label}
                </div>
                <div className="flex items-center gap-2">
                  {item.badge !== undefined && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${active ? "bg-white/20 text-white" : "bg-white/5 text-slate-500"}`}>
                      {item.badge}
                    </span>
                  )}
                  <ChevronRight size={13} className={`${active ? "opacity-100 " + item.color : "opacity-0"} transition-opacity`} />
                </div>
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-white/[0.06] shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs font-bold">A</div>
            <div>
              <p className="text-xs font-semibold text-white">Admin Master</p>
              <p className="text-[10px] text-slate-500">Central AgenteGo</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 shrink-0 border-b border-white/[0.06] bg-[#0f1117]/80 backdrop-blur-md flex items-center px-5 gap-4 z-10">
          <button className="md:hidden text-slate-400 hover:text-white" onClick={() => setSidebarOpen(true)}>
            <Menu size={22} />
          </button>
          <div className="flex-1">
            <h1 className="text-base font-bold text-white">
              {activeTab === "empresas" ? "Gestão de Empresas" : activeTab === "templates" ? "Templates de Nicho" : "Catálogo de Nichos & Especialistas"}
            </h1>
            <p className="text-[11px] text-slate-500 hidden md:block">
              {activeTab === "empresas" ? "Gerencie clientes, planos e acessos" : activeTab === "templates" ? "Configure os templates de IA por segmento" : "Visualize nichos, especialistas e prompts"}
            </p>
          </div>
          {/* Breadcrumb */}
          <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-500">
            <span>Admin</span>
            <ChevronRight size={12} />
            <span className="text-white font-medium capitalize">{activeTab === "nichos" ? "Catálogo" : activeTab}</span>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-5 md:p-8 bg-[#0f1117]">
          {children}
        </main>
      </div>
    </div>
  );
}
