"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Mic, Save, Info, Volume2, Music, UserCircle } from "lucide-react";
import api from "@/lib/api";
import { toast } from "react-hot-toast";

const VOICES = [
  { id: "nova", name: "Nova", gender: "Feminino", desc: "Enérgica e profissional" },
  { id: "shimmer", name: "Shimmer", gender: "Feminino", desc: "Calma e acolhedora" },
  { id: "alloy", name: "Alloy", gender: "Neutro", desc: "Equilibrada e clara" },
  { id: "onyx", name: "Onyx", gender: "Masculino", desc: "Profunda e autoritária" },
  { id: "echo", name: "Echo", gender: "Masculino", desc: "Suave e natural" },
  { id: "fable", name: "Fable", gender: "Masculino", desc: "Expressiva e narrativa" },
];

export default function ConfiguracoesFalaPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState({
    stt_enabled: true,
    tts_enabled: true,
    tts_always: false,
    tts_voice: "nova"
  });

  useEffect(() => {
    async function loadConfig() {
      try {
        const response = await api.get(`/dashboard/configuracoes/${slug}`);
        if (response.data?.config) {
          setConfig({
            stt_enabled: response.data.config.stt_enabled !== false,
            tts_enabled: response.data.config.tts_enabled !== false,
            tts_always: response.data.config.tts_always === true,
            tts_voice: response.data.config.tts_voice || "nova"
          });
        }
      } catch (error) {
        console.error("Erro ao carregar configurações:", error);
        toast.error("Erro ao carregar configurações");
      } finally {
        setLoading(false);
      }
    }
    if (slug) loadConfig();
  }, [slug]);

  async function handleSave() {
    setSaving(true);
    try {
      await api.post(`/dashboard/configuracoes/${slug}`, { config });
      toast.success("Configurações de fala atualizadas!");
    } catch (error) {
      console.error("Erro ao salvar:", error);
      toast.error("Erro ao salvar configurações");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-brand-500)]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Configurações de Fala</h1>
          <p className="text-[var(--color-foreground-muted)]">Personalize como o seu agente ouve e fala com os clientes.</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--color-brand-500)] hover:bg-[var(--color-brand-600)] text-white rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          <Save size={18} />
          {saving ? "Salvando..." : "Salvar Alterações"}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Painel de Ativação */}
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 space-y-6">
          <div className="flex items-center gap-3 mb-2">
            <Mic className="text-[var(--color-brand-400)]" size={20} />
            <h2 className="text-lg font-semibold text-white">Comportamento</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-[var(--color-background)] rounded-lg border border-[var(--color-border)]">
              <div>
                <p className="font-medium text-white">Ouvir Áudios (STT)</p>
                <p className="text-xs text-[var(--color-foreground-muted)]">Transcrever áudios enviados pelos clientes.</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.stt_enabled}
                  onChange={(e) => setConfig({ ...config, stt_enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-brand-500)]"></div>
              </label>
            </div>

            <div className="flex items-center justify-between p-4 bg-[var(--color-background)] rounded-lg border border-[var(--color-border)]">
              <div>
                <p className="font-medium text-white">Responder com Áudio (TTS)</p>
                <p className="text-xs text-[var(--color-foreground-muted)]">Gerar áudio quando o cliente enviar áudio.</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.tts_enabled}
                  onChange={(e) => setConfig({ ...config, tts_enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-brand-500)]"></div>
              </label>
            </div>

            <div className="flex items-center justify-between p-4 bg-[var(--color-background)] rounded-lg border border-[var(--color-border)]">
              <div>
                <p className="font-medium text-white">Sempre Responder com Áudio</p>
                <p className="text-xs text-[var(--color-foreground-muted)]">Mesmo que o cliente mande texto, o robô responde áudio.</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.tts_always}
                  onChange={(e) => setConfig({ ...config, tts_always: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-brand-500)]"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Seleção de Voz */}
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 space-y-6">
          <div className="flex items-center gap-3 mb-2">
            <UserCircle className="text-[var(--color-brand-400)]" size={20} />
            <h2 className="text-lg font-semibold text-white">Voz do Agente</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {VOICES.map((voice) => (
              <button
                key={voice.id}
                onClick={() => setConfig({ ...config, tts_voice: voice.id })}
                className={`flex flex-col text-left p-3 rounded-lg border transition-all ${
                  config.tts_voice === voice.id
                    ? "border-[var(--color-brand-500)] bg-[var(--color-brand-500)]/10 ring-1 ring-[var(--color-brand-500)]"
                    : "border-[var(--color-border)] bg-[var(--color-background)] hover:border-[var(--color-brand-400)]/50"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-white">{voice.name}</span>
                  <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded ${
                    voice.gender === "Feminino" ? "bg-pink-500/20 text-pink-400" : "bg-blue-500/20 text-blue-400"
                  }`}>
                    {voice.gender}
                  </span>
                </div>
                <span className="text-xs text-[var(--color-foreground-muted)]">{voice.desc}</span>
              </button>
            ))}
          </div>

          <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg flex gap-3">
            <Info className="text-blue-400 shrink-0" size={18} />
            <p className="text-xs text-blue-200">
              As vozes são geradas pela tecnologia HD da OpenAI para garantir a máxima naturalidade na fala do seu agente.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
