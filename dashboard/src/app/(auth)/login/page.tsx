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
      const response = await api.post("/dashboard/login", { email, password });
      const { access_token } = response.data;
      
      // Salva o token no localStorage
      localStorage.setItem("atendia_token", access_token);
      
      // Redireciona para o dashboard
      router.push("/");
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
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)] px-4">
      <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[var(--color-brand-900)]/40 via-[var(--color-background)] to-[var(--color-background)] pointer-events-none"></div>

      <div className="w-full max-w-md glass-panel p-8 md:p-10 z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-[var(--color-brand-500)] p-3 rounded-2xl text-white shadow-lg shadow-[var(--color-brand-500)]/30 mb-4">
            <Dumbbell size={32} />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">AtendIA</h1>
          <p className="text-sm text-[var(--color-foreground-muted)] mt-1 text-center">
            Faça login para acessar o painel do seu Agente Virtual.
          </p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-3 rounded-lg mb-6 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1.5">
              E-mail
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" size={18} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-[var(--color-brand-500)] focus:ring-1 focus:ring-[var(--color-brand-500)] transition-all"
                placeholder="seu@email.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--color-foreground-muted)] mb-1.5">
              Senha
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" size={18} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-[var(--color-brand-500)] focus:ring-1 focus:ring-[var(--color-brand-500)] transition-all"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-[var(--color-brand-600)] to-[var(--color-brand-400)] hover:from-[var(--color-brand-500)] hover:to-[var(--color-brand-300)] text-white font-medium py-2.5 rounded-lg transition-all shadow-lg shadow-[var(--color-brand-500)]/20 disabled:opacity-70 disabled:cursor-not-allowed mt-2"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : "Entrar no Painel"}
          </button>
        </form>
      </div>
    </div>
  );
}
