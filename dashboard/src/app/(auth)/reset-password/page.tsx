"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Smartphone, Lock, KeyRound, Loader2, ArrowLeft } from "lucide-react";
import api from "@/lib/api";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";

  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleResetPassword(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    if (newPassword !== confirmPassword) {
      setError("As senhas não coincidem.");
      setLoading(false);
      return;
    }

    if (newPassword.length < 6) {
      setError("A nova senha deve ter pelo menos 6 caracteres.");
      setLoading(false);
      return;
    }

    try {
      await api.post("dashboard/reset-password", {
        email,
        code,
        new_password: newPassword,
      });
      
      setSuccess("Senha redefinida com sucesso! Redirecionando para o login...");
      
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Código incorreto, expirado ou inválido.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md z-10">
      <div className="glass-panel p-8 md:p-10 border border-white/10 shadow-2xl">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-blue-600 p-3.5 rounded-2xl text-white shadow-xl shadow-blue-600/30 mb-5 transform transition-transform hover:scale-110">
            <Smartphone size={32} strokeWidth={2.5} />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Nova Senha</h1>
          <p className="text-slate-400 mt-2 text-center text-sm font-medium">
            Insira o código de 6 dígitos enviado ao seu WhatsApp e defina sua nova senha.
          </p>
          {email && (
            <span className="text-xs text-blue-400 font-semibold mt-2 px-3 py-1 bg-blue-500/10 rounded-full border border-blue-500/20">
              {email}
            </span>
          )}
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-4 rounded-xl mb-6 text-center animate-shake">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm p-4 rounded-xl mb-6 text-center">
            {success}
          </div>
        )}

        <form onSubmit={handleResetPassword} className="space-y-5">
          <div className="space-y-1.5">
            <label className="text-sm font-semibold text-slate-300 ml-1">
              Código de 6 dígitos
            </label>
            <div className="relative group">
              <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={20} />
              <input
                type="text"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                required
                disabled={!!success}
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all font-mono tracking-widest text-center text-lg disabled:opacity-50"
                placeholder="000000"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-semibold text-slate-300 ml-1">
              Nova Senha
            </label>
            <div className="relative group">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={20} />
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                disabled={!!success}
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50"
                placeholder="Mínimo 6 caracteres"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-semibold text-slate-300 ml-1">
              Confirmar Nova Senha
            </label>
            <div className="relative group">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={20} />
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={!!success}
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50"
                placeholder="Repita a nova senha"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !!success}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-blue-600/25 disabled:opacity-70 disabled:cursor-not-allowed mt-6 active:scale-[0.98]"
          >
            {loading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                <span>Validando & Redefinindo...</span>
              </>
            ) : (
              "Redefinir Minha Senha"
            )}
          </button>
        </form>

        <div className="flex justify-center mt-6">
          <Link href="/login" className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors">
            <ArrowLeft size={14} /> Voltar para o login
          </Link>
        </div>
      </div>
      
      <p className="text-center mt-8 text-slate-500 text-sm">
        &copy; 2026 AgenteGo — Sistema de Atendimento via IA
      </p>
    </div>
  );
}

export default function ResetPassword() {
  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden px-4 bg-[#0f172a]">
      {/* Background Decorative Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none"></div>
      
      <Suspense fallback={
        <div className="flex flex-col items-center justify-center text-white gap-3">
          <Loader2 size={40} className="animate-spin text-blue-500" />
          <span className="text-sm font-semibold text-slate-400">Carregando formulário...</span>
        </div>
      }>
        <ResetPasswordForm />
      </Suspense>
    </div>
  );
}
