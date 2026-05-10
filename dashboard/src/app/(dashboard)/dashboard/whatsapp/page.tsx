"use client";

import { useState, useEffect } from "react";
import { Smartphone, CheckCircle2, XCircle, Loader2, RefreshCw, LogOut } from "lucide-react";
import api from "@/lib/api";

export default function WhatsAppConnection() {
  const [status, setStatus] = useState<string>("loading");
  const [instance, setInstance] = useState<string>("");
  const [qrcode, setQrcode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function checkStatus() {
    try {
      const response = await api.get("/dashboard/whatsapp/status");
      const data = response.data;
      
      setStatus(data.status);
      setInstance(data.instance);
      setQrcode(data.qrcode);
      setError(null);
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
    }, 5000);

    return () => clearInterval(interval);
  }, [status]);

  async function handleLogout() {
    if (!confirm("Tem certeza que deseja desconectar este WhatsApp?")) return;
    
    setLoading(true);
    try {
      await api.post("/dashboard/whatsapp/logout");
      await checkStatus();
    } catch (err) {
      alert("Erro ao desconectar WhatsApp.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Conexão WhatsApp</h1>
          <p className="text-slate-400">Gerencie a conexão do seu robô com o WhatsApp</p>
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
        <div className="lg:col-span-2 glass-panel p-8 border border-white/10 flex flex-col items-center justify-center min-h-[400px]">
          {loading && status === "loading" ? (
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="text-blue-500 animate-spin" size={48} />
              <p className="text-slate-400 animate-pulse">Sincronizando com Evolution API...</p>
            </div>
          ) : status === "connected" ? (
            <div className="text-center space-y-6">
              <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-emerald-500/10 text-emerald-500 mb-2">
                <CheckCircle2 size={48} />
              </div>
              <h2 className="text-2xl font-bold text-white">WhatsApp Conectado!</h2>
              <p className="text-slate-400 max-w-sm mx-auto">
                Tudo pronto! Seu agente inteligente já está operando nesta linha de WhatsApp.
              </p>
              <div className="pt-4">
                <button 
                  onClick={checkStatus}
                  className="flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-all mx-auto"
                >
                  <RefreshCw size={18} />
                  Atualizar Status
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col md:flex-row items-center gap-12 w-full max-w-2xl">
              <div className="flex-1 space-y-6">
                <h2 className="text-2xl font-bold text-white">Escaneie o QR Code</h2>
                <ol className="space-y-4">
                  {[
                    "Abra o WhatsApp no seu celular",
                    "Toque em Aparelhos conectados",
                    "Toque em Conectar um aparelho",
                    "Aponte seu celular para esta tela"
                  ].map((step, i) => (
                    <li key={i} className="flex gap-4 items-start">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-600/20 text-blue-400 text-xs font-bold shrink-0">
                        {i + 1}
                      </span>
                      <span className="text-slate-300">{step}</span>
                    </li>
                  ))}
                </ol>
                
                <p className="text-xs text-slate-500 mt-6 italic">
                  O QR Code atualiza automaticamente a cada 30 segundos se não for utilizado.
                </p>
              </div>

              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                <div className="relative bg-white p-4 rounded-xl overflow-hidden shadow-2xl">
                  {qrcode ? (
                    <img 
                      src={qrcode.startsWith("data:image") ? qrcode : `data:image/png;base64,${qrcode}`} 
                      alt="WhatsApp QR Code" 
                      className="w-64 h-64"
                    />
                  ) : (
                    <div className="w-64 h-64 flex flex-col items-center justify-center gap-3 bg-slate-50">
                      <Loader2 className="text-blue-500 animate-spin" size={32} />
                      <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Gerando QR...</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
