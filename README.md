# Jogo Manga — Suporte IA para Telegram

## O que este projeto faz
- Recebe mensagens privadas do bot pelo webhook do Telegram.
- Também processa `business_message`, quando o bot estiver conectado a uma conta Telegram Business.
- Gera respostas com a API da OpenAI.
- Usa o link de suporte humano configurado.
- Não solicita senhas, códigos de autenticação nem pagamentos.

## Importante antes de publicar
1. O token que foi compartilhado no chat deve ser revogado no **@BotFather** (`/revoke`) e substituído por um token novo.
2. Crie uma chave da API da OpenAI em https://platform.openai.com/api-keys. A API é cobrada separadamente da assinatura do ChatGPT.
3. Crie uma conta no Render e publique este projeto como um Web Service.
4. Configure as variáveis de ambiente indicadas abaixo. Nunca coloque tokens no código nem envie-os em mensagens.

## Publicação no Render
1. Extraia este ZIP e envie a pasta para um repositório privado no GitHub.
2. No Render, escolha **New + → Blueprint** e conecte o repositório.
3. O Render identificará o `render.yaml`. Preencha `TELEGRAM_BOT_TOKEN` e `OPENAI_API_KEY` em Environment.
4. Após a implantação, copie a URL HTTPS do serviço, por exemplo `https://seu-servico.onrender.com`.
5. Configure o webhook substituindo `SEU_TOKEN`, `SUA_URL` e `SEU_SEGREDO` pelos valores corretos:

```bash
curl -X POST "https://api.telegram.org/botSEU_TOKEN/setWebhook" \
  -d "url=SUA_URL/telegram/webhook" \
  -d 'allowed_updates=["message","business_message","business_connection"]' \
  -d "secret_token=SEU_SEGREDO"
```

O `WEBHOOK_SECRET` precisa ser exatamente o mesmo valor usado em `secret_token`.

## Como conectar ao Telegram Business
- Na conta que receberá o atendimento, abra **Configurações → Telegram Business → Chatbots**.
- Adicione o bot e autorize o acesso às conversas que ele deverá atender.
- O bot precisa suportar Business Mode e a conta precisa ter o recurso Telegram Business disponível.
- Para atendimento apenas pelo perfil do bot, os jogadores precisam abrir o chat do bot e enviar uma mensagem; o bot não responde a mensagens recebidas na conta pessoal sem a conexão Business.

## Limitação do plano gratuito
O serviço gratuito do Render pode entrar em suspensão após inatividade e pode ter limites de uso. Portanto, não é uma garantia de atendimento ininterrupto 24/7. Para operação contínua, considere um plano pago ou outro servidor sempre ativo.

## Personalização
Edite `SYSTEM_PROMPT` em `main.py` para adicionar regras oficiais, valores e horários confirmados da Jogo Manga. Não inclua senhas, tokens ou dados pessoais de jogadores no prompt.

## Teste
Abra `https://SUA_URL/` e confirme que aparece `{"status":"ok"...}`. Depois envie uma mensagem ao bot no Telegram.
