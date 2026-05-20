import json
import logging
from app.openai_client import client

logger = logging.getLogger(__name__)

def parsear_template_via_ia(texto: str) -> dict:
    prompt = """
    Você é um assistente de cotação de seguros. Você receberá uma mensagem de template de cotação de seguro enviada de um sistema ou landing page externa.
    Analise o texto e extraia todas as informações fornecidas, retornando APENAS um objeto JSON válido.
    
    Os tipos de seguro suportados são:
    - "saude" (Plano de Saúde)
    - "odontologico" (Plano Odontológico)
    - "auto" (Seguro de Carro)
    - "moto" (Seguro de Moto)
    - "residencial" (Seguro Residencial)
    
    A estrutura de resposta do JSON deve ser EXATAMENTE a seguinte:
    {
      "tipo_seguro": "saude|odontologico|auto|moto|residencial|outro",
      "produto_especifico": "descrição do produto ou null",
      "nome_contato": "nome de quem entrou em contato ou null",
      "nome_segurado": "nome de quem vai usar o seguro ou null",
      "relacao_segurado": "proprio|conjuge|filho|pai|outro ou null",
      "telefone": "número com DDI (ex: 5519991234567) ou null",
      "idade_segurado": null ou número inteiro,
      "tem_cnpj": null ou true/false,
      "e_mei": null ou true/false,
      "mais_de_6_meses": null ou true/false,
      "tem_plano_anterior": null ou true/false,
      "plano_anterior_nome": null ou "nome do plano",
      "regiao": "cidade ou região ou null",
      "hospitais_preferidos": "lista de hospitais/preferências separados por vírgula ou null",
      "marca_modelo": "marca e modelo do veículo ou null",
      "ano_fabricacao": null ou número inteiro,
      "ano_modelo": null ou número inteiro,
      "placa": "placa ou null",
      "cep_pernoite": "cep ou null",
      "uso_veiculo": "particular|trabalho|aplicativo ou null",
      "tem_garagem": null ou true/false,
      "condutor_principal": "nome do condutor principal ou null",
      "idade_condutor": null ou número inteiro,
      "bonus_classe": null ou número inteiro,
      "campos_nao_informados": ["lista de campos com ** ou que estavam vazios/não informados"]
    }
    
    Regra Importante:
    - Se houver campos representados por "**" ou "não informado" ou que não existam na mensagem, coloque o valor do campo correspondente como null, e adicione o nome amigável do campo na lista "campos_nao_informados".
    - Retorne estritamente o JSON sem blocos de markdown e sem explicações.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": texto}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        logger.error(f"Erro ao parsear template via IA: {e}")
        return {}
