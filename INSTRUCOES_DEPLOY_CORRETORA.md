# Instruções para Deploy e Teste em Produção (Nicho Corretora)

Como o nosso código já isola os clientes pelo nicho (`empresa_id` e `nicho == 'corretora'`), subir esta atualização **não afetará a sua academia que já está em produção**. 

Aqui está o passo a passo para você aplicar a atualização no seu servidor de produção de forma segura:

### 1. Atualizar o Código no Servidor
Acesse o terminal do seu servidor de produção e atualize o código:
```bash
git pull origin main
```

### 2. Atualizar o Banco de Dados (Migrações)
Como criamos tabelas exclusivas para o nicho de seguros (`leads_seguro` e `documentos_seguro`), você precisa rodar o script de migração:
```bash
cd bot-service
python migrate_db.py
```

### 3. Inserir o Template da Corretora
Rode o script que atualizamos para inserir o template da "Corretora de Seguros" no banco de dados de produção:
```bash
python seed_templates.py
```

### 4. Reiniciar os Serviços
Após atualizar o código e o banco, reinicie o seu backend (Python/FastAPI) e o frontend (Next.js):
* **Backend:** `sudo systemctl restart seu-servico-backend` (ou reinicie via Docker/PM2).
* **Frontend:**
  ```bash
  cd ../dashboard
  npm run build
  # Reinicie o PM2 ou o serviço que roda o Next.js
  pm2 restart dashboard
  ```

### 5. Validando em Produção (Passo a Passo Seguro)
1. Acesse o **Painel Admin** em produção.
2. Crie uma **Nova Empresa** com o nicho **Corretora de Seguros (Gestão de Leads)**.
3. Faça login no Dashboard da Corretora.
4. Vá na aba **WhatsApp** e conecte um **número de telefone de teste** (nunca o mesmo da academia).
5. **MUITO IMPORTANTE:** Assim que o status ficar "Conectado", clique no botão azul **Sincronizar Eventos**. Isso fará a Evolution API ativar o recebimento de mensagens (Webhooks) para este número específico.
6. Envie um "Olá" de outro celular para o número de teste e veja a IA responder como corretora.
7. Envie uma foto genérica de CNH para testar se o pipeline de OCR extrai os dados corretamente e atualiza o lead no Dashboard.

Bom descanso! Quando voltar, siga essas instruções e qualquer dúvida é só me chamar.
