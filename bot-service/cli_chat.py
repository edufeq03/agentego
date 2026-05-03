import sys
import os

# Força codificação UTF-8 para suportar emojis no terminal do Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Adiciona o diretório atual ao path para poder importar o app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.agent import processar_mensagem

def iniciar_chat():
    print("======================================================")
    print("🤖 CHAT DE TESTE - AGENTE ACADEMIA (SEM WHATSAPP)")
    print("======================================================")
    print("Digite 'sair' para encerrar.\n")
    
    historico = []
    
    from app.database import obter_conversa, salvar_mensagem
    telefone_teste = "TERMINAL_TEST"
    conversa_id = obter_conversa(telefone_teste)
    
    while True:
        try:
            mensagem = input("Você: ")
            if mensagem.lower() in ['sair', 'exit', 'quit']:
                print("Encerrando chat de teste...")
                break
                
            if not mensagem.strip():
                continue
                
            salvar_mensagem(conversa_id, "usuario", mensagem)
            
            print("Rosana (digitando...)...\r", end="")
            resposta = processar_mensagem(mensagem, historico)
            
            salvar_mensagem(conversa_id, "agente", resposta)
            
            # Atualiza o histórico localmente, igual no main.py
            historico.append({"role": "user", "content": mensagem})
            historico.append({"role": "assistant", "content": resposta})
            
            # Mantém apenas as últimas 6 mensagens (3 interações completas)
            historico = historico[-6:]
            
            print(f"Rosana: {resposta}" + " " * 20 + "\n") # Espaços extras para limpar o "digitando..."
            
        except KeyboardInterrupt:
            print("\nEncerrando chat de teste...")
            break
        except Exception as e:
            print(f"\nErro ao processar mensagem: {e}\n")

if __name__ == "__main__":
    iniciar_chat()
