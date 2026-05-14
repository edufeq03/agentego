from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def perguntar(mensagem_usuario, contexto_sistema, historico=None):
    if historico is None:
        historico = []
        
    mensagens = [{"role": "system", "content": contexto_sistema}]
    mensagens.extend(historico)
    mensagens.append({"role": "user", "content": mensagem_usuario})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensagens
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

def gerar_audio(texto, caminho_salvar, voice="nova"):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=texto
    )
    response.write_to_file(caminho_salvar)