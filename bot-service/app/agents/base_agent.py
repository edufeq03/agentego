from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Interface comum para todos os agentes.
    Garante que qualquer especialista pode ser plugado
    no pipeline sem alterar o orquestrador.
    """
    nome: str = "BaseAgent"

    @abstractmethod
    def processar(
        self,
        mensagem: str,
        contexto: dict,
        historico: list
    ) -> tuple[str, int, int]:
        """
        Processa a mensagem e retorna:
          - resposta (str): texto da resposta
          - tokens_in (int): tokens de entrada consumidos
          - tokens_out (int): tokens de saída consumidos
        """
        pass

    def montar_historico_openai(self, historico: list) -> list:
        """Converte histórico do banco para formato OpenAI."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in historico
            if m.get("content")
        ]
