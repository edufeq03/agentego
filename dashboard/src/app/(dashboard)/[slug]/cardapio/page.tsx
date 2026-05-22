"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Plus, Edit2, Trash2, ToggleLeft, ToggleRight, QrCode, Clipboard, Check, Eye } from "lucide-react";
import api from "@/lib/api";

interface CardapioItem {
  id: string;
  categoria: string;
  nome: string;
  descricao: string | null;
  preco: number;
  disponivel: boolean;
  ordem: number;
}

export default function CardapioPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [itens, setItens] = useState<CardapioItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("todos");
  const [activeMenuTab, setActiveMenuTab] = useState<"cardapio" | "mesas">("cardapio");

  // Modal de Adicionar / Editar
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<CardapioItem | null>(null);
  const [formData, setFormData] = useState({
    categoria: "Lanches",
    nome: "",
    descricao: "",
    preco: "",
    ordem: "0",
    disponivel: true,
  });

  // Estado de Mesas/QR Code
  const [mesaInput, setMesaInput] = useState("");
  const [mesaQrLink, setMesaQrLink] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    carregarCardapio();
  }, [slug]);

  async function carregarCardapio() {
    try {
      setLoading(true);
      const response = await api.get("dashboard/lanchonete/cardapio");
      setItens(response.data);
    } catch (error) {
      console.error("Erro ao carregar cardápio:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleDisponibilidade(item: CardapioItem) {
    try {
      // Otimização pessimista com update visual imediato (otimista)
      setItens(prev => prev.map(i => i.id === item.id ? { ...i, disponivel: !i.disponivel } : i));
      await api.patch(`dashboard/lanchonete/cardapio/${item.id}/disponibilidade`);
    } catch (error) {
      console.error("Erro ao alterar disponibilidade:", error);
      // Reverter se der erro
      carregarCardapio();
    }
  }

  async function handleDeletarItem(item_id: string) {
    if (!confirm("Tem certeza que deseja remover este item do cardápio?")) return;
    try {
      await api.delete(`dashboard/lanchonete/cardapio/${item_id}`);
      setItens(prev => prev.filter(i => i.id !== item_id));
    } catch (error) {
      console.error("Erro ao remover item:", error);
    }
  }

  function handleOpenAddModal() {
    setEditingItem(null);
    setFormData({
      categoria: "Lanches",
      nome: "",
      descricao: "",
      preco: "",
      ordem: "0",
      disponivel: true,
    });
    setIsModalOpen(true);
  }

  function handleOpenEditModal(item: CardapioItem) {
    setEditingItem(item);
    setFormData({
      categoria: item.categoria,
      nome: item.nome,
      descricao: item.descricao || "",
      preco: item.preco.toString(),
      ordem: item.ordem.toString(),
      disponivel: item.disponivel,
    });
    setIsModalOpen(true);
  }

  async function handleSaveItem(e: React.FormEvent) {
    e.preventDefault();
    try {
      const payload = {
        categoria: formData.categoria,
        nome: formData.nome,
        preco: parseFloat(formData.preco),
        descricao: formData.descricao || null,
        disponivel: formData.disponivel,
        ordem: parseInt(formData.ordem) || 0,
      };

      if (editingItem) {
        await api.put(`dashboard/lanchonete/cardapio/${editingItem.id}`, payload);
      } else {
        await api.post("dashboard/lanchonete/cardapio", payload);
      }

      setIsModalOpen(false);
      carregarCardapio();
    } catch (error) {
      console.error("Erro ao salvar produto:", error);
      alert("Erro ao salvar o item do cardápio. Verifique os dados informados.");
    }
  }

  async function handleGerarQrMesa(e: React.FormEvent) {
    e.preventDefault();
    if (!mesaInput || isNaN(parseInt(mesaInput))) {
      alert("Por favor, informe um número de mesa válido.");
      return;
    }
    try {
      const response = await api.get("dashboard/lanchonete/mesa/qrcode", {
        params: { numero_mesa: parseInt(mesaInput) }
      });
      setMesaQrLink(response.data.link_whatsapp);
    } catch (error) {
      console.error("Erro ao gerar QR Code:", error);
    }
  }

  function handleCopiarLink() {
    navigator.clipboard.writeText(mesaQrLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const categorias = ["Lanches", "Acompanhamentos", "Bebidas", "Sobremesas"];
  const filteredItens = activeTab === "todos" 
    ? itens 
    : itens.filter(item => item.categoria.toLowerCase() === activeTab.toLowerCase());

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/40 p-6 rounded-2xl border border-slate-800 backdrop-blur-md">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Gestão do Cardápio</h2>
          <p className="text-slate-400 text-sm">Gerencie o cardápio que a IA apresenta e configure os QR Codes de atendimento local nas mesas.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveMenuTab("cardapio")}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeMenuTab === "cardapio"
                ? "bg-[var(--color-brand-500)] text-white shadow-lg shadow-[var(--color-brand-500)]/20"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            📋 Menu Cardápio
          </button>
          <button
            onClick={() => setActiveMenuTab("mesas")}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeMenuTab === "mesas"
                ? "bg-[var(--color-brand-500)] text-white shadow-lg shadow-[var(--color-brand-500)]/20"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            🍽️ Mesas & QR Codes
          </button>
        </div>
      </div>

      {activeMenuTab === "cardapio" ? (
        <>
          {/* Tabs e Adicionar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            {/* Category Filter Tabs */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setActiveTab("todos")}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === "todos"
                    ? "bg-white/10 text-white border border-white/20"
                    : "text-slate-400 hover:text-white bg-slate-900/20"
                }`}
              >
                Todos ({itens.length})
              </button>
              {categorias.map((cat) => {
                const count = itens.filter(i => i.categoria.toLowerCase() === cat.toLowerCase()).length;
                return (
                  <button
                    key={cat}
                    onClick={() => setActiveTab(cat)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      activeTab.toLowerCase() === cat.toLowerCase()
                        ? "bg-white/10 text-white border border-white/20"
                        : "text-slate-400 hover:text-white bg-slate-900/20"
                    }`}
                  >
                    {cat} ({count})
                  </button>
                );
              })}
            </div>

            <button
              onClick={handleOpenAddModal}
              className="bg-[var(--color-brand-500)] text-white px-4 py-2.5 rounded-xl font-medium hover:bg-[var(--color-brand-600)] transition-colors flex items-center gap-2 self-start shadow-lg shadow-[var(--color-brand-500)]/10"
            >
              <Plus size={18} /> Adicionar Produto
            </button>
          </div>

          {/* Grid de Itens */}
          {loading ? (
            <div className="text-center py-12 text-slate-400">Carregando cardápio...</div>
          ) : filteredItens.length === 0 ? (
            <div className="text-center py-16 bg-slate-900/10 border border-dashed border-slate-800 rounded-2xl text-slate-400">
              Nenhum produto cadastrado nesta categoria.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredItens.map((item) => (
                <div
                  key={item.id}
                  className={`bg-slate-900/20 border rounded-2xl p-5 flex flex-col justify-between transition-all ${
                    item.disponivel 
                      ? "border-slate-800 hover:border-slate-700" 
                      : "border-red-950/40 bg-red-950/5 opacity-70"
                  }`}
                >
                  <div>
                    <div className="flex justify-between items-start gap-2 mb-2">
                      <span className="text-xs px-2.5 py-1 bg-slate-800 text-slate-300 rounded-full font-semibold">
                        {item.categoria}
                      </span>
                      <span className="text-lg font-bold text-[var(--color-brand-400)]">
                        R$ {item.preco.toFixed(2)}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
                      {item.nome}
                      {!item.disponivel && (
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-red-500/20 text-red-400 rounded-full border border-red-500/20">
                          Pausado
                        </span>
                      )}
                    </h3>
                    <p className="text-slate-400 text-sm line-clamp-2 mb-4 leading-relaxed">
                      {item.descricao || "Sem descrição cadastrada."}
                    </p>
                  </div>

                  <div className="flex items-center justify-between border-t border-slate-800/60 pt-4 mt-auto">
                    <button
                      onClick={() => handleToggleDisponibilidade(item)}
                      className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
                      title={item.disponivel ? "Pausar vendas" : "Ativar vendas"}
                    >
                      {item.disponivel ? (
                        <>
                          <ToggleRight className="text-emerald-500" size={24} />
                          <span>Ativo</span>
                        </>
                      ) : (
                        <>
                          <ToggleLeft className="text-slate-600" size={24} />
                          <span>Indisponível</span>
                        </>
                      )}
                    </button>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleOpenEditModal(item)}
                        className="p-2 text-slate-400 hover:text-white bg-slate-800/40 hover:bg-slate-800 rounded-lg transition-all"
                        title="Editar"
                      >
                        <Edit2 size={15} />
                      </button>
                      <button
                        onClick={() => handleDeletarItem(item.id)}
                        className="p-2 text-slate-400 hover:text-red-400 bg-slate-850 hover:bg-red-500/10 rounded-lg transition-all"
                        title="Excluir"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        /* Aba de Mesas & QR Codes */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-slate-900/20 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-3 text-white font-bold text-lg mb-2">
              <QrCode className="text-[var(--color-brand-400)]" size={24} />
              Gerar QR Code de Mesa
            </div>
            <p className="text-slate-400 text-sm leading-relaxed">
              Digite o número da mesa abaixo para gerar o link e o QR Code. Ao escanear o QR Code impresso no papel, o cliente inicia uma conversa com o bot no WhatsApp identificando imediatamente em qual mesa está acomodado!
            </p>

            <form onSubmit={handleGerarQrMesa} className="flex gap-3 mt-4">
              <input
                type="number"
                value={mesaInput}
                onChange={(e) => setMesaInput(e.target.value)}
                placeholder="Ex: 5"
                className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-600 w-full focus:outline-none focus:border-[var(--color-brand-500)]"
              />
              <button
                type="submit"
                className="bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white px-5 rounded-xl font-semibold transition-colors shrink-0 shadow-lg shadow-[var(--color-brand-500)]/15"
              >
                Gerar
              </button>
            </form>
          </div>

          <div className="bg-slate-900/20 border border-slate-800 rounded-2xl p-6 flex flex-col items-center justify-center min-h-[300px]">
            {mesaQrLink ? (
              <div className="space-y-6 w-full flex flex-col items-center">
                <div className="bg-white p-4 rounded-2xl shadow-xl shadow-black/30">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(mesaQrLink)}`}
                    alt={`QR Code Mesa ${mesaInput}`}
                    className="w-[180px] h-[180px]"
                  />
                </div>
                <div className="text-center">
                  <h4 className="text-white font-bold text-lg">Mesa {mesaInput}</h4>
                  <p className="text-slate-400 text-xs mt-1">Escaneie com a câmera do celular para testar</p>
                </div>
                <div className="flex gap-2 w-full max-w-sm">
                  <button
                    onClick={handleCopiarLink}
                    className="flex-1 bg-slate-800 hover:bg-slate-700 text-white py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2"
                  >
                    {copied ? (
                      <>
                        <Check size={16} className="text-emerald-400" /> Copiado!
                      </>
                    ) : (
                      <>
                        <Clipboard size={16} /> Copiar Link
                      </>
                    )}
                  </button>
                  <a
                    href={mesaQrLink}
                    target="_blank"
                    rel="noreferrer"
                    className="bg-slate-800 hover:bg-slate-700 text-white p-2.5 rounded-xl text-sm font-semibold transition-all flex items-center justify-center"
                    title="Testar Link"
                  >
                    <Eye size={18} />
                  </a>
                </div>
              </div>
            ) : (
              <div className="text-center space-y-2 text-slate-500">
                <QrCode size={48} className="mx-auto text-slate-700 stroke-[1.5]" />
                <p className="text-sm">Preencha o número da mesa e clique em Gerar para ver o QR Code pronto.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal Adicionar / Editar */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800">
              <h3 className="text-white font-bold text-lg">
                {editingItem ? "✏️ Editar Produto" : "➕ Adicionar Produto ao Cardápio"}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveItem} className="p-6 space-y-4">
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1">Categoria</label>
                <select
                  value={formData.categoria}
                  onChange={(e) => setFormData(prev => ({ ...prev, categoria: e.target.value }))}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white w-full focus:outline-none focus:border-[var(--color-brand-500)]"
                >
                  {categorias.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1">Nome do Produto</label>
                <input
                  type="text"
                  required
                  value={formData.nome}
                  onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                  placeholder="Ex: X-Salada Especial"
                  className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-650 w-full focus:outline-none focus:border-[var(--color-brand-500)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 text-sm font-medium mb-1">Preço (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.preco}
                    onChange={(e) => setFormData(prev => ({ ...prev, preco: e.target.value }))}
                    placeholder="Ex: 22.00"
                    className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-650 w-full focus:outline-none focus:border-[var(--color-brand-500)]"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 text-sm font-medium mb-1">Ordem de Exibição</label>
                  <input
                    type="number"
                    value={formData.ordem}
                    onChange={(e) => setFormData(prev => ({ ...prev, ordem: e.target.value }))}
                    placeholder="Ex: 0"
                    className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-650 w-full focus:outline-none focus:border-[var(--color-brand-500)]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1">Descrição</label>
                <textarea
                  value={formData.descricao}
                  onChange={(e) => setFormData(prev => ({ ...prev, descricao: e.target.value }))}
                  placeholder="Descreva os ingredientes de forma apetitosa..."
                  rows={3}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-650 w-full focus:outline-none focus:border-[var(--color-brand-500)] resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-350 px-4 py-2.5 rounded-xl font-semibold transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white px-5 py-2.5 rounded-xl font-semibold transition-colors shadow-lg shadow-[var(--color-brand-500)]/15"
                >
                  Salvar Produto
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
