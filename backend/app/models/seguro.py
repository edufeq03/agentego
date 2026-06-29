import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base

class LeadSeguro(Base):
    __tablename__ = "leads_seguro"
    id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), primary_key=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    telefone = Column(String(20), nullable=False)
    nome_contato = Column(String(200), nullable=True)
    nome_segurado = Column(String(200), nullable=True)
    relacao_segurado = Column(String(50), nullable=True) # proprio, conjuge, filho, pai, outro
    
    tipo_seguro = Column(String(30), nullable=True) # saude, odontologico, auto, moto, residencial, empresarial, outro
    produto_especifico = Column(String(100), nullable=True)
    
    idade_segurado = Column(Integer, nullable=True)
    tem_cnpj = Column(Boolean, nullable=True)
    e_mei = Column(Boolean, nullable=True)
    tem_plano_anterior = Column(Boolean, nullable=True)
    plano_anterior_nome = Column(String(100), nullable=True)
    mais_de_6_meses = Column(Boolean, nullable=True)
    regiao = Column(String(200), nullable=True)
    hospitais_preferidos = Column(Text, nullable=True)
    
    marca_modelo = Column(String(100), nullable=True)
    ano_fabricacao = Column(Integer, nullable=True)
    ano_modelo = Column(Integer, nullable=True)
    placa = Column(String(10), nullable=True)
    cep_pernoite = Column(String(10), nullable=True)
    uso_veiculo = Column(String(30), nullable=True) # particular, trabalho, aplicativo
    tem_garagem = Column(Boolean, nullable=True)
    condutor_principal = Column(String(200), nullable=True)
    idade_condutor = Column(Integer, nullable=True)
    bonus_classe = Column(Integer, nullable=True)
    
    tipo_imovel = Column(String(30), nullable=True) # casa, apartamento, comercial
    cep_imovel = Column(String(10), nullable=True)
    metragem = Column(Integer, nullable=True)
    imovel_proprio = Column(Boolean, nullable=True)
    
    docs_recebidos = Column(JSONB, default=list) # [{"tipo": "cnh", "recebido_em": "..."}]
    docs_pendentes = Column(JSONB, default=list)
    
    stage = Column(String(30), default='novo') # novo, primeiro_contato, coletando_dados, aguardando_documentos, em_cotacao, proposta_enviada, negociando, fechado, renovacao_pendente, perdido
    canal_entrada = Column(String(20), default='organico') # template, organico
    template_raw = Column(Text, nullable=True)
    resumo_ia = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    
    seguradora_escolhida = Column(String(100), nullable=True)
    valor_proposta = Column(Float, nullable=True)
    data_proposta_enviada = Column(DateTime, nullable=True)
    data_vencimento_apolice = Column(DateTime, nullable=True)
    numero_apolice = Column(String(100), nullable=True)
    
    ultimo_followup_em = Column(DateTime, nullable=True)
    followup_count = Column(Integer, default=0)
    motivo_perda = Column(String(200), nullable=True)
    
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="leads_seguro")
    lead = relationship("Lead", back_populates="seguro")


class DocumentoSeguro(Base):
    __tablename__ = "documentos_seguro"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads_seguro.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    tipo = Column(String(30), nullable=False) # cnh, crlv, rg, cpf, comprovante_residencia, apolice_anterior, fatura_anterior, foto_veiculo, laudo_medico, outro
    arquivo_nome = Column(String(300), nullable=True)
    arquivo_path = Column(String(500), nullable=True)
    arquivo_url = Column(String(500), nullable=True)
    mimetype = Column(String(100), nullable=True)
    ocr_processado = Column(Boolean, default=False)
    ocr_resultado = Column(JSONB, default=dict)
    ocr_confianca = Column(Float, nullable=True)
    recebido_em = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("LeadSeguro")
    empresa = relationship("Empresa")


class FollowupSeguro(Base):
    __tablename__ = "followups_seguro"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads_seguro.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    tipo = Column(String(30), nullable=True) # manual, automatico_sugestao, automatico_enviado
    mensagem = Column(Text, nullable=False)
    enviado_em = Column(DateTime, default=datetime.utcnow)
    resultado = Column(String(30), default='pendente') # respondeu, ignorou, pendente
    
    lead = relationship("LeadSeguro")
    empresa = relationship("Empresa")
