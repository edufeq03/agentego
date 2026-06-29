from openai import OpenAI
import os
import requests

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def perguntar(mensagem_usuario, contexto_sistema, historico=None, temperature=0.2):
    if historico is None:
        historico = []
        
    mensagens = [{"role": "system", "content": contexto_sistema}]
    mensagens.extend(historico)
    mensagens.append({"role": "user", "content": mensagem_usuario})
    
    # Se o prompt do sistema exigir regras de sinalização (tags), reforçamos com uma mensagem de sistema no final da lista
    if "[ATUALIZAR_LEAD" in contexto_sistema or "REGRA DE OURO" in contexto_sistema:
        is_lanchonete = "[ADICIONAR_ITEM" in contexto_sistema
        is_corretora = "seguro" in contexto_sistema.lower() or "corretora" in contexto_sistema.lower()
        
        if is_corretora:
            exemplos = (
                "Exemplos:\n"
                "- Se informou nome: [ATUALIZAR_LEAD: nome_segurado=Eduardo Targine Capella]\n"
                "- Se quer plano de saúde: [ATUALIZAR_LEAD: tipo_seguro=saude]\n"
                "- Se quer plano odontológico: [ATUALIZAR_LEAD: tipo_seguro=odontologico]\n"
                "- Se informou idade/nascimento: [ATUALIZAR_LEAD: idade_segurado=41]\n"
                "- Se informou CNPJ: [ATUALIZAR_LEAD: tem_cnpj=false]\n"
                "- Se informou plano anterior: [ATUALIZAR_LEAD: tem_plano_anterior=true] [ATUALIZAR_LEAD: plano_anterior_nome=Unimed]\n"
                "- Se informou região: [ATUALIZAR_LEAD: regiao=Campinas]\n"
            )
        else:
            exemplos = (
                "Exemplos:\n"
                "- Se informou nome: [ATUALIZAR_LEAD: nome_cliente=Eduardo]\n"
            )

        lembrete_sistema = (
            "Lembrete de Formatação Crítico (MANDATÓRIO): Se o usuário acabou de fornecer, alterar ou confirmar qualquer dado "
            "dele na última mensagem, você DEVE incluir a tag invisível correspondente "
            "no final da sua resposta, exatamente no formato '[ATUALIZAR_LEAD: campo=valor]'.\n"
            f"{exemplos}"
            "Não responda sem incluir a tag correspondente! As tags são essenciais para salvar os dados no banco de dados.\n\n"
        )
        
        # Não injetar regra de CRM para Lanchonete, pois ela usa a tag de fechamento de pedido [CONFIRMAR_PEDIDO]
        if not is_lanchonete:
            lembrete_sistema += (
                "=== AUTOMAÇÃO INTELIGENTE DE CRM (NOVO) ===\n"
                "Se o cliente expressar forte intenção de compra, aceitar os valores passados, ou se a triagem de vendas "
                "estiver completa e você identificar que o lead está 'quente' e pronto para fechamento, você DEVE anexar "
                "a tag invisível [CRIAR_OPORTUNIDADE: motivo=sua justificativa aqui] no final da sua resposta. Isso criará "
                "automaticamente um card no CRM Kanban para a equipe comercial."
            )
            
        mensagens.append({"role": "system", "content": lembrete_sistema})
    
    # Usar temperatura configurável (garantir que esteja nos limites permitidos)
    temp_val = 0.2
    try:
        if temperature is not None:
            temp_val = float(temperature)
            temp_val = max(0.0, min(1.0, temp_val))
    except Exception:
        temp_val = 0.2

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensagens,
        temperature=temp_val
    )
    texto = response.choices[0].message.content
    t_in = response.usage.prompt_tokens
    t_out = response.usage.completion_tokens
    return texto, t_in, t_out

def transcrever_audio(caminho_arquivo):
    with open(caminho_arquivo, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcription.text

def gerar_audio(texto, caminho_salvar, provider="openai", voice="nova", api_key=None, voice_id=None):
    # Se o provedor for ElevenLabs, tenta gerar o áudio
    if provider == "elevenlabs":
        api_key_to_use = api_key or os.getenv("ELEVENLABS_API_KEY")
        voice_id_to_use = voice_id or os.getenv("ELEVENLABS_VOICE_ID") or "21m00Tcm4TlvDq8ikWAM"
        
        if not api_key_to_use:
            print("ElevenLabs API Key não configurada. Usando fallback para OpenAI TTS.")
            provider = "openai"
        else:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id_to_use}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key_to_use
            }
            data = {
                "text": texto,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            try:
                response = requests.post(url, json=data, headers=headers, timeout=15)
                if response.status_code == 200:
                    with open(caminho_salvar, "wb") as f:
                        f.write(response.content)
                    return
                else:
                    print(f"Erro ElevenLabs (Status {response.status_code}): {response.text}. Usando fallback para OpenAI TTS.")
                    provider = "openai"
            except Exception as e:
                print(f"Exceção ao chamar ElevenLabs: {e}. Usando fallback para OpenAI TTS.")
                provider = "openai"

    # Fallback ou padrão: OpenAI
    if provider == "openai" or not provider:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice or "nova",
            input=texto
        )
        response.write_to_file(caminho_salvar)