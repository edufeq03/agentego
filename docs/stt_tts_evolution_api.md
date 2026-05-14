# Conhecimento Técnico: STT e TTS com Evolution API

Este documento registra as lições aprendidas e a solução final para a reativação das funções de voz (Speech-to-Text e Text-to-Speech) no AgenteGo.

## 1. O Problema Identificado
O sistema de voz estava inoperante devido a três fatores:
1. **Bug de Código**: Havia um erro de digitação no payload de envio de áudio (`audio_audio_base64` em vez de `audio_base64`).
2. **Configuração da Evolution API**: A flag `webhookBase64` nem sempre é respeitada pela Evolution API, resultando em webhooks sem o conteúdo do áudio, mesmo quando a opção está visualmente ativada no painel.
3. **Criptografia de Mídia**: Quando o Base64 não é enviado, a Evolution envia uma URL de mídia do WhatsApp que está criptografada (`.enc`), impedindo a transcrição direta por download simples.

## 2. A Solução Implementada

### Backend (Bot Service)
- **Lógica de Captura Robusta**: O bot agora tenta capturar o áudio em três níveis de prioridade:
    1. Busca o `base64` direto na raiz do webhook.
    2. Busca o `base64` dentro do objeto `audioMessage`.
    3. **Fallback Automático**: Se o Base64 estiver ausente, o bot utiliza o endpoint oficial da Evolution API (`/chat/getBase64FromMedia`) para solicitar a descriptografia e o download do arquivo.
- **Configuração por Tenant**: Implementação de flags `stt_enabled`, `tts_enabled` e `tts_always` no JSON de configuração da empresa, permitindo controle individual.
- **Modernização da SDK OpenAI**: Atualização dos métodos de TTS para os padrões atuais da biblioteca OpenAI (v1.0+).

### Dashboard
- **Interface de Controle**: Adicionada seção "Configurações de Voz" no Agent Builder, permitindo que o usuário ative/desative as funções de voz e configure o robô para "Sempre responder com áudio".

## 3. Guia de Manutenção
Caso o áudio pare de funcionar novamente:
1. Verifique se a `OPENAI_API_KEY` tem créditos e se o modelo `whisper-1` e `tts-1` estão disponíveis.
2. Certifique-se de que o Webhook da Evolution API está configurado com `messages.upsert` ativo.
3. Se o log indicar `audio_sem_base64`, verifique se o bot consegue alcançar a URL da Evolution API para realizar o download de fallback.

---
*Documentação gerada em 13/05/2026 após sessão de estabilização de voz.*
