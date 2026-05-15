"use client";

import { useEffect, useState, useRef } from "react";
import api from "@/lib/api";
import { MessageCircle, Bot, User, Power, Search, Pause, AlertTriangle, ChevronLeft } from "lucide-react";

interface ConversaData {
  id: string;
  telefone: string;
  nome: string;
  stage: string;
  ultima_mensagem: string;
  timestamp: string;
  transbordo: string | null;
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
    // Se estiver a menos de 100px do fundo, habilita o auto-scroll
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
    setAutoScrollEnabled(isAtBottom);
  };

  useEffect(() => {
    scrollToBottom();
  }, [mensagens]);

  useEffect(() => {
    conversaAtivaRef.current = conversaAtiva;
  }, [conversaAtiva]);

  // Busca inicial (com spinner)
  async function carregarConversasInicial() {
    try {
      const response = await api.get("dashboard/conversas");
      setConversas(response.data);
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
    setLoadingMensagens(true);
    try {
      const response = await api.get(`/dashboard/conversas/${conversa.telefone}`);
      setMensagens(response.data);
    } catch (error) {
      console.error("Erro ao carregar mensagens:", error);
    } finally {
      setLoadingMensagens(false);
      // Ao abrir nova conversa, força o scroll pro fundo
      setTimeout(() => scrollToBottom(true), 100);
      setAutoScrollEnabled(true);
    }
  }

  function fecharConversaMobile() {
    setConversaAtiva(null);
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
      
      // Atualiza localmente para dar feedback imediato
      const novaMsg: MensagemData = {
        tipo: 'agente',
        mensagem: mensagemInput,
        timestamp: new Date().toISOString()
      };
      
      setMensagens([...mensagens, novaMsg]);
      setMensagemInput("");
      
      // O polling vai atualizar o resto depois
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
        <div className={`w-full md:w-1/3 flex flex-col glass-panel overflow-hidden transition-all ${conversaAtiva ? 'hidden md:flex' : 'flex'}`}>
          <div className="p-4 border-b border-[var(--color-border)]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" size={18} />
              <input 
                type="text" 
                placeholder="Buscar conversa..." 
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2 pl-10 pr-4 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />
            </div>
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

        {/* Histórico da Conversa (Direita) */}
        <div className={`flex-1 flex-col glass-panel overflow-hidden ${conversaAtiva ? 'flex' : 'hidden md:flex'}`}>
          {conversaAtiva ? (
            <>
              {/* Header Conversa */}
              <div className="p-4 border-b border-[var(--color-border)] flex flex-col md:flex-row md:justify-between md:items-center bg-[var(--color-surface-hover)]/30 gap-4">
                <div className="flex items-center gap-3">
                  <button 
                    className="md:hidden text-[var(--color-foreground-muted)] hover:text-white"
                    onClick={fecharConversaMobile}
                  >
                    <ChevronLeft size={24} />
                  </button>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{conversaAtiva.nome}</h3>
                    <p className="text-sm text-[var(--color-foreground-muted)]">{conversaAtiva.telefone}</p>
                  </div>
                </div>
                
                <div className="flex w-full md:w-auto">
                  {conversaAtiva.transbordo === 'pausado' ? (
                    <button 
                      onClick={reativarRobo}
                      className="w-full md:w-auto flex justify-center items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-lg shadow-green-500/20"
                    >
                      <Power size={16} /> Reativar Robô
                    </button>
                  ) : (
                    <button 
                      onClick={pausarRobo}
                      className="w-full md:w-auto flex justify-center items-center gap-2 bg-[var(--color-surface)] border border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] text-[var(--color-foreground-muted)] hover:text-white px-4 py-2 rounded-lg text-sm font-medium transition-all"
                    >
                      <Pause size={16} /> Pausar Robô
                    </button>
                  )}
                </div>
              </div>
              
              {conversaAtiva.transbordo === 'pausado' && (
                <div className="bg-red-500/10 border-b border-red-500/20 px-4 md:px-6 py-2 md:py-3 flex items-center justify-center gap-2 text-red-400 text-xs md:text-sm font-medium text-center">
                  <AlertTriangle size={16} className="shrink-0" />
                  O robô está pausado. O atendimento agora é humano.
                </div>
              )}
              
              <div 
                className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 relative" 
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
                          <div className={`flex max-w-[85%] md:max-w-[70%] gap-2 md:gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${isUser ? 'bg-[var(--color-surface-hover)]' : 'bg-gradient-to-tr from-[var(--color-brand-600)] to-[var(--color-brand-400)]'}`}>
                              {isUser ? <User size={16} className="text-[var(--color-foreground-muted)]" /> : <Bot size={16} className="text-white" />}
                            </div>
                            
                            <div className={`p-3 md:p-4 rounded-2xl ${
                              isUser 
                                ? 'bg-[var(--color-surface-hover)] text-white rounded-tr-none' 
                                : 'bg-[var(--color-brand-600)] text-white rounded-tl-none'
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

                {/* Botão flutuante para voltar ao fundo se houver novas mensagens */}
                {!autoScrollEnabled && (
                  <button 
                    onClick={() => {
                      setAutoScrollEnabled(true);
                      scrollToBottom(true);
                    }}
                    className="absolute bottom-24 right-8 bg-[var(--color-brand-500)] text-white p-2 rounded-full shadow-lg hover:bg-[var(--color-brand-600)] transition-all animate-bounce flex items-center gap-2 px-4 text-xs font-bold"
                  >
                    <ChevronLeft size={16} className="-rotate-90" />
                    Novas mensagens
                  </button>
                )}
              </div>

              {/* Input de Mensagem (Apenas se pausado) */}
              {conversaAtiva.transbordo === 'pausado' ? (
                <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-surface)]">
                  <form 
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendMessage();
                    }}
                    className="flex gap-2"
                  >
                    <input 
                      type="text"
                      placeholder="Digite sua mensagem aqui..."
                      value={mensagemInput}
                      onChange={(e) => setMensagemInput(e.target.value)}
                      className="flex-1 bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                    />
                    <button 
                      type="submit"
                      disabled={!mensagemInput.trim() || enviandoMensagem}
                      className="bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white px-6 py-3 rounded-xl font-bold transition-all disabled:opacity-50 flex items-center gap-2"
                    >
                      {enviandoMensagem ? <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" /> : "Enviar"}
                    </button>
                  </form>
                </div>
              ) : (
                <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-surface-hover)]/20 text-center">
                  <p className="text-xs text-[var(--color-foreground-muted)]">
                    Pause o robô para enviar mensagens manualmente.
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-foreground-muted)] p-8 text-center">
              <MessageCircle size={48} className="mb-4 opacity-20" />
              <p>Selecione uma conversa para visualizar o histórico</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
