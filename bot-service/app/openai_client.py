from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def perguntar(mensagem_usuario, contexto_sistema, historico=None):
    if historico is None:
        historico = []
        
    mensagens = [{"role": "system", "content": contexto_sistema}]
    mensagens.extend(historico)
    mensagens.append({"role": "user", "content": mensagem_usuario})
    
    # Se o prompt do sistema exigir regras de sinalização (tags), reforçamos com uma mensagem de sistema no final da lista
    if "[ATUALIZAR_LEAD" in contexto_sistema or "REGRA DE OURO" in contexto_sistema:
        lembrete_sistema = (
            "Lembrete de Formatação Crítico (MANDATÓRIO): Se o usuário acabou de fornecer, alterar ou confirmar qualquer dado "
            "dele ou do seguro na última mensagem, você DEVE incluir a tag invisível correspondente "
            "no final da sua resposta, exatamente no formato '[ATUALIZAR_LEAD: campo=valor]'.\n"
            "Exemplos:\n"
            "- Se informou nome: [ATUALIZAR_LEAD: nome_segurado=Eduardo Targine Capella]\n"
            "- Se quer plano de saúde: [ATUALIZAR_LEAD: tipo_seguro=saude]\n"
            "- Se quer plano odontológico: [ATUALIZAR_LEAD: tipo_seguro=odontologico]\n"
            "- Se informou idade/nascimento: [ATUALIZAR_LEAD: idade_segurado=41]\n"
            "- Se informou CNPJ: [ATUALIZAR_LEAD: tem_cnpj=false]\n"
            "- Se informou plano anterior: [ATUALIZAR_LEAD: tem_plano_anterior=true] [ATUALIZAR_LEAD: plano_anterior_nome=Unimed]\n"
            "- Se informou região: [ATUALIZAR_LEAD: regiao=Campinas]\n"
            "Não responda sem incluir a tag correspondente! As tags são essenciais para salvar os dados no banco de dados."
        )
        mensagens.append({"role": "system", "content": lembrete_sistema})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensagens,
        temperature=0.2
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