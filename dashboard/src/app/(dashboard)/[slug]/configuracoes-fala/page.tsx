"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Mic, Save, Info, Volume2, Music, UserCircle, Sliders, Key, Eye, EyeOff, Layers } from "lucide-react";
import api from "@/lib/api";

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
  const [showElevenlabsKey, setShowElevenlabsKey] = useState(false);
  const [config, setConfig] = useState({
    stt_enabled: true,
    tts_enabled: true,
    tts_always: false,
    tts_voice: "nova",
    provedor_tts: "openai",
    elevenlabs_api_key: "",
    elevenlabs_voice_id: "",
    openai_temperature: 0.2
  });

  useEffect(() => {
    async function loadConfig() {
      try {
        const response = await api.get("/dashboard/config");
        if (response.data?.config) {
          const configData = response.data.config;
          setConfig({
            stt_enabled: configData.stt_enabled !== false,
            tts_enabled: configData.tts_enabled !== false,
            tts_always: configData.tts_always === true,
            tts_voice: configData.tts_voice || "nova",
            provedor_tts: configData.provedor_tts || "openai",
            elevenlabs_api_key: configData.elevenlabs_api_key || "",
            elevenlabs_voice_id: configData.elevenlabs_voice_id || "",
            openai_temperature: configData.openai_temperature !== undefined ? configData.openai_temperature : 0.2
          });
        }
      } catch (error) {
        console.error("Erro ao carregar configurações:", error);
        alert("Erro ao carregar configurações");
      } finally {
        setLoading(false);
      }
    }
    if (slug) loadConfig();
  }, [slug]);

  async function handleSave() {
    setSaving(true);
    try {
      // Carrega a configuração atual primeiro para mesclar, 
      // para não sobrescrever outros campos do Agent Builder
      const currentRes = await api.get("/dashboard/config");
      const fullConfig = { ...(currentRes.data?.config || {}), ...config };
      
      await api.put("/dashboard/config", { config: fullConfig });
      alert("Configurações de fala atualizadas!");
    } catch (error) {
      console.error("Erro ao salvar:", error);
      alert("Erro ao salvar configurações");
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
        {/* Coluna da Esquerda: Comportamento e Ajustes de IA */}
        <div className="space-y-6">
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

          {/* Ajustes do Modelo de IA */}
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <Sliders className="text-[var(--color-brand-400)]" size={20} />
              <h2 className="text-lg font-semibold text-white">Modelo de IA (OpenAI)</h2>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-[var(--color-background)] rounded-lg border border-[var(--color-border)] space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">Temperatura do Modelo</p>
                    <p className="text-xs text-[var(--color-foreground-muted)]">Controla o nível de criatividade ou determinismo do agente.</p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-[var(--color-brand-500)]/20 text-[var(--color-brand-400)] font-mono font-bold text-sm">
                    {config.openai_temperature}
                  </span>
                </div>

                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.1"
                  value={config.openai_temperature}
                  onChange={(e) => setConfig({ ...config, openai_temperature: parseFloat(e.target.value) })}
                  className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-[var(--color-brand-500)]"
                />

                <div className="flex justify-between text-[10px] text-[var(--color-foreground-muted)] font-medium">
                  <span>Determinístico (Fiel)</span>
                  <span>Equilibrado</span>
                  <span>Criativo (Variado)</span>
                </div>
              </div>
              
              <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex gap-3">
                <Info className="text-yellow-400 shrink-0" size={18} />
                <p className="text-xs text-yellow-200">
                  {config.openai_temperature <= 0.2 ? (
                    "Recomendado: O agente será extremamente fiel à base de conhecimento e evitará alucinações ou desvios."
                  ) : config.openai_temperature <= 0.6 ? (
                    "Equilibrado: O agente terá um tom de conversa mais fluido e natural, mas mantendo boa fidelidade."
                  ) : (
                    "Aviso: Temperaturas altas aumentam a criatividade, mas podem levar o agente a ignorar regras restritas da base de conhecimento."
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Coluna da Direita: Seleção de Voz */}
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 space-y-6">
          <div className="flex items-center gap-3 mb-2">
            <UserCircle className="text-[var(--color-brand-400)]" size={20} />
            <h2 className="text-lg font-semibold text-white">Voz do Agente</h2>
          </div>

          {/* Seletor de Provedor de Voz */}
          <div className="flex gap-2 p-1 bg-[var(--color-background)] rounded-lg border border-[var(--color-border)]">
            <button
              onClick={() => setConfig({ ...config, provedor_tts: "openai" })}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md font-medium text-xs transition-all ${
                config.provedor_tts === "openai"
                  ? "bg-[var(--color-brand-500)] text-white shadow-md shadow-[var(--color-brand-500)]/20"
                  : "text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/5"
              }`}
            >
              <Volume2 size={14} />
              OpenAI (HD)
            </button>
            <button
              onClick={() => setConfig({ ...config, provedor_tts: "elevenlabs" })}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md font-medium text-xs transition-all ${
                config.provedor_tts === "elevenlabs"
                  ? "bg-[var(--color-brand-500)] text-white shadow-md shadow-[var(--color-brand-500)]/20"
                  : "text-[var(--color-foreground-muted)] hover:text-white hover:bg-white/5"
              }`}
            >
              <Layers size={14} />
              ElevenLabs (Premium)
            </button>
          </div>

          {config.provedor_tts === "openai" ? (
            <>
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
            </>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <Key size={14} className="text-[var(--color-brand-400)]" />
                  API Key da ElevenLabs
                </label>
                <div className="relative">
                  <input
                    type={showElevenlabsKey ? "text" : "password"}
                    value={config.elevenlabs_api_key || ""}
                    onChange={(e) => setConfig({ ...config, elevenlabs_api_key: e.target.value })}
                    placeholder="Cole sua API Key do ElevenLabs"
                    className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)] pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowElevenlabsKey(!showElevenlabsKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-foreground-muted)] hover:text-white transition-colors"
                  >
                    {showElevenlabsKey ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <Music size={14} className="text-[var(--color-brand-400)]" />
                  Voice ID da ElevenLabs
                </label>
                <input
                  type="text"
                  value={config.elevenlabs_voice_id || ""}
                  onChange={(e) => setConfig({ ...config, elevenlabs_voice_id: e.target.value })}
                  placeholder="Ex: 21m00Tcm4TlvDq8ikWAM (Voz da Rachel)"
                  className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--color-brand-500)]"
                />
                <p className="text-[10px] text-[var(--color-foreground-muted)]">
                  Deixe em branco para usar a voz premium padrão super natural em Português do Brasil (Rachel).
                </p>
              </div>

              <div className="p-4 bg-[var(--color-brand-500)]/10 border border-[var(--color-brand-500)]/20 rounded-lg flex gap-3">
                <Info className="text-[var(--color-brand-400)] shrink-0" size={18} />
                <p className="text-xs text-blue-200">
                  ElevenLabs oferece a tecnologia de voz mais avançada e natural do mercado, ideal para evitar sotaque estrangeiro no Português do Brasil (PT-BR).
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
