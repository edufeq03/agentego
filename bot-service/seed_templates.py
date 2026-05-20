from app.database import SessionLocal, PromptTemplate
import uuid

def seed():
    db = SessionLocal()
    try:
        # 1. Template Academia
        academia = db.query(PromptTemplate).filter(PromptTemplate.nome_nicho == "Academia").first()
        if not academia:
            academia = PromptTemplate(nome_nicho="Academia")
            db.add(academia)
        academia.prompt_sistema = "Você é uma assistente virtual de uma academia de alta performance. Seu tom é motivador, amigável e focado em saúde. Seu objetivo é tirar dúvidas de interessados e apresentar a academia, convidando-os de forma natural e acolhedora a fazer uma visita, sem ser inconveniente ou insistente."
        academia.tom_voz = "Motivador e Energético"
        academia.missao = "Transformar vidas através do exercício físico."
        academia.objetivo = "Tirar dúvidas e convidar para conhecer a academia de forma natural."
        academia.etapas_funil = ["novo", "curioso", "interessado", "agendado"]

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

        db.commit()
        print("Templates de nicho semeados com sucesso!")
    except Exception as e:
        print(f"Erro ao semear templates: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
