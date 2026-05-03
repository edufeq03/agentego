"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Filter, Lightbulb, MessageCircle, Settings, Dumbbell } from "lucide-react";

const navigation = [
  { name: "Visão Geral", href: "/", icon: LayoutDashboard },
  { name: "Funil de Vendas", href: "/funil", icon: Filter },
  { name: "Insights", href: "/insights", icon: Lightbulb },
  { name: "Conversas", href: "/conversas", icon: MessageCircle },
  { name: "Configurações", href: "/configuracoes", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col w-64 bg-[var(--color-surface)] border-r border-[var(--color-border)] min-h-screen">
      <div className="flex items-center gap-3 h-16 px-6 border-b border-[var(--color-border)]">
        <div className="bg-[var(--color-brand-500)] p-2 rounded-lg text-white">
          <Dumbbell size={20} />
        </div>
        <span className="text-xl font-bold text-white tracking-tight">AtendIA</span>
      </div>

      <div className="flex-1 py-6 flex flex-col gap-1 px-3">
        <div className="text-xs font-semibold text-[var(--color-foreground-muted)] uppercase tracking-wider mb-2 px-3">
          Dashboard
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-colors ${
                isActive
                  ? "bg-[var(--color-brand-500)] text-white"
                  : "text-[var(--color-foreground-muted)] hover:text-white hover:bg-[var(--color-surface-hover)]"
              }`}
            >
              <Icon size={18} className={isActive ? "text-white" : "text-[var(--color-brand-400)]"} />
              {item.name}
            </Link>
          );
        })}
      </div>

      <div className="p-4 border-t border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-[var(--color-brand-600)] to-[var(--color-brand-400)] flex items-center justify-center text-white font-bold">
            PF
          </div>
          <div>
            <p className="text-sm font-medium text-white">Prime Fit</p>
            <p className="text-xs text-[var(--color-foreground-muted)]">Plano Pro</p>
          </div>
        </div>
      </div>
    </div>
  );
}
