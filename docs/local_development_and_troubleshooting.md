# Guia de Desenvolvimento Local e Troubleshooting

Este documento registra as lições aprendidas durante a configuração do ambiente de desenvolvimento local e a resolução de problemas na VPS para o projeto AgenteGo.

## 1. Ambiente de Desenvolvimento Local

### Ambientes Virtuais (venv)
- **Problema**: Erro ao ativar o ambiente virtual no Linux quando ele foi criado no Windows.
- **Causa**: O `venv` do Windows usa uma estrutura de pastas diferente (`Scripts/` e `Lib/`) da do Linux (`bin/` e `lib/`).
- **Solução**: Sempre crie um novo `venv` ao trocar de sistema operacional:
  ```bash
  rm -rf venv
  python3 -m venv venv
  source venv/bin/activate
  ```

### Variáveis de Ambiente (.env)
- **Local**: Use `localhost` para conectar a serviços rodando via Docker com portas mapeadas.
- **VPS**: Use o nome do container ou a URL pública dependendo da rede Docker.
- **Segurança**: O `JWT_SECRET` é **obrigatório** e deve ter no mínimo **32 caracteres** para que o bot inicie corretamente.

## 2. Webhooks e Integração (WhatsApp)

### BASE_URL
- A variável `BASE_URL` no Bot define o link de Webhook enviado para a Evolution API.
- Se você estiver local, a Evolution (que é externa) não consegue acessar seu `localhost`. Use **Ngrok** para expor sua porta 8000.
- Na VPS, certifique-se de que o `BASE_URL` coincide exatamente com o domínio configurado no seu orquestrador (ex: Easypanel).

### Troubleshooting de Respostas
Se o robô não responder:
1. Verifique se o log do Bot mostra `🌐 [WEBHOOK] Evento recebido`.
2. Se não mostrar, a URL de Webhook na Evolution está errada ou inacessível.
3. Teste a URL do Bot no navegador. Se `/health` ou `/` responderem, a rede está ok.

## 3. Dashboard

### Configuração da API
- **Problema**: Erros 404 constantes nas chamadas do Dashboard.
- **Causa**: URL da API configurada com `/api` no final (ex: `http://localhost:8000/api`) somada ao prefixo que o código já adiciona, gerando URLs inválidas como `/api/api/dashboard`.
- **Solução**: No `.env.local` do Dashboard, a `NEXT_PUBLIC_API_URL` deve ser apenas a base (ex: `http://localhost:8000`).

## 4. Banco de Dados e Compatibilidade

### Estrutura de Configuração
- Durante a evolução do projeto, o campo `conhecimento` no banco de dados mudou de um **Objeto** para um **Array** de tópicos.
- O código do Dashboard foi atualizado com verificações `Array.isArray()` para garantir que dados legados não quebrem a interface ("Agent Builder").

## 5. Comandos Úteis de Diagnóstico

### Verificar usuários e empresas no banco:
```bash
python3 scratch/check_users.py
```

### Validar saúde da infraestrutura:
```bash
python3 scratch/check_infra.py
```

### Ver logs em tempo real na VPS:
```bash
docker logs -f atendia-bot --tail 50
```
