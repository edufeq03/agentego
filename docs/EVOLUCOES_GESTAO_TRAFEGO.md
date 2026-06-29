# Evoluções Futuras: Módulo de Gestão de Tráfego e ROI

Este documento registra as ideias e arquiteturas propostas para a próxima fase de desenvolvimento do AgenteGo, focada em fornecer métricas de conversão e ROI (Return on Investment) para gestores de tráfego.

## O Problema Atual
Gestores de tráfego geram dezenas de leads através de campanhas (Facebook Ads, Google Ads). Atualmente, é difícil provar para o dono da empresa quantos desses leads realmente se converteram em "vendas no caixa", pois o tráfego apenas contabiliza "cliques" e "mensagens iniciadas".

## A Fundação Existente
O AgenteGo já possui toda a base de dados necessária para este rastreamento "Ponta a Ponta" (End-to-End Tracking):
1. **Atribuição Automática (UTM):** O script `pipeline.py` lê a primeira mensagem do WhatsApp (ex: "Olá, vim pelo anúncio de Verão") e salva automaticamente nas colunas `utm_source` e `utm_campaign` da tabela `leads`.
2. **Qualificação Automática:** A IA qualifica o lead, coletando dados e intenções.
3. **Conversão de Vendas (CRM):** O painel Kanban permite ao vendedor arrastar a oportunidade para "Ganho" e preencher o valor real (`value`) do negócio fechado.

## Próximos Passos de Implementação (To-Do)

### 1. Novo Painel: "ROI & Campanhas"
Criar uma nova aba no Dashboard (ex: `/metrics/roi` ou dentro de CRM) dedicada a relatórios de tráfego.

**Métricas a serem exibidas:**
- **Volume de Leads por Campanha:** Quantos leads entraram com cada `utm_campaign`.
- **Taxa de Qualificação:** Quantos leads da campanha X viraram oportunidades (CrmDeal).
- **Vendas Reais (Conversão):** Quantas oportunidades da campanha X chegaram à coluna "Ganho" no Kanban.
- **Receita Gerada (ROAS):** Soma do campo `value` das oportunidades "Ganhos" agrupadas por campanha.

### 2. Funil Visual Ponta a Ponta
Um gráfico de funil para o gestor tirar print e mandar para o cliente:
`50 Cliques/Leads ➡️ 10 Oportunidades ➡️ 2 Vendas Fechadas ➡️ Faturamento R$ 3.000,00`

### 3. Melhorias no Backend
- Criar um endpoint `GET /api/crm/reports/roi` que faça um JOIN entre `leads`, `crm_contacts` e `crm_deals`.
- Agrupar os resultados por `utm_campaign` e `utm_source`.
- Calcular os valores totais agregados (`SUM(crm_deals.value)`).

## Conclusão
Com essas implementações, o AgenteGo deixa de ser apenas uma ferramenta de atendimento e se consolida como um **CRM de Atribuição de Marketing**, entregando valor extremo para agências e gestores de tráfego.
