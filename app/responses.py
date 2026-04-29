def gerar_resposta(intencao):
    if intencao == "HORARIO":
        return "Funcionamos de segunda a sexta, das 08:00 às 22:00."
    
    elif intencao == "PRECO":
        return "Temos plano simples por R$80 e completo por R$150."
    
    else:
        return "Posso te ajudar com horários e valores. O que você gostaria de saber?"