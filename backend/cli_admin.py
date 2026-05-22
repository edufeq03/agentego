import os
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, init_db, Empresa, Usuario, Configuracao
from app.auth import get_password_hash

def register_admin():
    print("=== Cadastro de Nova Academia e Administrador (SaaS) ===")
    
    nome_empresa = input("Nome da Academia: ")
    telefone_whatsapp = input("Número de WhatsApp (ex: 5511999999999): ")
    email_admin = input("E-mail do Administrador (para login no painel): ")
    senha_admin = input("Senha do Administrador: ")
    
    print("\nIniciando banco de dados...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # 1. Checa se empresa já existe
        empresa = db.query(Empresa).filter(Empresa.telefone_whatsapp == telefone_whatsapp).first()
        if empresa:
            print("Erro: Já existe uma empresa com esse número de WhatsApp cadastrado.")
            return

        # 2. Checa se o email já existe
        usuario = db.query(Usuario).filter(Usuario.email == email_admin).first()
        if usuario:
            print("Erro: Já existe um usuário com esse e-mail.")
            return

        # 3. Cria a Empresa
        nova_empresa = Empresa(
            nome=nome_empresa,
            telefone_whatsapp=telefone_whatsapp
        )
        db.add(nova_empresa)
        db.flush() # Para gerar o ID e webhook_token
        
        # 4. Cria a Configuração Padrão
        nova_config = Configuracao(
            empresa_id=nova_empresa.id,
            config={
                "nome_agente": "Rosana",
                "personalidade": "Seja simpática, profissional e vendedora.",
                "mensagens_base": {
                    "saudacao": "Olá! Sou a Rosana, assistente virtual da academia."
                }
            }
        )
        db.add(nova_config)

        # 5. Cria o Usuário Administrador
        novo_usuario = Usuario(
            empresa_id=nova_empresa.id,
            email=email_admin,
            senha_hash=get_password_hash(senha_admin)
        )
        db.add(novo_usuario)
        
        db.commit()
        
        print("\n✅ Cadastro Realizado com Sucesso!")
        print("-" * 50)
        print(f"Empresa: {nova_empresa.nome}")
        print(f"URL do Webhook para EvolutionAPI: /webhook/{nova_empresa.webhook_token}")
        print(f"Login Dashboard: {novo_usuario.email}")
        print(f"Senha Dashboard: {senha_admin}")
        print("-" * 50)
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao cadastrar: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    register_admin()
