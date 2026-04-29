RESPOSTAS = {
    "HORARIO": "Funcionamos de segunda a sexta, das 08:00 às 22:00 e sábados das 09:00 às 13:00.",
    "PRECO": "Temos o plano Básico (R$80) e o VIP (R$150 com aulas coletivas).",
    "LOCALIZACAO": "Estamos localizados na Avenida Principal, 1000. Temos estacionamento no local!",
    "AULA_EXPERIMENTAL": "Claro! Você tem direito a 1 dia grátis para conhecer a academia. É só trazer um documento com foto.",
    "AULAS_COLETIVAS": "Oferecemos aulas de Spinning, Zumba, Crossfit e Pilates. Todas estão inclusas no plano VIP!",
    "CANCELAMENTO": "O cancelamento pode ser feito a qualquer momento na recepção, sem multa para planos mensais.",
    "FORMAS_PAGAMENTO": "Aceitamos Cartão de Crédito (recorrente, não prende o limite), PIX, Gympass e TotalPass.",
    "SAUDACAO": "Olá! Sou o assistente virtual da academia. Posso tirar suas dúvidas sobre planos, horários, aulas e muito mais. Como posso te ajudar?"
}

def gerar_resposta(intencao):
    fallback = "Não entendi muito bem. Posso ajudar com planos, horários, localização, aulas e Gympass. O que deseja saber?"
    return RESPOSTAS.get(intencao, fallback)