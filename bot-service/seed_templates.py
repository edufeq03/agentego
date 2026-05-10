from app.database import SessionLocal, PromptTemplate
import uuid

def seed():
    db = SessionLocal()
    try:
        # 1. Template Academia
        if not db.query(PromptTemplate).filter(PromptTemplate.nome_nicho == "Academia").first():
            academia = PromptTemplate(
                nome_nicho="Academia",
                prompt_sistema="Você é uma assistente virtual de uma academia de alta performance. Seu tom é motivador, amigável e focado em saúde. Seu objetivo é converter interessados em visitas presenciais.",
                tom_voz="Motivador e Energético",
                missao="Transformar vidas através do exercício físico.",
                objetivo="Agendar visitas experimentais.",
                etapas_funil=["novo", "curioso", "interessado", "agendado"]
            )
            db.add(academia)

        # 2. Template Clínica Médica
        if not db.query(PromptTemplate).filter(PromptTemplate.nome_nicho == "Clínica").first():
            clinica = PromptTemplate(
                nome_nicho="Clínica",
                prompt_sistema="Você é uma assistente virtual de uma clínica médica. Seu tom é profissional, empático e cuidadoso. Seu objetivo é agendar consultas e triar necessidades básicas.",
                tom_voz="Profissional e Empático",
                missao="Proporcionar saúde e bem-estar com excelência.",
                objetivo="Marcar consultas médicas.",
                etapas_funil=["novo", "curioso", "triagem", "agendado"]
            )
            db.add(clinica)

        # 3. Template Imobiliária
        if not db.query(PromptTemplate).filter(PromptTemplate.nome_nicho == "Imobiliária").first():
            imobiliaria = PromptTemplate(
                nome_nicho="Imobiliária",
                prompt_sistema="Você é uma assistente virtual de uma imobiliária de luxo. Seu tom é elegante, prestativo e focado em detalhes. Seu objetivo é qualificar leads e agendar visitas a imóveis.",
                tom_voz="Elegante e Sofisticado",
                missao="Encontrar o lar dos sonhos para nossos clientes.",
                objetivo="Agendar visitas a imóveis.",
                etapas_funil=["novo", "curioso", "qualificado", "visita_marcada"]
            )
            db.add(imobiliaria)

        db.commit()
        print("Templates de nicho semeados com sucesso!")
    except Exception as e:
        print(f"Erro ao semear templates: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
