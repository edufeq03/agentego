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

        # Obter UTMs e flag de recorrência do lead
        utm_source = getattr(lead, "utm_source", None)
        utm_campaign = getattr(lead, "utm_campaign", None)
        canal_entrada = getattr(lead, "canal_entrada", "organico")
        campanha_nome = None
        campanha_desc = None

        if lead and utm_campaign:
            from app.database import SessionLocal, Campanha
            db_session = SessionLocal()
            try:
                camp_obj = db_session.query(Campanha).filter(
                    Campanha.empresa_id == empresa.id,
                    Campanha.codigo_ref == utm_campaign
                ).first()
                if camp_obj:
                    campanha_nome = camp_obj.nome
                    campanha_desc = camp_obj.descricao
            except Exception:
                pass
            finally:
                db_session.close()
        
        recorrente = False
        if lead and getattr(lead, "id", None):
            from app.database import SessionLocal, Mensagem
            db_session = SessionLocal()
            try:
                # É recorrente se houver pelo menos uma mensagem enviada por nós (agente) anteriormente
                recorrente = db_session.query(Mensagem).filter(
                    Mensagem.lead_id == lead.id,
                    Mensagem.tipo == "agente"
                ).count() > 0
            except Exception:
                pass
            finally:
                db_session.close()

        # Carregar campos de triagem dinâmicos da empresa
        campos_pendentes = []
        campos_coletados = []
        if lead and getattr(lead, "id", None):
            from app.database import SessionLocal, CampoCustomizado
            db_session = SessionLocal()
            try:
                # Carregar campos configurados ativos
                db_campos = db_session.query(CampoCustomizado).filter(
                    CampoCustomizado.empresa_id == empresa.id,
                    CampoCustomizado.ativo == True
                ).order_by(CampoCustomizado.ordem.asc(), CampoCustomizado.criado_em.asc()).all()
                
                # Se ainda não existem campos cadastrados no banco (e a rota listar_campos não foi chamada),
                # podemos gerar a lista com base no dicionário dados_customizados do lead (ou usar fallback estático do nicho)
                if len(db_campos) == 0:
                    if empresa.nicho == "corretora":
                        chaves_def = [
                            ("tipo_seguro", "Tipo de Seguro", "opcao_unica", ["Saúde / PME", "Odontológico", "Carro", "Moto"], True),
                            ("nome_segurado", "Nome do Segurado", "texto", None, True),
                            ("idade_segurado", "Idade ou Nascimento", "texto", None, True),
                            ("marca_modelo", "Marca e Modelo do Veículo", "texto", None, False),
                            ("ano_fabricacao", "Ano de Fabricação", "numero", None, False),
                            ("cep_pernoite", "CEP de Pernoite", "texto", None, False),
                            ("uso_veiculo", "Uso do Veículo", "opcao_unica", ["particular", "trabalho", "aplicativo"], False),
                            ("tem_garagem", "Possui Garagem?", "booleano", None, False),
                        ]
                    elif empresa.nicho in ("generico", "academia"):
                        chaves_def = [
                            ("nome_completo", "Nome Completo", "texto", None, True),
                            ("idade", "Idade", "texto", None, True),
                            ("objetivo", "Objetivo do Treino", "opcao_unica", ["Emagrecimento", "Ganho de Massa", "Condicionamento"], False),
                            ("frequencia", "Frequência Pretendida", "opcao_unica", ["1 a 2 dias", "3 a 4 dias", "5+ dias"], False),
                        ]
                    else:
                        chaves_def = [
                            ("nome_completo", "Nome Completo", "texto", None, True),
                            ("objetivo_contato", "Objetivo do Contato", "texto", None, True),
                        ]
                    
                    db_campos = [
                        CampoCustomizado(empresa_id=empresa.id, chave=k, label=l, tipo=t, opcoes=o, obrigatorio=ob)
                        for k, l, t, o, ob in chaves_def
                    ]
                
                # Mapear dados coletados do JSONB
                dados_lead = getattr(lead, "dados_customizados", {}) or {}
                
                # Se for corretora, enriquecer com dados físicos de lead_seguro
                if empresa.nicho == "corretora" and lead_seguro:
                    for attr in ["tipo_seguro", "marca_modelo", "cep_pernoite", "uso_veiculo", "tem_garagem"]:
                        val_fisico = getattr(lead_seguro, attr, None)
                        if val_fisico is not None and attr not in dados_lead:
                            dados_lead[attr] = val_fisico
                    if getattr(lead_seguro, "nome_segurado", None) and "nome_segurado" not in dados_lead:
                        dados_lead["nome_segurado"] = lead_seguro.nome_segurado
                    if getattr(lead_seguro, "idade_segurado", None) and "idade_segurado" not in dados_lead:
                        dados_lead["idade_segurado"] = lead_seguro.idade_segurado

                for campo in db_campos:
                    valor = dados_lead.get(campo.chave)
                    
                    # Formatar visualmente a regra do campo
                    regra_desc = f"- {campo.label} (Chave: {campo.chave})"
                    if campo.obrigatorio:
                        regra_desc += " [OBRIGATÓRIO]"
                    if campo.tipo == "opcao_unica" and campo.opcoes:
                        regra_desc += f" (Opções permitidas: {', '.join(campo.opcoes)})"
                    elif campo.tipo == "booleano":
                        regra_desc += " (Responda apenas Sim/Não)"
                    elif campo.tipo == "numero":
                        regra_desc += " (Responda apenas número inteiro)"
                        
                    if valor is not None and valor != "":
                        if isinstance(valor, bool):
                            valor = "Sim" if valor else "Não"
                        campos_coletados.append(f"- {campo.label}: {valor}")
                    else:
                        campos_pendentes.append(regra_desc)
            except Exception as ex_context:
                import logging
                logging.getLogger("uvicorn").error(f"Erro ao computar campos dinâmicos no contexto: {ex_context}")
            finally:
                db_session.close()

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
            
            # Rastreamento de Campanhas e Recorrência
            "campanha": {
                "codigo": utm_campaign,
                "origem": utm_source,
                "canal": canal_entrada,
                "nome": campanha_nome,
                "descricao": campanha_desc
            },
            "lead_recorrente": recorrente,

            # Triagem Dinâmica de Campos
            "triagem_dinamica": {
                "campos_pendentes": "\n".join(campos_pendentes) if campos_pendentes else "Todos os dados já foram coletados com sucesso!",
                "campos_coletados": "\n".join(campos_coletados) if campos_coletados else "Nenhum dado coletado ainda."
            },

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
