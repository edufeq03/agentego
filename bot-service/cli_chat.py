import sys
import os

# Força codificação UTF-8 para suportar emojis no terminal do Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Adiciona o diretório atual ao path para poder importar o app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import get_db, Empresa, init_db
from app.pipeline import processar_webhook

def iniciar_chat():
    print("======================================================")
    print("🤖 CHAT DE TESTE MULTI-TENANT - AGENTE ACADEMIA")
    print("======================================================")
    print("Iniciando banco de dados...")
    init_db()

    db = get_db()
    empresa = db.query(Empresa).filter(Empresa.nome == "Prime Fit").first()
    db.close()

    if not empresa:
        print("Erro: Empresa 'Prime Fit' não encontrada. Rode o seed.py primeiro.")
        return

    print(f"Empresa selecionada: {empresa.nome}")
    print("Digite 'sair' para encerrar.\n")
    
    telefone_teste = "5511999999999" # Mesmo número usado no seed.py para manter contexto
    
    while True:
        try:
            mensagem = input("Você: ")
            if mensagem.lower() in ['sair', 'exit', 'quit']:
                print("Encerrando chat de teste...")
                break
                
            if not mensagem.strip():
                continue
            
            print(f"{empresa.configuracoes.config.get('nome_agente', 'Agente')} (processando...)...\r", end="")
            
            # Usar o pipeline central passando a entidade da empresa simulada
            db = get_db()
            empresa = db.query(Empresa).filter(Empresa.id == empresa.id).first()
            resultado = processar_webhook(empresa, telefone_teste, mensagem)
            db.close()
            
            if resultado["status"] == "ok":
                resposta = resultado["resposta"]
            else:
                resposta = f"[O bot está pausado. Status: {resultado['status']}]"
            
            nome_bot = empresa.configuracoes.config.get('nome_agente', 'Agente')
            print(f"{nome_bot}: {resposta}" + " " * 20 + "\n")
            
        except KeyboardInterrupt:
            print("\nEncerrando chat de teste...")
            break
        except Exception as e:
            print(f"\nErro ao processar mensagem: {e}\n")

if __name__ == "__main__":
    iniciar_chat()
