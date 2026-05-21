import sys
import os

# Adiciona o diretório bot-service ao PATH para conseguir importar os módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bot-service')))

from app.database import SessionLocal, Empresa, Configuracao
from app.agent import montar_prompt

def test_and_persist_config():
    db = SessionLocal()
    try:
        # 1. Recuperar empresa da academia Prime Fit
        empresa = db.query(Empresa).filter(Empresa.telefone_whatsapp == "5511999990000").first()
        if not empresa:
            print("ERRO: Empresa Prime Fit não encontrada no banco de dados!")
            return
        
        print(f"Empresa encontrada: {empresa.nome} (Nicho: {empresa.nicho})")
        
        # 2. Recuperar a configuração atual
        config_obj = db.query(Configuracao).filter(Configuracao.empresa_id == empresa.id).first()
        if not config_obj:
            print("ERRO: Configuração da Prime Fit não encontrada!")
            return
            
        current_config = config_obj.config or {}
        print("Configuração atual carregada com sucesso.")
        
        # 3. Adicionar dados mockados de Professores e Grade de Aulas
        new_professores = [
            {
                "nome": "Ricardo Silva",
                "especialidade": "Musculação e Hipertrofia",
                "descricao": "Formado em Ed. Física pela UNICAMP, especialista em reabilitação física."
            },
            {
                "nome": "Ana Beatriz",
                "especialidade": "Yoga e Pilates",
                "descricao": "Especialista em bem-estar corporal com mais de 8 anos de experiência."
            }
        ]
        
        new_aulas = [
            {
                "nome": "Crossfit",
                "dias_horarios": "Ter e Qui às 19h",
                "professor": "Ricardo Silva",
                "descricao": "Treino de alta intensidade focado em força e condicionamento. Limite de 15 alunos."
            },
            {
                "nome": "Yoga Matinal",
                "dias_horarios": "Qua e Sex às 08h",
                "professor": "Ana Beatriz",
                "descricao": "Perfeito para começar o dia com equilíbrio, foco e alongamento."
            }
        ]
        
        # Atualiza a configuração
        current_config["professores"] = new_professores
        current_config["aulas"] = new_aulas
        
        # Garante que o SQLAlchemy detecte a alteração no dicionário interno do JSONB
        from sqlalchemy.orm.attributes import flag_modified
        config_obj.config = {**current_config}
        flag_modified(config_obj, "config")
        
        # 4. Testar montagem de prompt para verificar se as informações são injetadas
        prompt = montar_prompt(
            config=current_config,
            intencao="duvida",
            stage="novo",
            contexto_tempo="Tarde"
        )
        
        # Validações estruturais no prompt gerado
        print("\n" + "="*50)
        print("TESTE DE GERAÇÃO DE PROMPT")
        print("="*50)
        
        has_professores = "=== PROFESSORES E EQUIPE ===" in prompt
        has_aulas = "=== GRADE DE AULAS / MODALIDADES ===" in prompt
        has_ricardo = "Ricardo Silva" in prompt
        has_crossfit = "Crossfit" in prompt
        
        print(f"Injetou seção de Professores? {'SIM' if has_professores else 'NÃO'}")
        print(f"Injetou seção de Grade de Aulas? {'SIM' if has_aulas else 'NÃO'}")
        print(f"Ricardo Silva está no prompt? {'SIM' if has_ricardo else 'NÃO'}")
        print(f"Crossfit está no prompt? {'SIM' if has_crossfit else 'NÃO'}")
        
        if not (has_professores and has_aulas and has_ricardo and has_crossfit):
            print("\nERRO: O prompt gerado não contém todas as informações injetadas!")
            return
            
        print("\nSucesso! O prompt de IA foi montado perfeitamente com todas as novas informações dinâmicas!")
        
        # 5. Salvar no Banco de Dados
        config_obj.config = current_config
        db.commit()
        print("\nConfigurações persistidas com sucesso no banco de dados local!")
        
        # 6. Recarregar do banco e fazer dupla verificação
        db.refresh(config_obj)
        saved_config = config_obj.config
        assert "professores" in saved_config, "Erro: Professores não persistidos!"
        assert "aulas" in saved_config, "Erro: Aulas não persistidas!"
        print("Dupla verificação no banco concluída com 100% de sucesso!")
        
    except Exception as e:
        print(f"Erro inesperado no teste: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_and_persist_config()
