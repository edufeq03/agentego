from datetime import datetime
import pytz

class ContextoAgent:
    """
    Monta o contexto completo para o agente especialista.
    Sem chamadas de IA — apenas organização de dados.
    """
    nome = "ContextoAgent"

    def montar(
        self,
        empresa,
        lead,
        lead_seguro,        # None se não for corretora
        triagem: dict,
        config: dict,
        documentos_legais: list = None
    ) -> dict:
        """
        Retorna um dicionário de contexto rico para o especialista.
        """
        fuso = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso)

        ctx = {
            # Empresa e configuração
            "nicho": empresa.nicho or "generico",
            "config": config,
            "nome_empresa": config.get("nome_empresa", empresa.nome),
            "nome_agente": config.get("nome_agente", "Rosana"),

            # Lead base
            "lead_id": str(lead.id) if lead else None,
            "telefone": lead.telefone if lead else None,
            "stage": lead.stage if lead else "novo",
            "lead_nome": lead.nome if lead else None,

            # Triagem
            "intencao": triagem.get("intencao", "duvida"),
            "sentimento": triagem.get("sentimento", "neutro"),
            "urgente": triagem.get("urgente", False),
            "resumo_triagem": triagem.get("resumo_curto", ""),

            # Tempo
            "contexto_tempo": self._formatar_tempo(agora, config),

            # Nicho específico
            "dados_lead_seguro": None,
            "docs_pendentes": None,
            "documentos_legais": documentos_legais or [],
        }

        # Enriquecer com dados de lead_seguro (corretora)
        if lead_seguro:
            ctx["dados_lead_seguro"] = self._formatar_lead_seguro(lead_seguro)
            docs_p = lead_seguro.docs_pendentes or []
            ctx["docs_pendentes"] = (
                ", ".join(docs_p) if docs_p
                else "Nenhum documento pendente."
            )

        return ctx

    def _formatar_tempo(self, agora, config) -> str:
        dia_semana = agora.strftime("%A")
        hora = agora.strftime("%H:%M")
        return f"Data/Hora atual: {agora.strftime('%d/%m/%Y %H:%M')} (Brasília)"

    def _formatar_lead_seguro(self, lead_seguro) -> str:
        """Formata dados do lead de seguro para injeção no prompt."""
        campos = [
            ("nome_segurado", "Nome do Segurado"),
            ("tipo_seguro", "Tipo de Seguro"),
            ("produto_especifico", "Produto"),
            ("relacao_segurado", "Relação com segurado"),
            ("idade_segurado", "Idade"),
            ("regiao", "Região"),
            ("hospitais_preferidos", "Hospitais preferidos"),
            ("tem_cnpj", "Tem CNPJ"),
            ("e_mei", "É MEI"),
            ("tem_plano_anterior", "Plano anterior"),
            ("plano_anterior_nome", "Nome do plano anterior"),
            ("mais_de_6_meses", "Sem plano há +6 meses"),
            ("marca_modelo", "Veículo"),
            ("placa", "Placa"),
            ("cep_pernoite", "CEP pernoite"),
            ("uso_veiculo", "Uso do veículo"),
            ("tem_garagem", "Tem garagem"),
            ("condutor_principal", "Condutor principal"),
            ("idade_condutor", "Idade do condutor"),
            ("bonus_classe", "Classe de bônus"),
        ]
        linhas = []
        for campo, label in campos:
            valor = getattr(lead_seguro, campo, None)
            if valor is not None:
                if isinstance(valor, bool):
                    valor = "Sim" if valor else "Não"
                linhas.append(f"- {label}: {valor}")
        return "\n".join(linhas) if linhas else "Nenhum dado coletado ainda."

contexto_agent = ContextoAgent()
