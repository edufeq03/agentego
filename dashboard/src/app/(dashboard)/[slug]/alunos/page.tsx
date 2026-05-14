"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { 
  Users, 
  Upload, 
  Trash2, 
  Search, 
  Calendar, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  FileSpreadsheet,
  X
} from "lucide-react";
import api from "@/lib/api";

interface Membro {
  id: string;
  nome: string;
  telefone: string;
  plano_nome: string;
  data_vencimento: string;
  dias_restantes: number;
  status: 'ativo' | 'vencendo' | 'vencido';
}

export default function AlunosPage() {
  const params = useParams();
  const slug = params?.slug as string;
  
  const [membros, setMembros] = useState<Membro[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  useEffect(() => {
    fetchMembros();
  }, []);

  async function fetchMembros() {
    try {
      const response = await api.get('dashboard/membros');
      setMembros(response.data);
    } catch (error) {
      console.error("Erro ao carregar membros:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Tem certeza que deseja remover este aluno?")) return;
    try {
      await api.delete(`dashboard/membros/${id}`);
      setMembros(membros.filter(m => m.id !== id));
    } catch (error) {
      alert("Erro ao remover aluno.");
    }
  }

  async function handleImport(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;

    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('dashboard/membros/importar-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setImportResult(response.data);
      fetchMembros();
    } catch (error) {
      alert("Erro na importação. Verifique o formato do CSV.");
    } finally {
      setImporting(false);
    }
  }

  const filteredMembros = membros.filter(m => 
    m.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.telefone.includes(searchTerm)
  );

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Gestão de Alunos</h2>
          <p className="text-[var(--color-foreground-muted)] mt-1">
            Gerencie sua base de alunos e automatize avisos de vencimento.
          </p>
        </div>
        <button 
          onClick={() => {
            setIsImportModalOpen(true);
            setImportResult(null);
            setFile(null);
          }}
          className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-xl font-semibold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
        >
          <Upload size={18} />
          Importar CSV
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl">
          <div className="flex items-center gap-4">
            <div className="bg-emerald-500/10 p-3 rounded-xl text-emerald-500">
              <CheckCircle2 size={24} />
            </div>
            <div>
              <p className="text-sm text-[var(--color-foreground-muted)]">Ativos</p>
              <p className="text-2xl font-bold text-white">{membros.filter(m => m.status === 'ativo').length}</p>
            </div>
          </div>
        </div>
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl">
          <div className="flex items-center gap-4">
            <div className="bg-amber-500/10 p-3 rounded-xl text-amber-500">
              <Clock size={24} />
            </div>
            <div>
              <p className="text-sm text-[var(--color-foreground-muted)]">Vencendo (7 dias)</p>
              <p className="text-2xl font-bold text-white">{membros.filter(m => m.status === 'vencendo').length}</p>
            </div>
          </div>
        </div>
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl">
          <div className="flex items-center gap-4">
            <div className="bg-red-500/10 p-3 rounded-xl text-red-500">
              <AlertCircle size={24} />
            </div>
            <div>
              <p className="text-sm text-[var(--color-foreground-muted)]">Vencidos</p>
              <p className="text-2xl font-bold text-white">{membros.filter(m => m.status === 'vencido').length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-[var(--color-border)] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)]" size={18} />
            <input 
              type="text"
              placeholder="Buscar por nome ou telefone..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-xl py-2.5 pl-10 pr-4 text-white placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-500)]/50 transition-all"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-[var(--color-surface-hover)]/50 text-[var(--color-foreground-muted)] text-sm font-medium">
                <th className="px-6 py-4">Aluno</th>
                <th className="px-6 py-4">Telefone</th>
                <th className="px-6 py-4">Plano</th>
                <th className="px-6 py-4">Vencimento</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-[var(--color-foreground-muted)]">
                    Carregando alunos...
                  </td>
                </tr>
              ) : filteredMembros.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-[var(--color-foreground-muted)]">
                    Nenhum aluno encontrado.
                  </td>
                </tr>
              ) : (
                filteredMembros.map((membro) => (
                  <tr key={membro.id} className="hover:bg-[var(--color-surface-hover)]/30 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-[var(--color-brand-500)]/10 flex items-center justify-center text-[var(--color-brand-400)] font-bold">
                          {membro.nome.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-medium text-white">{membro.nome}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-[var(--color-foreground-muted)]">{membro.telefone}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 rounded-md bg-[var(--color-surface-hover)] text-xs font-medium text-[var(--color-foreground-muted)]">
                        {membro.plano_nome || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-[var(--color-foreground-muted)]">
                        <Calendar size={14} />
                        {membro.data_vencimento}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                        membro.status === 'ativo' ? 'bg-emerald-500/10 text-emerald-500' :
                        membro.status === 'vencendo' ? 'bg-amber-500/10 text-amber-500' :
                        'bg-red-500/10 text-red-500'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          membro.status === 'ativo' ? 'bg-emerald-500' :
                          membro.status === 'vencendo' ? 'bg-amber-500' :
                          'bg-red-500'
                        }`} />
                        {membro.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => handleDelete(membro.id)}
                        className="p-2 text-[var(--color-foreground-muted)] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                        title="Remover"
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Importação */}
      {isImportModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => !importing && setIsImportModalOpen(false)} />
          <div className="relative bg-[var(--color-surface)] border border-[var(--color-border)] w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-[var(--color-border)] flex items-center justify-between">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <FileSpreadsheet className="text-[var(--color-brand-400)]" />
                Importar Alunos
              </h3>
              <button 
                onClick={() => setIsImportModalOpen(false)}
                className="text-[var(--color-foreground-muted)] hover:text-white"
                disabled={importing}
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-8">
              {!importResult ? (
                <form onSubmit={handleImport} className="space-y-6">
                  <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                    <p className="text-sm text-blue-400 leading-relaxed">
                      O arquivo CSV deve conter as colunas: <strong>nome</strong>, <strong>celular</strong> e <strong>vencimento</strong> (DD/MM/AAAA).
                    </p>
                  </div>

                  <div className="group relative border-2 border-dashed border-[var(--color-border)] hover:border-[var(--color-brand-500)] rounded-2xl p-10 transition-all text-center">
                    <input 
                      type="file" 
                      accept=".csv"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                    />
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center text-[var(--color-foreground-muted)] group-hover:text-[var(--color-brand-400)] group-hover:bg-[var(--color-brand-500)]/10 transition-all">
                        <Upload size={24} />
                      </div>
                      <div>
                        <p className="text-white font-medium">
                          {file ? file.name : "Clique ou arraste o arquivo CSV"}
                        </p>
                        <p className="text-xs text-[var(--color-foreground-muted)] mt-1">
                          Apenas arquivos .csv são permitidos
                        </p>
                      </div>
                    </div>
                  </div>

                  <button 
                    type="submit"
                    disabled={!file || importing}
                    className="w-full py-3.5 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-bold transition-all shadow-lg shadow-[var(--color-brand-500)]/20"
                  >
                    {importing ? "Processando..." : "Começar Importação"}
                  </button>
                </form>
              ) : (
                <div className="space-y-6">
                  <div className="text-center">
                    <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500 mx-auto mb-4">
                      <CheckCircle2 size={32} />
                    </div>
                    <h4 className="text-xl font-bold text-white">Importação Concluída</h4>
                    <p className="text-[var(--color-foreground-muted)] mt-1">
                      {importResult.importados} novos alunos importados.
                    </p>
                  </div>

                  {importResult.erros && importResult.erros.length > 0 && (
                    <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4 max-h-40 overflow-y-auto">
                      <p className="text-sm font-semibold text-red-400 mb-2">Erros encontrados:</p>
                      <ul className="text-xs text-red-400/80 space-y-1">
                        {importResult.erros.map((err: string, i: number) => (
                          <li key={i}>• {err}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <button 
                    onClick={() => setIsImportModalOpen(false)}
                    className="w-full py-3 bg-[var(--color-surface-hover)] hover:bg-[var(--color-border)] text-white rounded-xl font-bold transition-all"
                  >
                    Fechar
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
