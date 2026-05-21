import json
import logging
from app.openai_client import client

logger = logging.getLogger(__name__)

PROMPT_TRIAGEM = """
Você é um assistente de triagem de contatos em uma plataforma SaaS multi-nicho.
Analise a mensagem de um cliente e extraia os dados estruturados de triagem.
Retorne APENAS um objeto JSON válido no seguinte formato:

{
  "intencao": "preco|horario|servicos|plano|visita|documento|duvida|saudacao|encerramento",
  "sentimento": "positivo|neutro|negativo",
  "urgente": true|false,
  "resumo_curto": "máximo 10 palavras descrevendo o que o cliente quer"
}

Definições de Intenção:
- preco: cliente pergunta sobre valores, mensalidade, planos, orçamento, quanto custa
- horario: cliente pergunta sobre horário de funcionamento, abre/fecha, agenda/agendar
- servicos: cliente pergunta sobre aulas, modalidades, equipe, serviços, produtos, imovel
- plano: cliente pergunta sobre planos de assinatura, contrato, pacote, matrícula
- visita: cliente expressa intenção de agendar, ir, vir ou conhecer o local fisicamente
- documento: cliente enviou ou menciona envio de arquivo, foto, CNH, CRLV, carteirinha
- saudacao: "oi", "olá", "bom dia" sem conteúdo de dúvida adicional
- encerramento: "obrigado", "tchau", "até mais"
- duvida: qualquer outra pergunta ou assunto geral que não se encaixe nos anteriores

Definições de Sentimento:
- positivo: cliente alegre, satisfeito, agradecendo calorosamente
- neutro: tom de pergunta normal, padrão
- negativo: cliente frustrado, reclamando, reclamando de demora, usando caps lock ou sarcasmo

Definições de Urgente:
- true: cliente indica pressa, necessidade imediata, ou emergência ("preciso urgente", "rápido")
- false: caso contrário

Retorne estritamente o JSON sem blocos de markdown e sem explicações.
"""

class TriagemAgent:
    nome = "TriagemAgent"

    def analisar(self, mensagem: str) -> dict:
        """
        Analisa a mensagem e retorna dict com:
        intencao, sentimento, urgente, resumo_curto, tokens_in, tokens_out
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": PROMPT_TRIAGEM},
                    {"role": "user", "content": mensagem}
                ],
                response_format={"type": "json_object"},
                max_tokens=150,
                temperature=0.0
            )
            dados = json.loads(response.choices[0].message.content)
            dados["tokens_in"] = response.usage.prompt_tokens
            dados["tokens_out"] = response.usage.completion_tokens
            return dados
        except Exception as e:
            logger.error(f"Erro no TriagemAgent: {e}")
            # Fallback seguro: não quebra o fluxo
            return {
                "intencao": "duvida",
                "sentimento": "neutro",
                "urgente": False,
                "resumo_curto": "mensagem não classificada",
                "tokens_in": 0,
                "tokens_out": 0
            }

triagem_agent = TriagemAgent()
