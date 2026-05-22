# AgenteGo - SaaS de Atendimento Inteligente para Academias

Plataforma multi-tenant para automação de atendimento via WhatsApp utilizando IA (OpenAI) e Evolution API.

## Estrutura do Projeto

- `backend/`: Backend FastAPI (Processamento, IA, Banco de Dados).
- `dashboard/`: Frontend Next.js (Métricas, Configurações, Admin).
- `docker-compose.yml`: Orquestração dos serviços (Bot, DB, Dashboard).

## Como Rodar

1. Configure o arquivo `.env` baseado no `.env.example`.
2. Suba os containers:
   ```bash
   docker compose up -d --build
   ```
3. O bot estará disponível em `http://localhost:8000`.
4. O dashboard estará disponível em `http://localhost:3000`.

## Onboarding de Nova Academia (Passo a Passo)

Para adicionar um novo cliente ao SaaS:

### 1. Criar Empresa e Usuário Admin
Acesse a **Central do Franqueador** em `http://localhost:3000/admin`.
- Use o `ADMIN_TOKEN` configurado no `.env`.
- Clique em "Novo Cliente".
- Escolha um template de nicho (ex: Academia).
- Preencha os dados da unidade e as credenciais de acesso do cliente.

### 2. Configurar WhatsApp (Evolution API)
- Crie uma nova instância na sua Evolution API para a academia.
- Conecte o WhatsApp lendo o QR Code.
- Configure o Webhook na Evolution API apontando para:
  `http://seu-servidor:8000/webhook/{webhook_token}`
  *(O `webhook_token` é gerado automaticamente e pode ser visto no banco de dados ou via API de Admin).*

### 3. Personalizar Regras de Negócio
O cliente pode acessar seu próprio dashboard (`http://localhost:3000/{slug}`) para:
- Alterar preços de mensalidade.
- Atualizar horários de funcionamento.
- Definir a lista de aulas VIP e professores.

## Backup
O sistema possui um script de backup automático do banco de dados em `backend/backup.sh`.
Recomenda-se configurar um cronjob para execução diária.

## Suporte
Em caso de transbordo (atendimento humano), o bot pausará automaticamente e notificará o status no dashboard. Para reativar o bot manualmente, use o botão "Reativar Robô" na tela de conversas.

Para problemas técnicos ou configuração de ambiente, consulte o [Guia de Troubleshooting](docs/local_development_and_troubleshooting.md).
