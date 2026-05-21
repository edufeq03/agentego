import sys
import os
import uuid

# Adiciona o diretório bot-service ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../bot-service")))

from app.database import SessionLocal, CampoCustomizado

def seed_brokerage_triage():
    print("Iniciando seed de campos de triagem avançados para a Piccolo Corretora Teste...")
    db = SessionLocal()
    
    empresa_id = "4a376a15-7276-4bb6-b5ad-5329479dcd39"
    
    try:
        # 1. Limpar campos antigos
        deletados = db.query(CampoCustomizado).filter(CampoCustomizado.empresa_id == empresa_id).delete()
        print(f"Campos antigos removidos: {deletados}")
        
        # 2. Definir novos campos
        novos_campos = []
        
        # --- CAMPO RAIZ ---
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="tipo_seguro",
            label="Tipo de Seguro",
            tipo="opcao_unica",
            opcoes=["Plano de Saúde", "Automóvel/Motos", "Outros seguros"],
            obrigatorio=True,
            ativo=True,
            ordem=10,
            dependencias=None
        ))
        
        # --- PLANO DE SAÚDE (Condicionados a tipo_seguro == Plano de Saúde) ---
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="para_quem",
            label="Para quem é o plano?",
            tipo="texto",
            obrigatorio=True,
            ativo=True,
            ordem=20,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Plano de Saúde"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="idade_beneficiarios",
            label="Idade das pessoas beneficiárias",
            tipo="texto",
            obrigatorio=True,
            ativo=True,
            ordem=30,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Plano de Saúde"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="tem_cnpj_mei",
            label="Possui CNPJ ou MEI?",
            tipo="opcao_unica",
            opcoes=["Sim (CNPJ)", "Sim (MEI)", "Não"],
            obrigatorio=True,
            ativo=True,
            ordem=40,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Plano de Saúde"]}
        ))
        
        # --- SUB-CONDIÇÃO: Se for MEI, tem mais de 6 meses? (Condicionado a tem_cnpj_mei == Sim (MEI)) ---
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="mei_mais_6_meses",
            label="Se for MEI, possui mais de 6 meses de abertura?",
            tipo="opcao_unica",
            opcoes=["Sim", "Não"],
            obrigatorio=False,
            ativo=True,
            ordem=50,
            dependencias={"campo_pai": "tem_cnpj_mei", "valores": ["Sim (MEI)"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="cidade_regiao_atendimento",
            label="Região/Cidade para atendimento hospitalar",
            tipo="texto",
            obrigatorio=True,
            ativo=True,
            ordem=60,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Plano de Saúde"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="hospital_preferencia",
            label="Tem algum hospital de preferência? Se sim, qual?",
            tipo="texto",
            obrigatorio=False,
            ativo=True,
            ordem=70,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Plano de Saúde"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="plano_atual",
            label="Atualmente tem plano de saúde? Se sim, qual e há quanto tempo?",
            tipo="texto",
            obrigatorio=False,
            ativo=True,
            ordem=80,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Plano de Saúde"]}
        ))
        
        # --- AUTOMÓVEL/MOTOS (Condicionados a tipo_seguro == Automóvel/Motos) ---
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="placa_veiculo",
            label="Placa do veículo / moto",
            tipo="texto",
            obrigatorio=True,
            ativo=True,
            ordem=90,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Automóvel/Motos"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="cep_pernoite",
            label="CEP onde o veículo pernoita",
            tipo="texto",
            obrigatorio=True,
            ativo=True,
            ordem=100,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Automóvel/Motos"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="data_nascimento_condutor",
            label="Data de nascimento do condutor principal",
            tipo="texto",
            obrigatorio=True,
            ativo=True,
            ordem=110,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Automóvel/Motos"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="estado_civil_condutor",
            label="Estado civil do condutor principal",
            tipo="opcao_unica",
            opcoes=["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"],
            obrigatorio=True,
            ativo=True,
            ordem=120,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Automóvel/Motos"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="uso_veiculo",
            label="Uso é lazer exclusivo ou locomoção diária (trabalho/estudos)?",
            tipo="opcao_unica",
            opcoes=["Lazer exclusivo", "Locomoção diária (trabalho/estudos)"],
            obrigatorio=True,
            ativo=True,
            ordem=130,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Automóvel/Motos"]}
        ))
        
        # --- SUB-CONDIÇÃO: Se for para trabalho/estudos, possui garagem? ---
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="garagem_trabalho_escola",
            label="No local de trabalho/estudos, possui garagem fechada?",
            tipo="opcao_unica",
            opcoes=["Sim", "Não"],
            obrigatorio=False,
            ativo=True,
            ordem=140,
            dependencias={"campo_pai": "uso_veiculo", "valores": ["Locomoção diária (trabalho/estudos)"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="uso_comercial",
            label="Uso comercial (visitas a clientes ou fornecedores)?",
            tipo="opcao_unica",
            opcoes=["Sim", "Não"],
            obrigatorio=True,
            ativo=True,
            ordem=150,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Automóvel/Motos"]}
        ))
        
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="uso_aplicativo_entrega",
            label="Uso para aplicativo (Uber, 99) ou entrega de mercadorias?",
            tipo="opcao_unica",
            opcoes=["Sim", "Não"],
            obrigatorio=True,
            ativo=True,
            ordem=160,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Automóvel/Motos"]}
        ))
        
        # --- OUTROS SEGUROS (Condicionado a tipo_seguro == Outros seguros) ---
        novos_campos.append(CampoCustomizado(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            chave="outro_seguro_tipo",
            label="Qual tipo de seguro você precisa?",
            tipo="texto",
            obrigatorio=True,
            ativo=True,
            ordem=170,
            dependencias={"campo_pai": "tipo_seguro", "valores": ["Outros seguros"]}
        ))
        
        # 3. Adicionar e commitar todos os novos campos no DB
        for c in novos_campos:
            db.add(c)
        db.commit()
        print(f"\nSemeado {len(novos_campos)} novos campos de triagem com absoluto sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao semear campos: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_brokerage_triage()
