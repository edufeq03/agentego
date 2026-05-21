"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Sliders, Plus, Trash2, Edit2, ArrowUp, ArrowDown, Check, AlertCircle, Info, HelpCircle, Save, X, ToggleLeft, ToggleRight } from "lucide-react";

interface CampoCustomizado {
  id: string;
  chave: string;
  label: string;
  tipo: string; // 'texto', 'numero', 'booleano', 'opcao_unica'
  obrigatorio: boolean;
  opcoes?: string[] | null;
  ordem: number;
  ativo: boolean;
  dependencias?: Record<string, string[]> | null;
}

export default function TriagemConfigPage() {
  const [fields, setFields] = useState<CampoCustomizado[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Form State
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [label, setLabel] = useState("");
  const [chave, setChave] = useState("");
  const [tipo, setTipo] = useState("texto");
  const [obrigatorio, setObrigatorio] = useState(false);
  const [opcoesText, setOpcoesText] = useState("");
  const [ativo, setAtivo] = useState(true);

  // Dependencias Form State
  const [temDependencia, setTemDependencia] = useState(false);
  const [depChave, setDepChave] = useState("");
  const [depValores, setDepValores] = useState("");

  // Auto-slugification flag
  const [autoSlug, setAutoSlug] = useState(true);

  useEffect(() => {
    fetchFields();
  }, []);

  async function fetchFields() {
    try {
      setLoading(true);
      const response = await api.get("dashboard/marketing/triage/fields");
      setFields(response.data);
    } catch (error: any) {
      console.error("Erro ao carregar campos de triagem:", error);
      setErrorMsg("Não foi possível carregar os campos de triagem.");
    } finally {
      setLoading(false);
    }
  }

  // Handle auto-slugifying the Label to Chave
  function handleLabelChange(value: string) {
    setLabel(value);
    if (autoSlug && !editingFieldId) {
      const slug = value
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "") // remove acentos
        .replace(/[^a-z0-9\s-_]/g, "") // remove caracteres especiais
        .trim()
        .replace(/\s+/g, "_") // espaços para underline
        .slice(0, 30);
      setChave(slug);
    }
  }

  // Quick Inline Toggle for Ativo/Obrigatorio
  async function handleToggle(field: CampoCustomizado, property: "ativo" | "obrigatorio") {
    try {
      const updatedValue = !field[property];
      const payload = {
        chave: field.chave,
        label: field.label,
        tipo: field.tipo,
        obrigatorio: property === "obrigatorio" ? updatedValue : field.obrigatorio,
        opcoes: field.opcoes,
        ordem: field.ordem,
        ativo: property === "ativo" ? updatedValue : field.ativo,
        dependencias: field.dependencias,
      };

      await api.put(`dashboard/marketing/triage/fields/${field.id}`, payload);
      
      // Update state local to prevent flicker
      setFields(prev =>
        prev.map(f => (f.id === field.id ? { ...f, [property]: updatedValue } : f))
      );
      
      showToast(`Campo "${field.label}" atualizado com sucesso!`);
    } catch (error: any) {
      console.error("Erro ao atualizar campo via toggle:", error);
      setErrorMsg("Ocorreu um erro ao salvar a alteração.");
    }
  }

  // Quick Order Swap (Up/Down)
  async function handleMove(index: number, direction: "up" | "down") {
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= fields.length) return;

    try {
      const currentField = fields[index];
      const targetField = fields[targetIndex];

      // Swap orders
      const currentOrder = currentField.ordem;
      const targetOrder = targetField.ordem;

      // Make API calls in parallel
      await Promise.all([
        api.put(`dashboard/marketing/triage/fields/${currentField.id}`, {
          chave: currentField.chave,
          label: currentField.label,
          tipo: currentField.tipo,
          obrigatorio: currentField.obrigatorio,
          opcoes: currentField.opcoes,
          ordem: targetOrder,
          ativo: currentField.ativo,
          dependencias: currentField.dependencias,
        }),
        api.put(`dashboard/marketing/triage/fields/${targetField.id}`, {
          chave: targetField.chave,
          label: targetField.label,
          tipo: targetField.tipo,
          obrigatorio: targetField.obrigatorio,
          opcoes: targetField.opcoes,
          ordem: currentOrder,
          ativo: targetField.ativo,
          dependencias: targetField.dependencias,
        })
      ]);

      // Re-fetch sorted list
      await fetchFields();
      showToast("Ordem dos campos redefinida!");
    } catch (error: any) {
      console.error("Erro ao mover campo:", error);
      setErrorMsg("Não foi possível salvar a nova ordem.");
    }
  }

  // Submit form for creation or update
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!label.trim() || !chave.trim()) {
      setErrorMsg("Preencha o rótulo e a chave técnica.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg("");
      setSuccessMsg("");

      // Parse comma-separated options list
      let parsedOptions: string[] | null = null;
      if (tipo === "opcao_unica") {
        parsedOptions = opcoesText
          .split(",")
          .map(s => s.trim())
          .filter(Boolean);
        
        if (!parsedOptions.length) {
          setErrorMsg("Para o tipo 'Opções de Seleção', forneça ao menos uma opção.");
          setSubmitting(false);
          return;
        }
      }

      let dependenciasPayload: Record<string, string[]> | null = null;
      if (temDependencia && depChave) {
        const parsedVals = depValores
          .split(",")
          .map(v => v.trim())
          .filter(Boolean);
        if (parsedVals.length > 0) {
          dependenciasPayload = {
            [depChave]: parsedVals
          };
        }
      }

      const payload = {
        chave: chave.trim().toLowerCase().replace(/\s+/g, "_"),
        label: label.trim(),
        tipo,
        obrigatorio,
        opcoes: parsedOptions,
        ordem: editingFieldId 
          ? fields.find(f => f.id === editingFieldId)?.ordem || 0 
          : (fields.length > 0 ? Math.max(...fields.map(f => f.ordem)) + 10 : 10),
        ativo,
        dependencias: dependenciasPayload,
      };

      if (editingFieldId) {
        await api.put(`dashboard/marketing/triage/fields/${editingFieldId}`, payload);
        showToast("Campo atualizado com sucesso!");
      } else {
        await api.post("dashboard/marketing/triage/fields", payload);
        showToast("Novo campo cadastrado com sucesso!");
      }

      // Reset form
      handleCancelEdit();
      await fetchFields();
    } catch (error: any) {
      console.error("Erro ao salvar campo:", error);
      const msg = error.response?.data?.detail || "Erro ao salvar campo de triagem.";
      setErrorMsg(msg);
    } finally {
      setSubmitting(false);
    }
  }

  // Set form values for editing
  function handleStartEdit(field: CampoCustomizado) {
    setEditingFieldId(field.id);
    setLabel(field.label);
    setChave(field.chave);
    setTipo(field.tipo);
    setObrigatorio(field.obrigatorio);
    setAtivo(field.ativo);
    setOpcoesText(field.opcoes ? field.opcoes.join(", ") : "");
    setAutoSlug(false); // don't auto-slugify existing fields

    if (field.dependencias && Object.keys(field.dependencias).length > 0) {
      const firstKey = Object.keys(field.dependencias)[0];
      setTemDependencia(true);
      setDepChave(firstKey);
      setDepValores(field.dependencias[firstKey].join(", "));
    } else {
      setTemDependencia(false);
      setDepChave("");
      setDepValores("");
    }
  }

  // Cancel edit mode
  function handleCancelEdit() {
    setEditingFieldId(null);
    setLabel("");
    setChave("");
    setTipo("texto");
    setObrigatorio(false);
    setAtivo(true);
    setOpcoesText("");
    setAutoSlug(true);
    setErrorMsg("");
    setTemDependencia(false);
    setDepChave("");
    setDepValores("");
  }

  // Delete field
  async function handleDelete(field: CampoCustomizado) {
    if (!confirm(`Tem certeza de que deseja excluir o campo "${field.label}"?`)) return;

    try {
      setErrorMsg("");
      await api.delete(`dashboard/marketing/triage/fields/${field.id}`);
      showToast("Campo excluído com sucesso!");
      await fetchFields();
    } catch (error: any) {
      console.error("Erro ao excluir campo:", error);
      setErrorMsg("Ocorreu um erro ao excluir o campo.");
    }
  }

  // Display micro success notifications
  function showToast(msg: string) {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 4000);
  }

  if (loading && fields.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--color-brand-500)]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Sliders className="text-[var(--color-brand-500)] h-7 w-7" /> Triagem da IA (Campos Dinâmicos)
        </h2>
        <p className="text-[var(--color-foreground-muted)] mt-1">
          Configure as informações que a Inteligência Artificial deve perguntar no WhatsApp. O robô atualiza o banco em tempo real conforme as tags são geradas no diálogo.
        </p>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="flex items-center gap-3 p-4 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-emerald-400 animate-fadeIn">
          <Check className="h-5 w-5 shrink-0" />
          <span className="text-sm font-medium">{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center gap-3 p-4 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span className="text-sm font-medium">{errorMsg}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Fields List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-panel p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">Campos da Triagem Ativa</h3>
              <span className="text-xs px-2.5 py-1 bg-[rgba(59,130,246,0.1)] border border-blue-500/20 text-blue-400 rounded-full font-medium">
                {fields.length} {fields.length === 1 ? "campo" : "campos"}
              </span>
            </div>

            {fields.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center text-[var(--color-foreground-muted)] border border-dashed border-white/10 rounded-xl">
                <Sliders className="h-12 w-12 mb-3 stroke-1" />
                <p className="text-sm">Nenhum campo de triagem configurado.</p>
                <p className="text-xs mt-1">Utilize o formulário ao lado para cadastrar seu primeiro campo customizado.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {fields.map((field, index) => (
                  <div
                    key={field.id}
                    className={`flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-xl gap-4 transition-all duration-300 ${
                      editingFieldId === field.id
                        ? "bg-[rgba(139,92,246,0.06)] border-[var(--color-brand-500)] shadow-lg shadow-purple-950/20"
                        : field.ativo
                        ? "bg-white/[0.02] border-white/5 hover:bg-white/[0.04]"
                        : "bg-white/[0.01] border-white/5 opacity-60"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-white">{field.label}</span>
                          {field.obrigatorio && (
                            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-red-950/40 border border-red-500/30 text-red-400 rounded-md">
                              Obrigatório
                            </span>
                          )}
                          {!field.ativo && (
                            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-white/5 border border-white/10 text-[var(--color-foreground-muted)] rounded-md">
                              Inativo
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--color-foreground-muted)]">
                          <span>Chave: <code className="bg-white/5 px-1 py-0.5 rounded text-white font-mono">{field.chave}</code></span>
                          <span className="w-1.5 h-1.5 rounded-full bg-white/15 hidden sm:inline" />
                          <span className="capitalize">Tipo: {field.tipo === "opcao_unica" ? "Opções de Seleção" : field.tipo === "booleano" ? "Sim / Não" : field.tipo}</span>
                        </div>
                        {field.tipo === "opcao_unica" && field.opcoes && (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {field.opcoes.map((opt, oIdx) => (
                              <span key={oIdx} className="text-[10px] px-2 py-0.5 bg-white/5 border border-white/5 rounded text-white/80">
                                {opt}
                              </span>
                            ))}
                          </div>
                        )}
                        {field.dependencias && Object.keys(field.dependencias).length > 0 && (
                          <div className="flex items-center gap-1.5 mt-2 text-[10px] text-amber-400 bg-amber-950/20 border border-amber-500/20 px-2.5 py-1 rounded-lg w-fit">
                            <Info className="h-3.5 w-3.5 shrink-0" />
                            <span>
                              Depende de: <code className="bg-white/5 px-1 py-0.5 rounded text-white font-mono font-bold">{Object.keys(field.dependencias)[0]}</code> = <strong className="text-white">{field.dependencias[Object.keys(field.dependencias)[0]].join(", ")}</strong>
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center">
                      {/* Move buttons */}
                      <div className="flex items-center border border-white/5 rounded-lg bg-white/[0.02]">
                        <button
                          onClick={() => handleMove(index, "up")}
                          disabled={index === 0}
                          className="p-1.5 text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:hover:bg-transparent rounded-l-lg transition-colors"
                          title="Subir"
                        >
                          <ArrowUp className="h-4 w-4" />
                        </button>
                        <div className="w-[1px] h-4 bg-white/5" />
                        <button
                          onClick={() => handleMove(index, "down")}
                          disabled={index === fields.length - 1}
                          className="p-1.5 text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:hover:bg-transparent rounded-r-lg transition-colors"
                          title="Descer"
                        >
                          <ArrowDown className="h-4 w-4" />
                        </button>
                      </div>

                      {/* Quick toggles */}
                      <button
                        onClick={() => handleToggle(field, "obrigatorio")}
                        className={`p-1.5 rounded-lg border transition-colors flex items-center gap-1 text-xs font-medium ${
                          field.obrigatorio 
                            ? "bg-red-950/20 border-red-500/20 text-red-400 hover:bg-red-950/40"
                            : "bg-white/[0.02] border-white/5 text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/5"
                        }`}
                        title={field.obrigatorio ? "Tornar Opcional" : "Tornar Obrigatório"}
                      >
                        *
                      </button>

                      <button
                        onClick={() => handleToggle(field, "ativo")}
                        className="p-1.5 rounded-lg transition-colors"
                        title={field.ativo ? "Desativar" : "Ativar"}
                      >
                        {field.ativo ? (
                          <ToggleRight className="h-7 w-7 text-[var(--color-brand-500)]" />
                        ) : (
                          <ToggleLeft className="h-7 w-7 text-[var(--color-foreground-muted)]" />
                        )}
                      </button>

                      {/* CRUD Buttons */}
                      <button
                        onClick={() => handleStartEdit(field)}
                        className="p-1.5 rounded-lg border border-white/5 bg-white/[0.02] text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/5 transition-colors"
                        title="Editar"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(field)}
                        className="p-1.5 rounded-lg border border-red-950/30 bg-red-950/10 text-red-400 hover:bg-red-900/30 transition-colors"
                        title="Excluir"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Creator / Editor Form */}
        <div className="space-y-4">
          <form onSubmit={handleSubmit} className="glass-panel p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2 border-b border-white/5 pb-3">
              <Plus className="text-[var(--color-brand-500)] h-5 w-5" /> 
              {editingFieldId ? "Editar Campo de Triagem" : "Adicionar Campo de Triagem"}
            </h3>

            {/* Input Label */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-white/90">
                Rótulo / Pergunta (Label) <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                placeholder="Ex: Placa do Carro"
                value={label}
                onChange={(e) => handleLabelChange(e.target.value)}
                className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] transition-all"
                required
              />
            </div>

            {/* Input Technical Key */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold text-white/90">
                  Chave Técnica (Database key) <span className="text-red-500">*</span>
                </label>
                {!editingFieldId && (
                  <button
                    type="button"
                    onClick={() => setAutoSlug(prev => !prev)}
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded transition-colors ${
                      autoSlug ? "bg-purple-950/40 text-purple-400 border border-purple-500/20" : "bg-white/5 text-[var(--color-foreground-muted)] border border-white/15"
                    }`}
                  >
                    Auto-Slug: {autoSlug ? "Ativo" : "Inativo"}
                  </button>
                )}
              </div>
              <input
                type="text"
                placeholder="Ex: placa_carro"
                value={chave}
                onChange={(e) => {
                  setChave(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""));
                  setAutoSlug(false);
                }}
                disabled={!!editingFieldId}
                className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] disabled:opacity-40 disabled:cursor-not-allowed font-mono transition-all"
                required
              />
              <p className="text-[10px] text-[var(--color-foreground-muted)] flex items-start gap-1 mt-1">
                <Info className="h-3 w-3 shrink-0 text-blue-400 mt-0.5" />
                <span>Chave única para armazenar a resposta no banco. Use apenas letras e underlays.</span>
              </p>
            </div>

            {/* Type Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-white/90">Tipo de Dado</label>
              <select
                value={tipo}
                onChange={(e) => setTipo(e.target.value)}
                className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] transition-all [&>option]:bg-zinc-950"
              >
                <option value="texto">Texto (Genérico)</option>
                <option value="numero">Número (Inteiro)</option>
                <option value="booleano">Sim / Não (Booleano)</option>
                <option value="opcao_unica">Opções de Seleção (Única Escolha)</option>
              </select>
            </div>

            {/* Selection Options Input */}
            {tipo === "opcao_unica" && (
              <div className="space-y-1.5 animate-fadeIn">
                <label className="text-xs font-semibold text-white/90">Opções Disponíveis (Separadas por vírgula)</label>
                <textarea
                  placeholder="Ex: PME Saúde, Individual, Odonto"
                  value={opcoesText}
                  onChange={(e) => setOpcoesText(e.target.value)}
                  rows={2}
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] transition-all resize-none"
                  required
                />
                <p className="text-[10px] text-[var(--color-foreground-muted)]">
                  Crie as opções que o assistente do robô oferecerá para o cliente escolher.
                </p>
              </div>
            )}

            {/* Dynamic Dependency Configuration */}
            <div className="space-y-3 pt-3 border-t border-white/5">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold text-white">Depende de outro campo?</span>
                  <p className="text-[9px] text-[var(--color-foreground-muted)]">Exibir apenas condicionalmente</p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setTemDependencia(!temDependencia);
                    if (!temDependencia && fields.length > 0) {
                      // Autoselect first possible field that is not the current one
                      const possibleFields = fields.filter(f => f.id !== editingFieldId);
                      if (possibleFields.length > 0) {
                        setDepChave(possibleFields[0].chave);
                      }
                    }
                  }}
                  className="focus:outline-none bg-transparent border-0 p-0"
                >
                  {temDependencia ? (
                    <ToggleRight className="h-8 w-8 text-[var(--color-brand-500)]" />
                  ) : (
                    <ToggleLeft className="h-8 w-8 text-[var(--color-foreground-muted)]" />
                  )}
                </button>
              </div>

              {temDependencia && (
                <div className="space-y-3 p-3 bg-white/[0.02] border border-white/5 rounded-xl animate-fadeIn">
                  {/* Select field parent */}
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-white/80">Selecionar Campo Pai</label>
                    <select
                      value={depChave}
                      onChange={(e) => setDepChave(e.target.value)}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[var(--color-brand-500)] transition-all [&>option]:bg-zinc-950"
                      required={temDependencia}
                    >
                      <option value="">Selecione um campo...</option>
                      {fields
                        .filter(f => f.id !== editingFieldId)
                        .map(f => (
                          <option key={f.id} value={f.chave}>
                            {f.label} ({f.chave})
                          </option>
                        ))
                      }
                    </select>
                  </div>

                  {/* Input values that trigger this field */}
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-white/80">Valores Ativadores (Separados por vírgula)</label>
                    <input
                      type="text"
                      placeholder="Ex: Carro, Moto"
                      value={depValores}
                      onChange={(e) => setDepValores(e.target.value)}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[var(--color-brand-500)] transition-all"
                      required={temDependencia}
                    />
                    <p className="text-[9px] text-[var(--color-foreground-muted)]">
                      O campo só aparecerá se o lead responder um desses valores no campo selecionado.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Toggles */}
            <div className="grid grid-cols-2 gap-4 py-2 border-t border-b border-white/5">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold text-white">Obrigatório</span>
                  <p className="text-[9px] text-[var(--color-foreground-muted)]">IA deve coletar</p>
                </div>
                <button
                  type="button"
                  onClick={() => setObrigatorio(!obrigatorio)}
                  className="focus:outline-none"
                >
                  {obrigatorio ? (
                    <ToggleRight className="h-8 w-8 text-[var(--color-brand-500)]" />
                  ) : (
                    <ToggleLeft className="h-8 w-8 text-[var(--color-foreground-muted)]" />
                  )}
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold text-white">Ativo</span>
                  <p className="text-[9px] text-[var(--color-foreground-muted)]">Habilitar no fluxo</p>
                </div>
                <button
                  type="button"
                  onClick={() => setAtivo(!ativo)}
                  className="focus:outline-none"
                >
                  {ativo ? (
                    <ToggleRight className="h-8 w-8 text-[var(--color-brand-500)]" />
                  ) : (
                    <ToggleLeft className="h-8 w-8 text-[var(--color-foreground-muted)]" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit / Cancel Buttons */}
            <div className="flex items-center gap-2 pt-2">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white text-sm font-semibold rounded-xl py-2.5 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] active:scale-[0.99] transition-all"
              >
                <Save className="h-4 w-4" />
                {editingFieldId ? "Salvar Alterações" : "Cadastrar Campo"}
              </button>

              {editingFieldId && (
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="p-2.5 bg-white/5 border border-white/10 hover:bg-white/10 rounded-xl text-white transition-all"
                  title="Cancelar Edição"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
