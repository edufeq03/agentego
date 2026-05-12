# Troubleshooting e Aprendizados de Produção - AgenteGo

Este documento registra as principais dificuldades e soluções encontradas durante a migração para o ambiente de produção e o rebranding para AgenteGo.

## 1. Gestão de Logs e Performance
### Problema
O log do container de backend ficava saturado ("metralhadora de logs") devido ao volume de webhooks enviados pela Evolution API (eventos de leitura, status, digitação, etc) e pelo polling constante do Dashboard (status do WhatsApp e novas mensagens).

### Solução
- Implementação de um filtro no middleware `log_requests` do FastAPI que ignora requisições com status 200 para caminhos que começam com `/webhook`, `/api/dashboard/whatsapp/status` e `/api/dashboard/conversas`.
- Adição de logs visuais e amigáveis (`📩`, `🤖`, `✅`) para rastrear o fluxo real de mensagens sem poluição técnica.

## 2. Conectividade e Webhooks (Evolution API)
### Problema
O robô recebia mensagens mas não respondia, ou os webhooks não chegavam ao servidor.
### Causas Comuns
1. **BASE_URL Incorreta:** A variável `BASE_URL` no `.env` deve ser o endereço público da API do Bot. Se estiver errada, a Evolution API tentará enviar mensagens para um destino inexistente.
2. **Sincronização de Instância:** Sempre que a URL do servidor mudar, é necessário forçar uma sincronização da instância para atualizar o endpoint de Webhook na Evolution.

### Solução
- O backend agora realiza um "Upsert" do Webhook sempre que o status da conexão é verificado e detectado como conectado.
- Adição de log de depuração mostrando a `Base URL` extraída para validar o `.env`.

## 3. Integridade de Dados (SaaS Multi-Tenant)
### Problema
Erro `NotNullViolation` ou `IntegrityError` ao tentar excluir uma Empresa ou Lead, devido a relacionamentos órfãos em mensagens e eventos.
### Solução
- Configuração de `cascade="all, delete-orphan"` em todos os relacionamentos da `Empresa` no `database.py`. Isso garante que ao deletar uma empresa, todos os leads, mensagens e eventos vinculados sejam limpos automaticamente.

## 4. Estabilidade da IA e Timeouts
### Problema
O processamento em background travava silenciosamente ou exibia erros de `Read timed out` ao tentar falar com a Evolution API.
### Solução
- **Unpacking de Funções:** Garantir que todas as funções de IA (`analisar_sentimento_ia`, `processar_mensagem_dinamica`) retornem consistentemente o mesmo número de valores (ex: `sentimento, prompt_tokens, completion_tokens`).
- **Resiliência:** Aumento do timeout para requisições de presença (digitando/gravando) para 5 segundos e redução da severidade do log para `WARNING` em caso de falha, para não interromper o fluxo principal.

## 5. Rebranding (AgenteGo)
### Checklist de Troca de Marca
- [x] Atualizar nomes na Landing Page.
- [x] Atualizar nomes e títulos no Dashboard.
- [x] Alterar chaves de `localStorage` (ex: `atendia_token` -> `agentego_token`) para evitar conflitos de sessão.
- [x] Configurar CORS para os novos domínios (com e sem `www`).

---
*Última atualização: 2026-05-11*
