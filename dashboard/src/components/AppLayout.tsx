"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, usePathname, useSearchParams } from "next/navigation";
import { LayoutDashboard, Filter, Lightbulb, MessageCircle, Settings, Dumbbell, Menu, X, LogOut, Smartphone, Mic, Users, Megaphone, Briefcase, CalendarCheck, FileText, Share2, Sliders, Zap, Utensils, ClipboardList, TrendingUp } from "lucide-react";
import api from "@/lib/api";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const params = useParams();
  const slug = params?.slug as string;
  const searchParams = useSearchParams();
  const impersonateToken = searchParams.get('_imp');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [temConversaPausada, setTemConversaPausada] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [nicho, setNicho] = useState<string | null>(null);
  const [modulosAtivos, setModulosAtivos] = useState<string[]>([]);
  const [empresa, setEmpresa] = useState<{ nome: string; plano: string } | null>(null);

  const navigation = [
    { name: "Visão Geral", href: `/${slug}`, icon: LayoutDashboard },
    { name: "Conectar WhatsApp", href: `/${slug}/whatsapp`, icon: Smartphone },
    
    // Módulo Agenda
    ...(modulosAtivos.includes('agenda') || nicho === 'agenda' ? [
      { name: "Visualizar Agenda", href: `/${slug}/agenda`, icon: CalendarCheck },
      { name: "Serviços", href: `/${slug}/agenda/servicos`, icon: ClipboardList },
      { name: "Configurar Agenda", href: `/${slug}/agenda/disponibilidade`, icon: Sliders },
    ] : []),
    
    // Nicho Academia
    ...(nicho === 'academia' ? [
      { name: "Gestão de Alunos", href: `/${slug}/alunos`, icon: Dumbbell },
      { name: "Comunicados", href: `/${slug}/comunicados`, icon: Megaphone },
    ] : []),

    // Nicho Corretora
    ...(nicho === 'corretora' ? [
      { name: "Gestão de Leads", href: `/${slug}/alunos`, icon: Users },
      { name: "Comunicados", href: `/${slug}/comunicados`, icon: Megaphone },
    ] : []),

    // Nicho Lanchonete
    ...(nicho === 'lanchonete' ? [
      { name: "Cardápio", href: `/${slug}/cardapio`, icon: Utensils },
      { name: "Painel de Pedidos", href: `/${slug}/pedidos`, icon: ClipboardList },
      { name: "Comunicados", href: `/${slug}/comunicados`, icon: Megaphone },
    ] : []),

    // Nicho Contabilidade
    ...(nicho === 'contabilidade' ? [
      { name: "Empresas Clientes", href: `/${slug}/clientes`, icon: Briefcase },
      { name: "Obrigações Fiscais", href: `/${slug}/obrigacoes`, icon: CalendarCheck },
      { name: "Base Legal", href: `/${slug}/documentos`, icon: FileText },
    ] : []),

    { name: "Métricas & Insights", href: `/${slug}/funil`, icon: TrendingUp },
    { name: "Marketing", href: `/${slug}/marketing`, icon: Share2 },
    { name: "Triagem da IA", href: `/${slug}/triagem`, icon: Sliders },
    { name: "Disparos da IA", href: `/${slug}/disparos`, icon: Zap },
    { name: "Conversas", href: `/${slug}/conversas`, icon: MessageCircle },
    { name: "Configurações", href: `/${slug}/configuracoes`, icon: Settings },
    { name: "Voz e Fala", href: `/${slug}/configuracoes-fala`, icon: Mic },
  ];

  // Fecha o menu ao mudar de rota no mobile
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  // Checa autenticação e valida Slug
  useEffect(() => {
    // Se houver um token de impersonation na URL, prioriza ele
    if (impersonateToken && slug) {
      localStorage.setItem('agentego_token', impersonateToken);
      localStorage.setItem('agentego_slug', slug);
      // Limpa a URL imediatamente sem reload
      window.history.replaceState({}, '', `/${slug}`);
    }

    const token = localStorage.getItem('agentego_token');
    const storedSlug = localStorage.getItem('agentego_slug');
    
    if (!token) {
      window.location.href = '/login';
    } else if (slug && storedSlug && slug !== storedSlug) {
      // Se o usuário tentar acessar outro slug, manda pro dele
      window.location.href = `/${storedSlug}`;
    } else {
      setIsAuthenticated(true);
    }
  }, [pathname, slug, impersonateToken]);

  // Polling para checar se há conversas pausadas
  useEffect(() => {
    if (!isAuthenticated) return;

    async function checkPausadas() {
      try {
        const response = await api.get("dashboard/conversas");
        const conversas = response.data;
        const temPausada = conversas.some((c: any) => c.transbordo === 'pausado');
        setTemConversaPausada(temPausada);
      } catch (error) {
        console.error("Erro ao checar notificações:", error);
      }
    }

    checkPausadas();
    const interval = setInterval(checkPausadas, 10000); // Check a cada 10s
    return () => clearInterval(interval);
  }, [isAuthenticated, pathname]);

  // Busca o nicho da empresa
  useEffect(() => {
    if (!isAuthenticated) return;
    async function fetchConfig() {
      try {
        const response = await api.get('dashboard/config');
        setNicho(response.data.nicho || 'generico');
        setModulosAtivos(response.data.config?.modulos_ativos || []);
        setEmpresa({
          nome: response.data.config?.nome_empresa || response.data.nome || 'Minha Empresa',
          plano: response.data.plano?.toUpperCase() || 'PRO'
        });
      } catch (error) {
        console.error("Erro ao carregar nicho:", error);
      }
    }
    fetchConfig();
  }, [isAuthenticated]);

  function handleLogout() {
    localStorage.removeItem('agentego_token');
    localStorage.removeItem('agentego_slug');
    window.location.href = '/login';
  }

  if (!isAuthenticated) {
    return <div className="h-screen bg-[var(--color-background)] flex items-center justify-center text-white">Carregando...</div>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-background)]">
      {/* Overlay Mobile */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-sm"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div 
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-[var(--color-surface)] border-r border-[var(--color-border)] transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between h-16 px-6 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-3">
            <div className="bg-[var(--color-brand-500)] p-2 rounded-lg text-white">
              <Smartphone size={20} />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">AgenteGo</span>
          </div>
          <button 
            className="md:hidden text-[var(--color-foreground-muted)] hover:text-white"
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <X size={24} />
          </button>
        </div>

        <div className="flex flex-col h-[calc(100vh-4rem)]">
          <div className="flex-1 py-6 flex flex-col gap-1 px-3 overflow-y-auto">
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
                  className={`flex items-center justify-between px-3 py-2.5 rounded-lg font-medium transition-colors ${
                    isActive
                      ? "bg-[var(--color-brand-500)] text-white"
                      : "text-[var(--color-foreground-muted)] hover:text-white hover:bg-[var(--color-surface-hover)]"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon size={18} className={isActive ? "text-white" : "text-[var(--color-brand-400)]"} />
                    {item.name}
                  </div>
                  {/* Badge de Notificação */}
                  {item.name === "Conversas" && temConversaPausada && (
                    <span className="flex h-2.5 w-2.5 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
                    </span>
                  )}
                </Link>
              );
            })}
          </div>

          {/* Sidebar Footer (Only Mobile) */}
          <div className="p-4 border-t border-[var(--color-border)] md:hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 shrink-0 rounded-full bg-gradient-to-tr from-[var(--color-brand-600)] to-[var(--color-brand-400)] flex items-center justify-center text-white font-bold">
                  {empresa?.nome.charAt(0).toUpperCase() || 'E'}
                </div>
                <div className="truncate">
                  <p className="text-sm font-medium text-white truncate">{empresa?.nome || 'Carregando...'}</p>
                  <p className="text-xs text-[var(--color-foreground-muted)] truncate">Plano {empresa?.plano || '...'}</p>
                </div>
              </div>
              <button 
                onClick={handleLogout}
                className="p-2 text-[var(--color-foreground-muted)] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                title="Sair"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header/Topbar */}
        <header className="h-16 shrink-0 border-b border-[var(--color-border)] bg-[var(--color-background)]/80 backdrop-blur-md flex items-center px-4 md:px-8 z-10 gap-4">
          <button 
            className="md:hidden text-[var(--color-foreground-muted)] hover:text-white"
            onClick={() => setIsMobileMenuOpen(true)}
          >
            <Menu size={24} />
          </button>
          <div className="flex-1 flex items-center justify-between">
            <h1 className="text-lg md:text-xl font-semibold tracking-tight text-white truncate">Dashboard do Agente</h1>
            
            {/* Desktop Profile Info */}
            <div className="hidden md:flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium text-white">{empresa?.nome || '...'}</p>
                <p className="text-[10px] text-[var(--color-foreground-muted)] uppercase tracking-wider">Plano {empresa?.plano || '...'}</p>
              </div>
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-[var(--color-brand-600)] to-[var(--color-brand-400)] flex items-center justify-center text-white font-bold shadow-lg shadow-[var(--color-brand-500)]/20">
                {empresa?.nome.charAt(0).toUpperCase() || 'E'}
              </div>
              <div className="h-8 w-px bg-[var(--color-border)] mx-2" />
              <button 
                onClick={handleLogout}
                className="p-2 text-[var(--color-foreground-muted)] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                title="Sair"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </header>
        
        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 pb-24 bg-[var(--color-background)]">
          <div className="max-w-6xl mx-auto h-full">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
