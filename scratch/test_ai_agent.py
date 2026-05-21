import sys
import os

# Adiciona o diretório bot-service ao PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bot-service')))

from app.database import SessionLocal, Empresa, Configuracao
from app.agent import processar_mensagem_dinamica

def test_ai_responses():
    db = SessionLocal()
    try:
        # 1. Recuperar empresa da academia Prime Fit
        empresa = db.query(Empresa).filter(Empresa.telefone_whatsapp == "5511999990000").first()
        config_obj = db.query(Configuracao).filter(Configuracao.empresa_id == empresa.id).first()
        config = config_obj.config
        
        print("="*60)
        print("INICIANDO TESTE COM API REAL DA OPENAI (GPT-4o-mini)")
        print("="*60)
        
        # Teste 1: Informações existentes (Aulas)
        q1 = "Quais os horários de Crossfit e quem dá a aula?"
        print(f"\nPergunta 1: {q1}")
        res1 = processar_mensagem_dinamica(
            mensagem_usuario=q1,
            config=config,
            intencao="duvida",
            stage="novo",
            contexto_tempo="Tarde"
        )
        print(f"Resposta 1:\n{res1}")
        
        # Teste 2: Informações existentes (Professores)
        q2 = "Quem é o professor Ricardo Silva?"
        print(f"\nPergunta 2: {q2}")
        res2 = processar_mensagem_dinamica(
            mensagem_usuario=q2,
            config=config,
            intencao="duvida",
            stage="novo",
            contexto_tempo="Tarde"
        )
        print(f"Resposta 2:\n{res2}")
        
        # Teste 3: Anti-Alucinação (Modalidade inexistente)
        q3 = "Vocês têm aula de Natação? Gostaria muito de saber o horário."
        print(f"\nPergunta 3 (Guarda-chuva/Guardrail): {q3}")
        res3 = processar_mensagem_dinamica(
            mensagem_usuario=q3,
            config=config,
            intencao="duvida",
            stage="novo",
            contexto_tempo="Tarde"
        )
        print(f"Resposta 3:\n{res3}")
        
        # Teste 4: Anti-Alucinação (Professor inexistente)
        q4 = "Queria fazer aula com o professor André. Quais aulas ele dá?"
        print(f"\nPergunta 4 (Guarda-chuva/Guardrail): {q4}")
        res4 = processar_mensagem_dinamica(
            mensagem_usuario=q4,
            config=config,
            intencao="duvida",
            stage="novo",
            contexto_tempo="Tarde"
        )
        print(f"Resposta 4:\n{res4}")
        
        print("\n" + "="*60)
        print("VALIDAÇÃO CONCLUÍDA")
        print("="*60)
        
    except Exception as e:
        print(f"Erro ao testar a IA: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_ai_responses()
