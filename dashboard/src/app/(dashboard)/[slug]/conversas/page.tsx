"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import api from "@/lib/api";
import { MessageCircle, Bot, User, Power, Search, Pause, AlertTriangle, ChevronLeft, Sliders, Target, PanelLeftClose, PanelLeftOpen } from "lucide-react";

interface ConversaData {
  id: string;
  telefone: string;
  nome: string;
  stage: string;
  ultima_mensagem: string;
  timestamp: string;
  transbordo: string | null;
  dados_customizados?: Record<string, any> | null;
}

interface MensagemData {
  tipo: string;
  mensagem: string;
  timestamp: string;
}

export default function Conversas() {
  const [conversas, setConversas] = useState<ConversaData[]>([]);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState("");
  
  const [conversaAtiva, setConversaAtiva] = useState<ConversaData | null>(null);
  const [mensagens, setMensagens] = useState<MensagemData[]>([]);
  const [loadingMensagens, setLoadingMensagens] = useState(false);
  const [mensagemInput, setMensagemInput] = useState("");
  const [enviandoMensagem, setEnviandoMensagem] = useState(false);
  const [convertendo, setConvertendo] = useState(false);
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<'mensagens' | 'perfil' | 'triagem'>('mensagens');
  
  const router = useRouter();
  const params = useParams();

  async function converterLead() {
    if (!conversaAtiva) return;
    setConvertendo(true);
    try {
      await api.post(`/crm/deals/from-lead/${conversaAtiva.id}`);
      alert("Sucesso! O lead foi convertido em Oportunidade no CRM.");
      router.push(`/${params?.slug || ''}/crm`);
    } catch (error: any) {
      console.error(error);
      alert(error.response?.data?.detail || "Erro ao converter lead");
    } finally {
      setConvertendo(false);
    }
  }
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);
  const conversaAtivaRef = useRef(conversaAtiva);

  const scrollToBottom = (force = false) => {
    if (force || autoScrollEnabled) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
    setAutoScrollEnabled(isAtBottom);
  };

  useEffect(() => {
    if (activeTab === 'mensagens') {
      scrollToBottom();
    }
  }, [mensagens, activeTab]);

  useEffect(() => {
    conversaAtivaRef.current = conversaAtiva;
  }, [conversaAtiva]);

  // Busca inicial (com spinner)
  async function carregarConversasInicial() {
    try {
      const response = await api.get("dashboard/conversas");
      setConversas(response.data);
      
      const searchParams = new URLSearchParams(window.location.search);
      const telefoneQuery = searchParams.get("telefone");
      if (telefoneQuery) {
        const target = response.data.find((c: any) => c.telefone === telefoneQuery);
        if (target) {
          abrirConversa(target);
        }
      }
    } catch (error) {
      console.error("Erro ao buscar conversas:", error);
    } finally {
      setLoading(false);
    }
  }

  // Busca de atualização (sem spinner)
  async function atualizarConversas() {
    try {
      const response = await api.get("dashboard/conversas");
      setConversas(response.data);
    } catch (error) {
      console.error("Erro ao atualizar conversas:", error);
    }
  }

  async function atualizarMensagens(telefone: string) {
    try {
      const response = await api.get(`/dashboard/conversas/${telefone}`);
      setMensagens(response.data);
    } catch (error) {
      console.error("Erro ao atualizar mensagens:", error);
    }
  }

  // Polling em tempo real
  useEffect(() => {
    carregarConversasInicial();

    const intervalId = setInterval(() => {
      atualizarConversas();
      if (conversaAtivaRef.current) {
        atualizarMensagens(conversaAtivaRef.current.telefone);
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, []);

  async function abrirConversa(conversa: ConversaData) {
    setConversaAtiva(conversa);
    setActiveTab('mensagens');
    if (window.innerWidth < 768) setIsSidebarOpen(false);
    
    setLoadingMensagens(true);
    try {
      const response = await api.get(`/dashboard/conversas/${conversa.telefone}`);
      setMensagens(response.data);
    } catch (error) {
      console.error("Erro ao carregar mensagens:", error);
    } finally {
      setLoadingMensagens(false);
      setTimeout(() => scrollToBottom(true), 100);
      setAutoScrollEnabled(true);
    }
  }

  function fecharConversaMobile() {
    setConversaAtiva(null);
    setIsSidebarOpen(true);
  }

  async function pausarRobo() {
    if (!conversaAtiva) return;
    try {
      await api.post(`/dashboard/conversas/${conversaAtiva.telefone}/pausar`);
      setConversaAtiva({ ...conversaAtiva, transbordo: 'pausado' });
      setConversas(conversas.map(c => c.id === conversaAtiva.id ? { ...c, transbordo: 'pausado' } : c));
    } catch (error) {
      console.error("Erro ao pausar robô:", error);
      alert("Erro ao pausar robô.");
    }
  }

  async function handleSendMessage() {
    if (!conversaAtiva || !mensagemInput.trim()) return;
    
    setEnviandoMensagem(true);
    try {
      await api.post(`/dashboard/conversas/${conversaAtiva.telefone}/enviar`, {
        mensagem: mensagemInput
      });
      
      const novaMsg: MensagemData = {
        tipo: 'agente',
        mensagem: mensagemInput,
        timestamp: new Date().toISOString()
      };
      
      setMensagens([...mensagens, novaMsg]);
      setMensagemInput("");
    } catch (error) {
      console.error("Erro ao enviar mensagem:", error);
      alert("Erro ao enviar mensagem. Verifique a conexão do WhatsApp.");
    } finally {
      setEnviandoMensagem(false);
    }
  }

  async function reativarRobo() {
    if (!conversaAtiva) return;
    try {
      await api.post(`/dashboard/conversas/${conversaAtiva.telefone}/reativar`);
      setConversaAtiva({ ...conversaAtiva, transbordo: null });
      setConversas(conversas.map(c => c.id === conversaAtiva.id ? { ...c, transbordo: null } : c));
    } catch (error) {
      console.error("Erro ao reativar robô:", error);
      alert("Erro ao reativar robô.");
    }
  }

  const conversasFiltradas = conversas.filter(c => 
    c.telefone.includes(busca) || 
    c.nome.toLowerCase().includes(busca.toLowerCase()) ||
    c.ultima_mensagem.toLowerCase().includes(busca.toLowerCase())
  );

  const conversaAtivaAtualizada = conversas.find(c => c.id === conversaAtiva?.id) || conversaAtiva;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="hidden md:block">
        <h2 className="text-2xl font-bold text-white tracking-tight">Caixa de Entrada</h2>
        <p className="text-[var(--color-foreground-muted)] mt-1 mb-6">
          Visualize o histórico de atendimento e assuma o controle quando necessário.
        </p>
      </div>

      <div className="flex-1 flex gap-0 md:gap-6 overflow-hidden">
        {/* Lista de Conversas (Esquerda) */}
        <div className={`w-full md:w-1/3 flex flex-col glass-panel overflow-hidden transition-all duration-300 ${isSidebarOpen ? 'flex' : 'hidden'} ${conversaAtiva && window.innerWidth < 768 ? 'hidden' : ''}`}>
          <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-between">
            <div className="relative flex-1 mr-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" size={18} />
              <input 
                type="text" 
                placeholder="Buscar conversa..." 
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 pl-10 pr-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />
            </div>
            <button 
              onClick={() => setIsSidebarOpen(false)}
              className="hidden md:flex p-2 text-[var(--color-foreground-muted)] hover:text-white bg-[var(--color-surface-hover)] rounded-lg transition-colors"
              title="Recolher lista"
            >
              <PanelLeftClose size={20} />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center text-[var(--color-foreground-muted)]">Carregando conversas...</div>
            ) : conversasFiltradas.length > 0 ? (
              conversasFiltradas.map((conversa) => (
                <div 
                  key={conversa.id}
                  onClick={() => abrirConversa(conversa)}
                  className={`p-4 border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-hover)] transition-colors ${conversaAtiva?.id === conversa.id ? 'bg-[var(--color-surface-hover)]/80 md:border-l-4 md:border-l-[var(--color-brand-500)]' : 'md:border-l-4 md:border-l-transparent'}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-semibold text-white truncate">{conversa.nome}</span>
                    <span className="text-xs text-[var(--color-foreground-muted)] whitespace-nowrap ml-2">
                      {new Date(conversa.timestamp).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'})}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--color-foreground-muted)] truncate">{conversa.ultima_mensagem}</p>
                  
                  <div className="flex gap-2 mt-2">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-[var(--color-foreground-muted)] uppercase tracking-wide">
                      {conversa.stage}
                    </span>
                    {conversa.transbordo === 'pausado' && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-red-500/10 text-red-400 uppercase tracking-wide">
                        Humano
                      </span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-[var(--color-foreground-muted)]">Nenhuma conversa encontrada.</div>
            )}
          </div>
        </div>

        {/* Área Principal (Chat e Tabs) */}
        <div className={`flex-1 flex flex-col glass-panel overflow-hidden transition-all duration-300 ${!conversaAtiva && window.innerWidth < 768 ? 'hidden' : 'flex'}`}>
          {conversaAtivaAtualizada ? (
            <>
              {/* Header Conversa com Botão de Expandir Lista */}
              <div className="p-4 border-b border-[var(--color-border)] flex flex-col md:flex-row md:justify-between md:items-center bg-[var(--color-surface-hover)]/30 gap-4">
                <div className="flex items-center gap-3">
                  {!isSidebarOpen && (
                    <button 
                      onClick={() => setIsSidebarOpen(true)}
                      className="hidden md:flex p-2 mr-1 text-[var(--color-foreground-muted)] hover:text-white bg-[var(--color-surface-hover)] rounded-lg transition-colors"
                      title="Expandir lista"
                    >
                      <PanelLeftOpen size={20} />
                    </button>
                  )}
                  <button 
                    className="md:hidden text-[var(--color-foreground-muted)] hover:text-white"
                    onClick={fecharConversaMobile}
                  >
                    <ChevronLeft size={24} />
                  </button>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{conversaAtivaAtualizada.nome}</h3>
                    <p className="text-sm text-[var(--color-foreground-muted)]">{conversaAtivaAtualizada.telefone}</p>
                  </div>
                </div>
                
                <div className="flex w-full md:w-auto gap-2">
                  {conversaAtivaAtualizada.transbordo === 'pausado' ? (
                    <button 
                      onClick={reativarRobo}
                      className="flex-1 md:w-auto flex justify-center items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-lg shadow-green-500/20"
                    >
                      <Power size={16} /> Reativar Robô
                    </button>
                  ) : (
                    <button 
                      onClick={pausarRobo}
                      className="flex-1 md:w-auto flex justify-center items-center gap-2 bg-[var(--color-surface)] border border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] text-[var(--color-foreground-muted)] hover:text-white px-4 py-2 rounded-lg text-sm font-medium transition-all"
                    >
                      <Pause size={16} /> Pausar Robô
                    </button>
                  )}
                </div>
              </div>

              {/* Sistema de Abas */}
              <div className="flex border-b border-[var(--color-border)] bg-[var(--color-surface)] overflow-x-auto">
                <button
                  onClick={() => setActiveTab('mensagens')}
                  className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 whitespace-nowrap flex items-center gap-2 ${
                    activeTab === 'mensagens' 
                      ? 'border-[var(--color-brand-500)] text-white' 
                      : 'border-transparent text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/5'
                  }`}
                >
                  <MessageCircle size={16} /> Mensagens
                </button>
                <button
                  onClick={() => setActiveTab('perfil')}
                  className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 whitespace-nowrap flex items-center gap-2 ${
                    activeTab === 'perfil' 
                      ? 'border-[var(--color-brand-500)] text-white' 
                      : 'border-transparent text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/5'
                  }`}
                >
                  <User size={16} /> Perfil & Ações
                </button>
                <button
                  onClick={() => setActiveTab('triagem')}
                  className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 whitespace-nowrap flex items-center gap-2 ${
                    activeTab === 'triagem' 
                      ? 'border-[var(--color-brand-500)] text-white' 
                      : 'border-transparent text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Sliders size={16} /> Triagem IA
                </button>
              </div>
              
              {/* Conteúdo das Abas */}
              <div className="flex-1 flex flex-col overflow-hidden relative">
                
                {/* Aba 1: Mensagens (Chat) */}
                {activeTab === 'mensagens' && (
                  <>
                    {conversaAtivaAtualizada.transbordo === 'pausado' && (
                      <div className="bg-red-500/10 border-b border-red-500/20 px-4 md:px-6 py-2 md:py-3 flex items-center justify-center gap-2 text-red-400 text-xs md:text-sm font-medium text-center">
                        <AlertTriangle size={16} className="shrink-0" />
                        O robô está pausado. O atendimento agora é humano.
                      </div>
                    )}
                    
                    <div 
                      className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4" 
                      id="chat-messages"
                      ref={chatContainerRef}
                      onScroll={handleScroll}
                    >
                      {loadingMensagens ? (
                        <div className="flex justify-center py-10">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-brand-500)]"></div>
                        </div>
                      ) : (
                        <>
                          {mensagens.map((msg, index) => {
                            const isUser = msg.tipo === 'usuario';
                            return (
                              <div key={index} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                                <div className={`flex max-w-[85%] md:max-w-[65%] lg:max-w-[60%] xl:max-w-[50%] gap-2 md:gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${isUser ? 'bg-[var(--color-surface-hover)]' : 'bg-gradient-to-tr from-[var(--color-brand-600)] to-[var(--color-brand-400)]'}`}>
                                    {isUser ? <User size={16} className="text-[var(--color-foreground-muted)]" /> : <Bot size={16} className="text-white" />}
                                  </div>
                                  
                                  <div className={`p-3 md:p-4 rounded-2xl ${
                                    isUser 
                                      ? 'bg-[var(--color-surface-hover)] text-white rounded-tr-none' 
                                      : 'bg-[var(--color-brand-600)] text-white rounded-tl-none shadow-lg shadow-brand-500/10'
                                  }`}>
                                    <p className="whitespace-pre-wrap text-sm md:text-base leading-relaxed break-words">{msg.mensagem}</p>
                                    <span className={`text-[10px] mt-1 md:mt-2 block ${isUser ? 'text-[var(--color-foreground-muted)] text-right' : 'text-blue-200 text-left'}`}>
                                      {new Date(msg.timestamp).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'})}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                          <div ref={messagesEndRef} />
                        </>
                      )}

                      {/* Botão flutuante para voltar ao fundo */}
                      {!autoScrollEnabled && (
                        <button 
                          onClick={() => {
                            setAutoScrollEnabled(true);
                            scrollToBottom(true);
                          }}
                          className="absolute bottom-24 right-8 bg-[var(--color-brand-500)] text-white p-2 rounded-full shadow-lg hover:bg-[var(--color-brand-600)] transition-all animate-bounce flex items-center gap-2 px-4 text-xs font-bold z-10"
                        >
                          <ChevronLeft size={16} className="-rotate-90" />
                          Novas mensagens
                        </button>
                      )}
                    </div>

                    {/* Input de Mensagem */}
                    {conversaAtivaAtualizada.transbordo === 'pausado' ? (
                      <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-surface)] shrink-0">
                        <form 
                          onSubmit={(e) => {
                            e.preventDefault();
                            handleSendMessage();
                          }}
                          className="flex gap-2 max-w-5xl mx-auto"
                        >
                          <input 
                            type="text"
                            placeholder="Digite sua mensagem aqui..."
                            value={mensagemInput}
                            onChange={(e) => setMensagemInput(e.target.value)}
                            className="flex-1 bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[var(--color-brand-500)] shadow-inner"
                          />
                          <button 
                            type="submit"
                            disabled={!mensagemInput.trim() || enviandoMensagem}
                            className="bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white px-6 py-3 rounded-xl font-bold transition-all disabled:opacity-50 flex items-center gap-2 shadow-lg shadow-brand-500/20"
                          >
                            {enviandoMensagem ? <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" /> : "Enviar"}
                          </button>
                        </form>
                      </div>
                    ) : (
                      <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-surface-hover)]/20 text-center shrink-0">
                        <p className="text-xs text-[var(--color-foreground-muted)]">
                          Pause o robô para enviar mensagens manualmente.
                        </p>
                      </div>
                    )}
                  </>
                )}

                {/* Aba 2: Perfil & Ações */}
                {activeTab === 'perfil' && (
                  <div className="flex-1 overflow-y-auto p-6 md:p-8">
                    <div className="max-w-2xl mx-auto space-y-8">
                      <div className="flex items-center gap-4 pb-6 border-b border-white/5">
                        <div className="w-16 h-16 rounded-full bg-[var(--color-brand-500)]/20 text-[var(--color-brand-500)] flex items-center justify-center">
                          <User size={32} />
                        </div>
                        <div>
                          <h2 className="text-2xl font-bold text-white">{conversaAtivaAtualizada.nome}</h2>
                          <p className="text-[var(--color-foreground-muted)] text-lg font-mono mt-1">{conversaAtivaAtualizada.telefone}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-[var(--color-surface-hover)]/30 border border-white/5 p-6 rounded-2xl">
                          <span className="text-sm text-[var(--color-foreground-muted)] uppercase tracking-wider block mb-2">Estágio do Funil</span>
                          <span className="inline-block text-sm font-bold uppercase tracking-wider px-3 py-1 bg-white/5 border border-white/10 text-white rounded-lg">
                            {conversaAtivaAtualizada.stage}
                          </span>
                        </div>
                        
                        <div className="bg-[var(--color-surface-hover)]/30 border border-white/5 p-6 rounded-2xl flex flex-col justify-center items-start">
                          <span className="text-sm text-[var(--color-foreground-muted)] uppercase tracking-wider block mb-3">Ações Comerciais</span>
                          <button
                            onClick={converterLead}
                            disabled={convertendo}
                            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-5 py-3 rounded-xl font-bold transition-all shadow-lg shadow-blue-600/20 disabled:opacity-50"
                          >
                            {convertendo ? (
                              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                            ) : (
                              <>
                                <Target size={20} /> Converter em Oportunidade
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Aba 3: Triagem IA */}
                {activeTab === 'triagem' && (
                  <div className="flex-1 overflow-y-auto p-6 md:p-8">
                    <div className="max-w-2xl mx-auto space-y-6">
                      <div className="flex items-center gap-3 pb-4 border-b border-white/5">
                        <div className="p-2 bg-[var(--color-brand-500)]/20 rounded-lg">
                          <Sliders className="h-6 w-6 text-[var(--color-brand-500)]" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-white">Dados Capturados</h3>
                          <p className="text-sm text-[var(--color-foreground-muted)]">Informações extraídas automaticamente pela IA durante a conversa.</p>
                        </div>
                      </div>

                      {!conversaAtivaAtualizada.dados_customizados || Object.keys(conversaAtivaAtualizada.dados_customizados).length === 0 ? (
                        <div className="p-10 bg-white/[0.01] border border-dashed border-white/5 rounded-2xl text-center text-[var(--color-foreground-muted)]">
                          <Bot size={48} className="mx-auto mb-4 opacity-20" />
                          <p className="text-lg mb-2 text-white/80">Nenhum dado extraído ainda.</p>
                          <p className="max-w-sm mx-auto">Conforme a IA conversar com o lead, os campos configurados serão preenchidos automaticamente aqui.</p>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {Object.entries(conversaAtivaAtualizada.dados_customizados).map(([key, value]) => {
                            let displayValue = String(value);
                            if (value === true) displayValue = "Sim";
                            if (value === false) displayValue = "Não";
                            if (value === null || value === undefined) displayValue = "-";

                            return (
                              <div key={key} className="p-5 bg-[var(--color-surface-hover)]/30 border border-white/5 rounded-2xl hover:bg-white/[0.03] transition-colors">
                                <span className="text-xs text-[var(--color-foreground-muted)] font-semibold uppercase tracking-wider block mb-1">
                                  {key.replace(/_/g, " ")}
                                </span>
                                <span className="text-base font-bold text-white break-words block">
                                  {displayValue}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-foreground-muted)] p-8 text-center bg-[var(--color-surface)]/50">
              <div className="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center mb-6">
                <MessageCircle size={48} className="opacity-20" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Caixa de Entrada Vazia</h3>
              <p className="max-w-sm">Selecione uma conversa na lista lateral para visualizar o histórico e gerenciar o atendimento.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
