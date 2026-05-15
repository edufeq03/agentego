"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { 
  Megaphone, 
  Send, 
  Users, 
  AlertCircle, 
  CheckCircle2,
  Loader2,
  Calendar,
  History,
  Trash2,
  Clock,
  Image as ImageIcon
} from "lucide-react";
import api from "@/lib/api";

export default function ComunicadosPage() {
  const params = useParams();
  const slug = params?.slug as string;
  
  const [mensagem, setMensagem] = useState("");
  const [imagemUrl, setImagemUrl] = useState("");
  const [uploading, setUploading] = useState(false);
  const [dataProgramada, setDataProgramada] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [historico, setHistorico] = useState<any[]>([]);
  const [totalMembros, setTotalMembros] = useState<number | null>(null);
  const [logsAbertos, setLogsAbertos] = useState<string | null>(null);
  const [logs, setLogs] = useState<any[]>([]);

  const apiBaseUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

  useEffect(() => {
    fetchHistorico();
    fetchStats();
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('dashboard/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setImagemUrl(res.data.url);
    } catch (e) {
      alert("Erro ao subir imagem.");
    } finally {
      setUploading(false);
    }
  }

  async function fetchLogs(id: string) {
    setLogsAbertos(id);
    setLogs([]);
    try {
      const res = await api.get(`dashboard/comunicados/${id}/logs`);
      setLogs(res.data);
    } catch (e) {
      console.error(e);
    }
  }

  async function fetchStats() {
    try {
      const res = await api.get('dashboard/membros');
      const ativos = res.data.filter((m: any) => m.ativo).length;
      setTotalMembros(ativos);
    } catch (e) {
      console.error(e);
    }
  }

  async function fetchHistorico() {
    try {
      const res = await api.get('dashboard/comunicados');
      setHistorico(res.data);
    } catch (e) {
      console.error(e);
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!mensagem.trim()) return;

    if (!confirm("Isso enviará uma mensagem para TODOS os alunos ativos. Continuar?")) return;

    setLoading(true);
    setStatus('idle');

    try {
      await api.post('dashboard/comunicados/enviar', { 
        mensagem,
        imagem_url: imagemUrl,
        data_programada: dataProgramada ? new Date(dataProgramada).toISOString() : null
      });
      setStatus('success');
      setMensagem("");
      setImagemUrl("");
      setDataProgramada("");
      fetchHistorico();
    } catch (error) {
      console.error("Erro ao enviar comunicado:", error);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Deseja cancelar este agendamento?")) return;
    try {
      await api.delete(`dashboard/comunicados/${id}`);
      fetchHistorico();
    } catch (e) {
      alert("Erro ao excluir.");
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

      <div className="grid grid-cols-1 gap-6">
        <div className="space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-xl">
            <form onSubmit={handleSend} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-white">
                    Sua Mensagem
                  </label>
                  <textarea 
                    rows={10}
                    value={mensagem}
                    onChange={(e) => setMensagem(e.target.value)}
                    placeholder="Ex: Olá pessoal! Amanhã teremos um horário especial devido ao feriado..."
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl p-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all resize-none"
                  />
                </div>

                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-white flex items-center gap-2">
                      <ImageIcon size={16} className="text-[var(--color-brand-400)]" />
                      Imagem / Anexo
                    </label>
                    <div className="flex items-center gap-3">
                      <label className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-[var(--color-background)] border-2 border-dashed border-[var(--color-border)] hover:border-[var(--color-brand-500)]/50 rounded-xl cursor-pointer transition-all">
                        <input 
                          type="file" 
                          className="hidden" 
                          accept="image/*"
                          onChange={handleUpload}
                        />
                        {uploading ? (
                          <Loader2 className="animate-spin text-[var(--color-brand-400)]" size={20} />
                        ) : (
                          <ImageIcon size={20} className="text-[var(--color-foreground-muted)]" />
                        )}
                        <span className="text-sm text-[var(--color-foreground-muted)]">
                          {imagemUrl ? "Alterar imagem" : "Clique para anexar imagem"}
                        </span>
                      </label>
                      {imagemUrl && (
                        <button 
                          type="button"
                          onClick={() => setImagemUrl("")}
                          className="p-3 text-red-400 hover:bg-red-400/10 rounded-xl transition-colors"
                        >
                          <Trash2 size={20} />
                        </button>
                      )}
                    </div>
                  </div>

                  {imagemUrl && (
                    <div className="relative aspect-video w-full bg-[var(--color-background)] rounded-xl overflow-hidden border border-[var(--color-border)] group">
                      <img 
                        src={imagemUrl.startsWith('http') ? imagemUrl : `${apiBaseUrl}${imagemUrl}`} 
                        alt="Preview" 
                        className="w-full h-full object-cover"
                        onError={(e) => (e.currentTarget.style.display = 'none')}
                      />
                      <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-xs text-white font-medium">Prévia da Imagem</span>
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-white flex items-center gap-2">
                      <Calendar size={16} className="text-[var(--color-brand-400)]" />
                      Programar Envio (Opcional)
                    </label>
                    <input 
                      type="datetime-local"
                      value={dataProgramada}
                      onChange={(e) => setDataProgramada(e.target.value)}
                      className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all"
                    />
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-4 border-t border-[var(--color-border)]">
                <div className="flex items-center gap-4 text-[var(--color-foreground-muted)]">
                   <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--color-background)] rounded-lg border border-[var(--color-border)]">
                      <Users size={14} className="text-[var(--color-brand-400)]" />
                      <span className="text-xs font-medium text-white">{totalMembros !== null ? totalMembros : '...'} Alunos Ativos</span>
                   </div>
                   <p className="text-xs hidden md:block">
                    Intervalo dinâmico ativado para maior segurança.
                  </p>
                </div>
                <button 
                  type="submit"
                  disabled={loading || !mensagem.trim()}
                  className="w-full md:w-auto flex items-center justify-center gap-2 px-8 py-4 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] disabled:opacity-50 text-white rounded-xl font-bold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
                >
                  {loading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                  Disparar para todos
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Tabela de Histórico */}
      <div className="space-y-4 pb-20">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <History size={20} className="text-[var(--color-brand-400)]" />
          Histórico e Agendamentos
        </h3>
        
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden overflow-x-auto shadow-lg">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[var(--color-background)] border-b border-[var(--color-border)]">
                <th className="p-4 text-xs font-bold text-[var(--color-foreground-muted)] uppercase tracking-wider">Data</th>
                <th className="p-4 text-xs font-bold text-[var(--color-foreground-muted)] uppercase tracking-wider">Mensagem</th>
                <th className="p-4 text-xs font-bold text-[var(--color-foreground-muted)] uppercase tracking-wider">Público</th>
                <th className="p-4 text-xs font-bold text-[var(--color-foreground-muted)] uppercase tracking-wider">Status</th>
                <th className="p-4 text-xs font-bold text-[var(--color-foreground-muted)] uppercase tracking-wider text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {historico.map((com) => (
                <tr key={com.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="p-4 whitespace-nowrap">
                    <div className="flex flex-col">
                      <span className="text-sm text-white">
                        {new Date(com.data_programada || com.criado_em).toLocaleDateString('pt-BR')}
                      </span>
                      <span className="text-[10px] text-[var(--color-foreground-muted)]">
                        {new Date(com.data_programada || com.criado_em).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </td>
                  <td className="p-4 min-w-[200px]">
                    <p className="text-sm text-white line-clamp-2">{com.mensagem}</p>
                  </td>
                  <td className="p-4">
                    <span className="text-xs text-white">{com.total_membros} alunos</span>
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase border ${
                      com.status === 'enviado' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                      com.status === 'pendente' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' :
                      com.status === 'enviando' ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' :
                      'bg-red-500/10 text-red-500 border-red-500/20'
                    }`}>
                      {com.status === 'pendente' && <Clock size={10} />}
                      {com.status === 'enviado' && <CheckCircle2 size={10} />}
                      {com.status === 'enviando' && <Loader2 className="animate-spin" size={10} />}
                      {com.status}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button 
                        onClick={() => fetchLogs(com.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/10 rounded-lg transition-all"
                      >
                        Auditoria
                      </button>
                      {com.status === 'pendente' && (
                        <button 
                          onClick={() => handleDelete(com.id)}
                          className="p-2 text-[var(--color-foreground-muted)] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {historico.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-[var(--color-foreground-muted)] text-sm italic">
                    Nenhum comunicado enviado ou agendado ainda.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      {/* Modal de Auditoria */}
      {logsAbertos && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-300">
            <div className="p-6 border-b border-[var(--color-border)] flex items-center justify-between bg-[var(--color-background)]">
              <div>
                <h3 className="text-xl font-bold text-white">Relatório de Entrega</h3>
                <p className="text-xs text-[var(--color-foreground-muted)]">Detalhamento por número de telefone</p>
              </div>
              <button 
                onClick={() => setLogsAbertos(null)}
                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
              >
                <Trash2 size={20} className="text-[var(--color-foreground-muted)]" />
              </button>
            </div>
            
            <div className="p-6 max-h-[60vh] overflow-y-auto space-y-3">
              {logs.length === 0 ? (
                <div className="text-center py-12 space-y-4">
                  <Loader2 className="animate-spin mx-auto text-[var(--color-brand-400)]" size={32} />
                  <p className="text-[var(--color-foreground-muted)] text-sm">Processando registros...</p>
                </div>
              ) : (
                logs.map((log) => (
                  <div key={log.id} className="flex items-center justify-between p-4 bg-[var(--color-background)] rounded-xl border border-[var(--color-border)]">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${log.status === 'sucesso' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                        {log.status === 'sucesso' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{log.telefone}</p>
                        {log.erro && <p className="text-[10px] text-red-400 mt-1">{log.erro}</p>}
                      </div>
                    </div>
                    <span className="text-[10px] text-[var(--color-foreground-muted)] font-mono">
                      {new Date(log.criado_em).toLocaleTimeString()}
                    </span>
                  </div>
                ))
              )}
            </div>
            
            <div className="p-4 bg-[var(--color-background)] border-t border-[var(--color-border)] flex justify-end">
               <button 
                onClick={() => setLogsAbertos(null)}
                className="px-6 py-2 bg-[var(--color-surface)] hover:bg-[var(--color-surface-hover)] text-white rounded-xl text-sm font-bold transition-all"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
