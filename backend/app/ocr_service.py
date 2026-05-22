import base64
import json
import logging
import httpx
from app.openai_client import client

logger = logging.getLogger(__name__)

PROMPTS_OCR = {
    "cnh": """
        Analise esta imagem de CNH (Carteira Nacional de Habilitação).
        Extraia os dados e retorne APENAS um JSON válido no formato:
        {
          "nome": "NOME COMPLETO DO CONDUTOR",
          "cpf": "CPF FORMATADO COM PONTOS OU APENAS DIGITOS",
          "data_nascimento": "DD/MM/AAAA",
          "data_validade": "DD/MM/AAAA",
          "categoria": "A|B|AB|C|D|E",
          "numero_registro": "NUMERO DE REGISTRO",
          "confianca": 0.0_a_1.0
        }
        Se não conseguir ler algum campo, coloque null.
        Retorne estritamente o JSON sem marcações de markdown e sem explicações.
    """,
    "crlv": """
        Analise esta imagem de CRLV (Certificado de Registro e Licenciamento de Veículo).
        Extraia os dados e retorne APENAS um JSON válido no formato:
        {
          "placa": "PLACA DO VEICULO",
          "renavam": "RENAVAM",
          "chassi": "CHASSI",
          "marca": "MARCA",
          "modelo": "MODELO",
          "ano_fabricacao": 20XX,
          "ano_modelo": 20XX,
          "cor": "COR DO VEICULO",
          "municipio": "CIDADE/UF",
          "confianca": 0.0_a_1.0
        }
        Se não conseguir ler algum campo, coloque null.
        Retorne estritamente o JSON sem marcações de markdown e sem explicações.
    """,
    "carteirinha_plano": """
        Analise esta carteirinha de plano de saúde / plano odontológico.
        Extraia os dados e retorne APENAS um JSON válido no formato:
        {
          "nome_titular": "NOME DO TITULAR",
          "operadora": "NOME DA OPERADORA/SEGURADORA",
          "numero_carteirinha": "NUMERO DA CARTEIRINHA OU CONTRATO",
          "plano_nome": "NOME DO PRODUTO/PLANO",
          "validade": "DD/MM/AAAA ou null",
          "confianca": 0.0_a_1.0
        }
        Se não conseguir ler algum campo, coloque null.
        Retorne estritamente o JSON sem marcações de markdown e sem explicações.
    """,
}

def processar_ocr(url_imagem: str, tipo: str) -> dict:
    """
    Baixa a imagem da Evolution API e usa o GPT-4o Vision para processar o OCR.
    """
    logger.info(f"Iniciando processamento de OCR para tipo={tipo}, url={url_imagem}")
    prompt = PROMPTS_OCR.get(tipo, """
        Analise este documento de seguro.
        Extraia os dados de forma estruturada e retorne um JSON com os campos encontrados e um campo "confianca" de 0.0 a 1.0.
        Retorne estritamente o JSON sem explicações.
    """)
    
    try:
        # Baixar imagem
        response = httpx.get(url_imagem, timeout=30)
        response.raise_for_status()
        
        # Converter para base64
        img_b64 = base64.b64encode(response.content).decode("utf-8")
        
        # Determinar mimetype simples
        ext = url_imagem.split("?")[0].split(".")[-1].lower()
        if ext not in ("jpg", "jpeg", "png", "webp"):
            ext = "jpeg"
        mimetype = f"image/{ext}"
        
        resultado = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{mimetype};base64,{img_b64}"
                    }}
                ]
            }],
            response_format={"type": "json_object"},
            max_tokens=500,
            temperature=0.0
        )
        
        dados = json.loads(resultado.choices[0].message.content)
        return dados
    except Exception as e:
        logger.error(f"Erro no OCR service para {url_imagem}: {e}")
        return {"erro": str(e), "confianca": 0.0}

def classificar_e_processar_ocr(img_b64: str, mimetype: str) -> dict:
    """
    Classifica e extrai dados de CNH, CRLV ou Carteirinha em um único call GPT-4o.
    """
    prompt = """
    Analise esta imagem de documento de seguro.
    Identifique se é uma CNH (Carteira Nacional de Habilitação), um CRLV (Documento de Licenciamento de Veículo) ou uma Carteirinha de Plano de Saúde/Odontológico.
    
    Retorne APENAS um JSON válido no seguinte formato:
    {
      "tipo": "cnh|crlv|carteirinha_plano|outro",
      "dados": {
         ... extraia todos os dados legíveis correspondentes ...
      },
      "confianca": 0.0_a_1.0
    }
    
    Se for CNH, extraia: nome, cpf, data_nascimento (DD/MM/AAAA), data_validade (DD/MM/AAAA), categoria, numero_registro.
    Se for CRLV, extraia: placa, renavam, chassi, marca, modelo, ano_fabricacao, ano_modelo, cor, municipio.
    Se for Carteirinha de Plano, extraia: nome_titular, operadora, numero_carteirinha, plano_nome, validade.
    
    Se não for nenhum desses, retorne "tipo": "outro" e quaisquer textos úteis em "dados".
    Retorne estritamente o JSON sem marcações de markdown e sem explicações.
    """
    try:
        resultado = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{mimetype};base64,{img_b64}"
                    }}
                ]
            }],
            response_format={"type": "json_object"},
            max_tokens=600,
            temperature=0.0
        )
        return json.loads(resultado.choices[0].message.content)
    except Exception as e:
        logger.error(f"Erro ao classificar e processar OCR: {e}")
        return {"tipo": "outro", "dados": {}, "confianca": 0.0, "erro": str(e)}
