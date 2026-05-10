"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Dumbbell, Lock, Mail, Loader2 } from "lucide-react";
import api from "@/lib/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await api.post("dashboard/login", { email, password });
      const { access_token, slug } = response.data;
      
      // Salva o token e o slug no localStorage
      localStorage.setItem("atendia_token", access_token);
      localStorage.setItem("atendia_slug", slug);
      
      // Redireciona para o dashboard específico da empresa
      router.push(`/${slug}`);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError("E-mail ou senha incorretos.");
      } else if (err.response?.status === 403) {
        setError("Sua conta está inativa. Contate o suporte.");
      } else {
        setError("Ocorreu um erro ao tentar fazer login.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden px-4 bg-[#0f172a]">
      {/* Background Decorative Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none"></div>
      
      <div className="w-full max-w-md z-10">
        <div className="glass-panel p-8 md:p-10 border border-white/10 shadow-2xl">
          <div className="flex flex-col items-center mb-10">
            <div className="bg-blue-600 p-3.5 rounded-2xl text-white shadow-xl shadow-blue-600/30 mb-5 transform transition-transform hover:scale-110">
              <Dumbbell size={32} strokeWidth={2.5} />
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">AtendIA</h1>
            <p className="text-slate-400 mt-2 text-center font-medium">
              Gestão Inteligente de Academias
            </p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-4 rounded-xl mb-6 text-center animate-shake">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-300 ml-1">
                E-mail de Acesso
              </label>
              <div className="relative group">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={20} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  placeholder="seu@email.com"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-300 ml-1">
                Sua Senha
              </label>
              <div className="relative group">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={20} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-blue-600/25 disabled:opacity-70 disabled:cursor-not-allowed mt-4 active:scale-[0.98]"
            >
              {loading ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  <span>Autenticando...</span>
                </>
              ) : (
                "Entrar no Painel"
              )}
            </button>
          </form>
        </div>
        
        <p className="text-center mt-8 text-slate-500 text-sm">
          &copy; 2026 AtendIA — Sistema Exclusivo para Academias
        </p>
      </div>
    </div>
  );
}
