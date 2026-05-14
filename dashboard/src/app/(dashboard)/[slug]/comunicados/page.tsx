"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { 
  Megaphone, 
  Send, 
  Users, 
  AlertCircle, 
  CheckCircle2,
  Loader2
} from "lucide-react";
import api from "@/lib/api";

export default function ComunicadosPage() {
  const params = useParams();
  const slug = params?.slug as string;
  
  const [mensagem, setMensagem] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!mensagem.trim()) return;

    if (!confirm("Isso enviará uma mensagem para TODOS os alunos ativos. Continuar?")) return;

    setLoading(true);
    setStatus('idle');

    try {
      // Endpoint a ser implementado no backend se necessário, 
      // ou podemos usar um loop aqui chamando o envio individual (não recomendado para grandes listas)
      // Por enquanto, vamos simular o envio ou disparar para um endpoint de broadcast
      await api.post('dashboard/comunicados/enviar', { mensagem });
      setStatus('success');
      setMensagem("");
    } catch (error) {
      console.error("Erro ao enviar comunicado:", error);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div>
        <h2 className="text-3xl font-bold text-white tracking-tight">Comunicados em Massa</h2>
        <p className="text-[var(--color-foreground-muted)] mt-1">
          Envie novidades, promoções ou avisos gerais para todos os seus alunos via WhatsApp.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl">
            <form onSubmit={handleSend} className="space-y-4">
              <label className="block text-sm font-medium text-white">
                Sua Mensagem
              </label>
              <textarea 
                rows={8}
                value={mensagem}
                onChange={(e) => setMensagem(e.target.value)}
                placeholder="Ex: Olá pessoal! Amanhã teremos um horário especial devido ao feriado..."
                className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl p-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all resize-none"
              />
              
              <div className="flex items-center justify-between">
                <p className="text-xs text-[var(--color-foreground-muted)]">
                  Use com moderação para evitar bloqueios de SPAM.
                </p>
                <button 
                  type="submit"
                  disabled={loading || !mensagem.trim()}
                  className="flex items-center gap-2 px-6 py-3 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] disabled:opacity-50 text-white rounded-xl font-bold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
                >
                  {loading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                  Disparar para todos
                </button>
              </div>
            </form>
          </div>

          {status === 'success' && (
            <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl flex items-center gap-3 text-emerald-500 animate-in slide-in-from-top-2">
              <CheckCircle2 size={20} />
              <p className="text-sm font-medium">Comunicado enviado com sucesso para a fila de disparo!</p>
            </div>
          )}

          {status === 'error' && (
            <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center gap-3 text-red-500 animate-in slide-in-from-top-2">
              <AlertCircle size={20} />
              <p className="text-sm font-medium">Erro ao processar o disparo. Tente novamente mais tarde.</p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl">
            <h4 className="font-bold text-white mb-4 flex items-center gap-2">
              <Users size={18} className="text-[var(--color-brand-400)]" />
              Público Alvo
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-[var(--color-foreground-muted)]">Alunos Ativos</span>
                <span className="text-white font-medium">Carregando...</span>
              </div>
              <div className="h-1 bg-[var(--color-background)] rounded-full overflow-hidden">
                <div className="h-full bg-[var(--color-brand-500)] w-full" />
              </div>
              <p className="text-[10px] text-[var(--color-foreground-muted)] leading-relaxed">
                Mensagens serão enviadas individualmente respeitando um intervalo de segurança para evitar banimento.
              </p>
            </div>
          </div>

          <div className="bg-amber-500/5 border border-amber-500/10 p-6 rounded-2xl">
            <h4 className="font-bold text-amber-500 mb-2 flex items-center gap-2 text-sm">
              <AlertCircle size={16} />
              Dica de Ouro
            </h4>
            <p className="text-xs text-amber-500/80 leading-relaxed">
              Mensagens curtas e personalizadas convertem mais e reduzem as chances de o usuário denunciar como spam.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
