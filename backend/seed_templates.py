from app.database import SessionLocal, PromptTemplate
import uuid

def seed():
    db = SessionLocal()
    try:
        # 1. Template Academia
        academia = db.query(PromptTemplate).filter(PromptTemplate.nicho == "academia").first()
        if not academia:
            academia = db.query(PromptTemplate).filter(PromptTemplate.nome_nicho == "Academia").first()
            if not academia:
                academia = PromptTemplate(nome_nicho="Academia", nicho="academia")
                db.add(academia)
            else:
                academia.nicho = "academia"
        else:
            academia.nome_nicho = "Academia"
            
        academia.prompt_sistema = "Você é uma assistente virtual de atendimento ao público de uma academia. Seu tom é prestativo, amigável e focado em bem-estar. Seu objetivo é acolher os alunos e interessados, tirar dúvidas sobre planos, horários de funcionamento, regras, modalidades e fornecer suporte de forma rápida e eficiente."
        academia.tom_voz = "Prestativo, Acolhedor e Educado"
        academia.missao = "Facilitar o acesso à informação e apoiar a jornada de bem-estar dos alunos."
        academia.objetivo = "Atendimento ao público e suporte geral para tirar dúvidas de alunos e interessados."
        academia.etapas_funil = ["novo", "em_atendimento", "resolvido"]

        # 2. Template Clínica Médica
        clinica = db.query(PromptTemplate).filter(PromptTemplate.nome_nicho == "Clínica").first()
        if not clinica:
            clinica = PromptTemplate(nome_nicho="Clínica")
            db.add(clinica)
        clinica.prompt_sistema = "Você é uma assistente virtual de uma clínica médica. Seu tom é profissional, empático e cuidadoso. Seu objetivo é agendar consultas e triar necessidades básicas."
        clinica.tom_voz = "Profissional e Empático"
        clinica.missao = "Proporcionar saúde e bem-estar com excelência."
        clinica.objetivo = "Marcar consultas médicas."
        clinica.etapas_funil = ["novo", "curioso", "triagem", "agendado"]

        # 3. Template Imobiliária
        imobiliaria = db.query(PromptTemplate).filter(PromptTemplate.nome_nicho == "Imobiliária").first()
        if not imobiliaria:
            imobiliaria = PromptTemplate(nome_nicho="Imobiliária")
            db.add(imobiliaria)
        imobiliaria.prompt_sistema = "Você é uma assistente virtual de uma imobiliária de luxo. Seu tom é elegante, prestativo e focado em detalhes. Seu objetivo é qualificar leads e agendar visitas a imóveis."
        imobiliaria.tom_voz = "Elegante e Sofisticado"
        imobiliaria.missao = "Encontrar o lar dos sonhos para nossos clientes."
        imobiliaria.objetivo = "Agendar visitas a imóveis."
        imobiliaria.etapas_funil = ["novo", "curioso", "qualificado", "visita_marcada"]

        # 4. Template Corretora de Seguros
        corretora = db.query(PromptTemplate).filter(PromptTemplate.nome_nicho == "Corretora de Seguros").first()
        if not corretora:
            corretora = PromptTemplate(nome_nicho="Corretora de Seguros")
            db.add(corretora)
        corretora.prompt_sistema = "Você é um corretor de seguros digital de alta performance. Seu tom é consultivo, profissional e que passa segurança. Seu objetivo é entender as necessidades do cliente, qualificar o lead (coletando dados para cotação) e solicitar o envio de documentos (CNH, CRLV, carteirinha atual) para preparar a melhor proposta de plano de saúde, odonto ou seguro auto/moto."
        corretora.tom_voz = "Consultivo e Seguro"
        corretora.missao = "Proteger o que é mais importante para nossos clientes com transparência e agilidade."
        corretora.objetivo = "Coletar dados para cotação de seguros e solicitar documentos."
        corretora.etapas_funil = ["novo_lead", "em_atendimento", "documentos_pendentes", "em_cotacao"]
        corretora.nicho = "corretora"

        # 5. Template Beleza e Estética
        beleza = db.query(PromptTemplate).filter(PromptTemplate.nicho == "beleza").first()
        if not beleza:
            beleza = PromptTemplate(nome_nicho="Beleza e Estética", nicho="beleza")
            db.add(beleza)
        else:
            beleza.nome_nicho = "Beleza e Estética"
            beleza.nicho = "beleza"
            
        beleza.prompt_sistema = "Você é uma assistente virtual de um salão de beleza e estética. Seu tom é caloroso, amigável e focado em bem-estar. Seu objetivo é ajudar clientes a escolherem serviços, sugerir recorrências e conduzi-los ao agendamento de forma suave e personalizada."
        beleza.tom_voz = "Caloroso, Elegante e Acolhedor"
        beleza.missao = "Realçar a beleza única de cada pessoa com carinho e profissionalismo."
        beleza.objetivo = "Agendar procedimentos de beleza, gerenciar lista de espera e sugerir recorrências."
        beleza.etapas_funil = ["novo", "curioso", "agendado"]

        db.commit()
        print("Templates de nicho semeados com sucesso!")
    except Exception as e:
        print(f"Erro ao semear templates: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
