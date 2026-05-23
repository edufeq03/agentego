"use client";

import { useState, useEffect } from "react";
import { Smartphone, CheckCircle2, XCircle, Loader2, RefreshCw, LogOut, Plus, Trash2, Save, ChefHat, Info, ShieldAlert } from "lucide-react";
import api from "@/lib/api";

export default function WhatsAppConnection() {
  const [status, setStatus] = useState<string>("loading");
  const [instance, setInstance] = useState<string>("");
  const [qrcode, setQrcode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Estados dos novos telefones centralizados
  const [telefoneProprietario, setTelefoneProprietario] = useState("");
  const [telefonesIgnorados, setTelefonesIgnorados] = useState<string[]>([]);
  const [whatsappCozinha, setWhatsappCozinha] = useState("");
  const [nicho, setNicho] = useState("generico");
  
  const [newIgnoredPhone, setNewIgnoredPhone] = useState("");
  const [savingConfig, setSavingConfig] = useState(false);
  const [savedConfig, setSavedConfig] = useState(false);
  const [hasLoadedInitial, setHasLoadedInitial] = useState(false);

  async function checkStatus() {
    try {
      const response = await api.get("dashboard/whatsapp/status");
      const data = response.data;
      
      setStatus(data.status);
      setInstance(data.instance);
      setQrcode(data.qrcode);
      setError(null);

      // Carrega os estados de telefone apenas na primeira inicialização para não apagar digitações em andamento
      if (!hasLoadedInitial) {
        setTelefoneProprietario(data.telefone_proprietario || "");
        setTelefonesIgnorados(data.telefones_ignorados || []);
        setWhatsappCozinha(data.whatsapp_cozinha || "");
        setNicho(data.nicho || "generico");
        setHasLoadedInitial(true);
      }
    } catch (err: any) {
      setError("Não foi possível carregar o status do WhatsApp.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Polling para atualizar o status e o QR Code
  useEffect(() => {
    checkStatus();
    const interval = setInterval(() => {
      // Só faz polling se não estiver conectado
      if (status !== "connected") {
        checkStatus();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [status, hasLoadedInitial]);

  async function handleLogout() {
    if (!confirm("Tem certeza que deseja desconectar este WhatsApp?")) return;
    
    setLoading(true);
    try {
      await api.post("dashboard/whatsapp/logout");
      await checkStatus();
    } catch (err) {
      alert("Erro ao desconectar WhatsApp.");
    } finally {
      setLoading(false);
    }
  }

  async function handleConnect() {
    setLoading(true);
    try {
      await api.post("dashboard/whatsapp/connect");
      setTimeout(() => checkStatus(), 2000);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erro ao conectar WhatsApp.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSync() {
    setLoading(true);
    try {
      const response = await api.post("dashboard/whatsapp/sync");
      alert(response.data?.mensagem || "Configurações sincronizadas com sucesso!");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erro ao sincronizar configurações do WhatsApp.");
    } finally {
      setLoading(false);
    }
  }

  // Ações de persistência de telefones centralizados
  async function handleSaveConfig(e: React.FormEvent) {
    e.preventDefault();
    setSavingConfig(true);
    setSavedConfig(false);
    
    try {
      await api.post("dashboard/whatsapp/config", {
        telefone_proprietario: telefoneProprietario,
        telefones_ignorados: telefonesIgnorados,
        whatsapp_cozinha: whatsappCozinha
      });
      setSavedConfig(true);
      setTimeout(() => setSavedConfig(false), 3000);
    } catch (err: any) {
      console.error("Erro ao salvar contatos:", err);
      alert("Erro ao salvar configurações de telefones.");
    } finally {
      setSavingConfig(false);
    }
  }

  const addIgnoredPhone = () => {
    const cleanPhone = newIgnoredPhone.replace(/\D/g, "");
    if (!cleanPhone) return;
    if (telefonesIgnorados.includes(cleanPhone)) {
      alert("Este número já está na lista.");
      return;
    }
    setTelefonesIgnorados([...telefonesIgnorados, cleanPhone]);
    setNewIgnoredPhone("");
  };

  const removeIgnoredPhone = (phone: string) => {
    setTelefonesIgnorados(telefonesIgnorados.filter((p) => p !== phone));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Central de WhatsApp & Contatos</h1>
          <p className="text-slate-400">Gerencie a linha do robô, contatos administrativos e números ignorados</p>
        </div>
        
        {status === "connected" && (
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl transition-all border border-red-500/20"
          >
            <LogOut size={18} />
            Desconectar WhatsApp
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Card de Status */}
        <div className="lg:col-span-1 glass-panel p-6 border border-white/10">
          <div className="flex items-center gap-4 mb-6">
            <div className={`p-3 rounded-2xl ${status === "connected" ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-800 text-slate-400"}`}>
              <Smartphone size={24} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Status Atual</h3>
              <p className={`text-lg font-bold ${status === "connected" ? "text-emerald-400" : "text-amber-400"}`}>
                {status === "connected" ? "Conectado" : status === "loading" ? "Carregando..." : "Desconectado"}
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
              <p className="text-xs text-slate-500 mb-1 font-medium uppercase">Instância</p>
              <p className="text-sm text-slate-300 font-mono">{instance || "Gerando..."}</p>
            </div>

            {status === "connected" ? (
              <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10 flex items-start gap-3">
                <CheckCircle2 className="text-emerald-500 shrink-0 mt-0.5" size={18} />
                <p className="text-sm text-emerald-200/70">
                  Seu robô está online e respondendo mensagens normalmente.
                </p>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10 flex items-start gap-3">
                <XCircle className="text-amber-500 shrink-0 mt-0.5" size={18} />
                <p className="text-sm text-amber-200/70">
                  O robô está pausado até que o QR Code seja escaneado.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Card do QR Code / Instruções */}
        <div className="lg:col-span-2 glass-panel p-8 border border-white/10 flex flex-col items-center justify-center min-h-[300px]">
          {loading && (status === "loading" || status === "not_found") ? (
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="text-blue-500 animate-spin" size={48} />
              <p className="text-slate-400 animate-pulse">Iniciando conexão...</p>
            </div>
          ) : status === "connected" ? (
            <div className="text-center space-y-6">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-500/10 text-emerald-500 mb-1">
                <CheckCircle2 size={40} />
              </div>
              <h2 className="text-xl font-bold text-white">WhatsApp Conectado!</h2>
              <p className="text-slate-400 max-w-sm mx-auto text-sm">
                Tudo pronto! Seu agente inteligente já está operando nesta linha de WhatsApp.
              </p>
              <div className="pt-2 flex flex-col sm:flex-row gap-3 justify-center">
                <button 
                  onClick={checkStatus}
                  className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-all text-sm"
                >
                  <RefreshCw size={16} />
                  Atualizar Status
                </button>
                <button 
                  onClick={handleSync}
                  className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold transition-all shadow-lg shadow-blue-600/20 text-sm"
                >
                  <RefreshCw size={16} />
                  Sincronizar Eventos
                </button>
              </div>
            </div>
          ) : status === "not_found" ? (
            <div className="text-center space-y-6">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-blue-500/10 text-blue-500 mb-1">
                <Smartphone size={40} />
              </div>
              <h2 className="text-xl font-bold text-white">Pronto para Conectar</h2>
              <p className="text-slate-400 max-w-sm mx-auto text-sm">
                Sua instância ainda não foi criada na Evolution API. Clique no botão abaixo para iniciar o processo.
              </p>
              <button 
                onClick={handleConnect}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold transition-all shadow-lg shadow-blue-600/20 text-sm"
              >
                Criar Instância e Gerar QR Code
              </button>
            </div>
          ) : (
            <div className="flex flex-col md:flex-row items-center gap-8 w-full max-w-2xl">
              <div className="flex-1 space-y-4">
                <h2 className="text-xl font-bold text-white">Escaneie o QR Code</h2>
                <ol className="space-y-3">
                  {[
                    "Abra o WhatsApp no seu celular",
                    "Toque em Aparelhos conectados",
                    "Toque em Conectar um aparelho",
                    "Aponte seu celular para esta tela"
                  ].map((step, i) => (
                    <li key={i} className="flex gap-3 items-start text-sm">
                      <span className="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600/20 text-blue-400 text-[10px] font-bold shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      <span className="text-slate-300">{step}</span>
                    </li>
                  ))}
                </ol>
                
                <p className="text-[11px] text-slate-500 italic">
                  O QR Code atualiza automaticamente a cada 30 segundos se não for utilizado.
                </p>
              </div>
 
              <div className="relative group shrink-0">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                <div className="relative bg-white p-3 rounded-xl overflow-hidden shadow-2xl">
                  {qrcode ? (
                    <img 
                      src={qrcode.startsWith("data:image") ? qrcode : `data:image/png;base64,${qrcode}`} 
                      alt="WhatsApp QR Code" 
                      className="w-48 h-48"
                    />
                  ) : (
                    <div className="w-48 h-48 flex flex-col items-center justify-center gap-3 bg-slate-50">
                      <Loader2 className="text-blue-500 animate-spin" size={28} />
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest">Gerando QR...</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* NOVO: Central Unificada de Contatos e Alertas */}
      <form onSubmit={handleSaveConfig} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card 2: Contatos Administrativos e Alertas */}
        <div className="glass-panel p-6 border border-white/10 flex flex-col space-y-6">
          <div>
            <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              <ShieldAlert className="text-blue-400" size={20} />
              Contatos Administrativos & Alertas
            </h2>
            <p className="text-xs text-slate-400">Configure quem recebe códigos de acesso e alertas de intervenção humana.</p>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 ml-1">
                WhatsApp do Proprietário (Alertas e Recuperação)
              </label>
              <input
                type="text"
                value={telefoneProprietario}
                onChange={(e) => setTelefoneProprietario(e.target.value)}
                placeholder="Ex: 5519996737713"
                className="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 transition-all text-sm"
              />
              <p className="text-[10px] text-slate-500 italic">Preencha com o código do país + DDD + número (somente números, ex: 5519996737713).</p>
            </div>

            <div className="space-y-3 pt-2">
              <label className="text-xs font-semibold text-slate-300 ml-1">
                Lista de Números Ignorados (Blacklist do Robô)
              </label>
              
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newIgnoredPhone}
                  onChange={(e) => setNewIgnoredPhone(e.target.value)}
                  placeholder="Ex: 5519988887777"
                  className="flex-1 bg-slate-900/50 border border-slate-800 rounded-xl py-2.5 px-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500 transition-all text-sm"
                />
                <button
                  type="button"
                  onClick={addIgnoredPhone}
                  className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold transition-all text-sm flex items-center justify-center shrink-0"
                >
                  <Plus size={16} />
                </button>
              </div>

              {telefonesIgnorados.length > 0 ? (
                <div className="flex flex-wrap gap-2 p-3 bg-slate-950/40 rounded-xl border border-slate-900 min-h-[60px]">
                  {telefonesIgnorados.map((phone) => (
                    <div 
                      key={phone} 
                      className="flex items-center gap-2 px-3 py-1 bg-slate-800/80 text-slate-300 text-xs font-mono rounded-full border border-slate-700 hover:border-red-500 hover:text-red-400 transition-all cursor-pointer group"
                      onClick={() => removeIgnoredPhone(phone)}
                    >
                      <span>{phone}</span>
                      <Trash2 size={12} className="text-slate-500 group-hover:text-red-400 transition-colors" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl border border-dashed border-slate-800 text-center text-xs text-slate-500">
                  Nenhum número ignorado cadastrado. O robô responderá a todas as linhas.
                </div>
              )}
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={savingConfig}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-600/25 text-sm disabled:opacity-75"
            >
              {savingConfig ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Salvando...</span>
                </>
              ) : savedConfig ? (
                <>
                  <CheckCircle2 size={16} className="text-emerald-400" />
                  <span>Configurações Salvas!</span>
                </>
              ) : (
                <>
                  <Save size={16} />
                  <span>Salvar Configurações de Telefones</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Card 3: Contatos Setoriais e Nicho */}
        <div className="glass-panel p-6 border border-white/10 flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              {nicho === "lanchonete" ? (
                <>
                  <ChefHat className="text-blue-400" size={20} />
                  Contatos de Produção (Cozinha)
                </>
              ) : (
                <>
                  <Info className="text-blue-400" size={20} />
                  Direcionamento e Transbordo Humano
                </>
              )}
            </h2>
            <p className="text-xs text-slate-400">
              {nicho === "lanchonete" 
                ? "Configure para onde o robô deve despachar as comandas e comandar a produção."
                : "Veja o fluxo de funcionamento e atendimento humano da sua inteligência."}
            </p>
          </div>

          <div className="flex-1 flex flex-col justify-center space-y-4 py-4">
            {nicho === "lanchonete" ? (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 ml-1">
                  WhatsApp da Cozinha / Despacho
                </label>
                <input
                  type="text"
                  value={whatsappCozinha}
                  onChange={(e) => setWhatsappCozinha(e.target.value)}
                  placeholder="Ex: 5519996737713"
                  className="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 transition-all text-sm font-mono"
                />
                <p className="text-[10px] text-slate-500 italic">Pedidos feitos pelo cardápio automático da IA serão despachados diretamente para este número.</p>
              </div>
            ) : (
              <div className="p-4 bg-slate-950/40 rounded-xl border border-slate-900 space-y-3">
                <div className="flex gap-3 items-start">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                  <p className="text-xs text-slate-300 leading-relaxed">
                    <strong>Nicho Ativo:</strong> Nível de atendimento personalizado para <span className="text-blue-400 font-bold uppercase">{nicho}</span>.
                  </p>
                </div>
                <div className="flex gap-3 items-start">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                  <p className="text-xs text-slate-300 leading-relaxed">
                    <strong>Transbordo Inteligente:</strong> Quando o robô necessita de auxílio manual de um atendente físico, ele dispara instantaneamente uma notificação contendo o histórico para o seu número administrativo de controle.
                  </p>
                </div>
                <div className="flex gap-3 items-start">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                  <p className="text-xs text-slate-300 leading-relaxed">
                    Você pode alterar este comportamento cadastrando novos parâmetros ou configurando novas chaves de comportamento em Configurações Gerais.
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="pt-2 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
            <Info size={14} className="text-slate-400" />
            <span>Utilize apenas números com DDI brasileiro (55) + DDD (ex: 5519...).</span>
          </div>
        </div>
      </form>
    </div>
  );
}
