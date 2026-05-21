import sys
import os
import uuid

# Configura o path do bot-service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../bot-service")))

from app.database import SessionLocal, Lead, Empresa, CampoCustomizado
from app.agents.contexto_agent import ContextoAgent

def run_step_by_step_triage_simulation():
    print("==========================================================================")
    print("  SIMULAÇÃO DE TRIAGEM MULTI-NÍVEL DE SEGUROS (PICCOLO CORRETORA TESTE)")
    print("==========================================================================\n")

    db = SessionLocal()
    agent = ContextoAgent()
    
    empresa_id = "4a376a15-7276-4bb6-b5ad-5329479dcd39"
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        print("Erro: Empresa Piccolo Corretora Teste não encontrada!")
        return

    # Mock Lead inicial limpo
    lead = Lead(
        id=str(uuid.uuid4()),
        empresa_id=empresa.id,
        nome="Cliente Simulado",
        dados_customizados={}
    )

    # 1. Obter todos os campos configurados no banco
    db_campos = db.query(CampoCustomizado).filter(
        CampoCustomizado.empresa_id == empresa_id,
        CampoCustomizado.ativo == True
    ).order_by(CampoCustomizado.ordem.asc()).all()

    print(f"Total de campos ativos na corretora: {len(db_campos)}")
    print("Campos cadastrados:")
    for c in db_campos:
        dep_desc = ""
        if c.dependencias:
            dep_desc = f" | Depende de: {c.dependencias.get('campo_pai')} = {c.dependencias.get('valores')}"
        print(f"  - [{c.chave}] {c.label} ({c.tipo}){dep_desc}")
    print("\n--------------------------------------------------------------------------\n")

    # Função auxiliar para simular o estado da triagem conforme respostas entram
    def show_triage_state(lead_state, step_title, user_input=None):
        ctx = agent.montar(
            empresa=empresa,
            lead=lead_state,
            lead_seguro=None,
            triagem={},
            config={"nome_agente": "Rosana", "nome_empresa": empresa.nome}
        )
        
        pendentes = ctx.get("triagem_dinamica", {}).get("campos_pendentes", "").split("\n")
        coletados = ctx.get("triagem_dinamica", {}).get("campos_coletados", "").split("\n")
        
        print(f"▶ ETAPA: {step_title}")
        if user_input:
            print(f"  [Usuário respondeu]: \"{user_input}\"")
        print("  [Campos Coletados]:")
        for col in coletados:
            if col.strip() and not col.startswith("Nenhum"):
                print(f"    ✅ {col}")
            elif col.startswith("Nenhum"):
                print("    ℹ️ Nenhum dado coletado ainda.")
        print("  [Próximos Campos Requeridos pela IA]:")
        for pen in pendentes[:3]: # Mostra os primeiros 3 próximos da fila
            if pen.strip():
                print(f"    ➡️ {pen}")
        print("\n--------------------------------------------------------------------------\n")

    # --- SIMULAÇÃO PLANO DE SAÚDE ---
    print("⚡ SIMULAÇÃO 1: CLIENTE QUER PLANO DE SAÚDE E TEM MEI\n")
    
    # Início: Sem dados coletados
    show_triage_state(lead, "Início da Conversa (Sem respostas)")

    # Usuário escolhe Plano de Saúde
    lead.dados_customizados = {"tipo_seguro": "Plano de Saúde"}
    show_triage_state(lead, "Tipo de Seguro Escolhido", user_input="Quero um plano de saúde")

    # Usuário responde para quem
    lead.dados_customizados.update({"para_quem": "Próprio e esposa"})
    show_triage_state(lead, "Respondido para quem", user_input="Seria para mim e minha esposa")

    # Usuário responde idade
    lead.dados_customizados.update({"idade_beneficiarios": "35 e 32 anos"})
    show_triage_state(lead, "Respondido idades", user_input="Eu tenho 35 e ela 32")

    # Usuário responde que possui MEI
    lead.dados_customizados.update({"tem_cnpj_mei": "Sim (MEI)"})
    # NOTE: Neste ponto, a dependência "mei_mais_6_meses" (que depende de tem_cnpj_mei == Sim (MEI)) deve se ativar!
    show_triage_state(lead, "Respondido CNPJ/MEI (Identificado MEI - Ativa Pergunta de Tempo)", user_input="Nós temos MEI")

    # Usuário responde tempo do MEI
    lead.dados_customizados.update({"mei_mais_6_meses": "Sim"})
    show_triage_state(lead, "Respondido tempo de MEI", user_input="Sim, tem 2 anos que abri")


    # --- SIMULAÇÃO AUTOMÓVEL ---
    print("\n⚡ SIMULAÇÃO 2: CLIENTE QUER SEGURO AUTO E USA PARA TRABALHO\n")
    
    lead_auto = Lead(
        id=str(uuid.uuid4()),
        empresa_id=empresa.id,
        nome="Cliente Simulado Auto",
        dados_customizados={}
    )
    
    # Início: Sem dados coletados
    show_triage_state(lead_auto, "Início da Conversa Auto")

    # Usuário escolhe Automóvel/Motos
    lead_auto.dados_customizados = {"tipo_seguro": "Automóvel/Motos"}
    show_triage_state(lead_auto, "Tipo de Seguro Escolhido", user_input="Preciso de seguro pro meu carro")

    # Usuário fornece Placa, CEP, Nascimento e Estado Civil
    lead_auto.dados_customizados.update({
        "placa_veiculo": "ABC1D23",
        "cep_pernoite": "13010-000",
        "data_nascimento_condutor": "15/08/1990",
        "estado_civil_condutor": "Casado(a)"
    })
    show_triage_state(lead_auto, "Preenchido Dados Iniciais do Veículo", user_input="Minha placa é ABC1D23, pernoita no CEP 13010-000, nasci em 15/08/1990 e sou casado")

    # Usuário responde que usa para Trabalho/Estudos
    lead_auto.dados_customizados.update({"uso_veiculo": "Locomoção diária (trabalho/estudos)"})
    # NOTE: Neste ponto, a dependência "garagem_trabalho_escola" (que depende de uso_veiculo == Locomoção diária) deve se ativar!
    show_triage_state(lead_auto, "Respondido Uso (Uso diário - Ativa Pergunta de Garagem no Trabalho)", user_input="Uso todo dia para ir trabalhar")

    # Usuário responde se tem garagem
    lead_auto.dados_customizados.update({"garagem_trabalho_escola": "Sim"})
    show_triage_state(lead_auto, "Respondido Garagem no Trabalho", user_input="Sim, o escritório tem garagem fechada")

    db.close()
    print("==========================================================================")
    print("  SIMULAÇÃO CONCLUÍDA COM SUCESSO TOTAL!")
    print("==========================================================================")

if __name__ == "__main__":
    run_step_by_step_triage_simulation()
