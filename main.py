
import os
import logging
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
SUPPORT_URL = os.getenv(
    "SUPPORT_URL",
    "https://t.me/jogomanga_Rowen"
).strip()

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ==========================================
# RESPOSTAS AUTOMÁTICAS DA JOGO MANGA
# ==========================================

def responder(mensagem):

    texto = (mensagem or "").lower().strip()

    # SAUDAÇÕES
    if any(p in texto for p in [
        "oi", "olá", "ola", "bom dia",
        "boa tarde", "boa noite"
    ]):
        return (
            "Olá! Seja bem-vindo ao suporte oficial da Jogo Manga.\n\n"
            "Estamos aqui para ajudar.\n\n"
            "Selecione uma opção:\n\n"
            "1️⃣ Bônus e promoções\n"
            "2️⃣ Depósitos\n"
            "3️⃣ Saques\n"
            "4️⃣ Conta e acesso\n"
            "5️⃣ Atendimento humano\n\n"
            "Digite o número correspondente ou escreva sua dúvida."
        )

    # MENU NUMÉRICO
    if texto == "1":
        return (
            "🎁 BÔNUS E PROMOÇÕES\n\n"
            "Para consultar um bônus ou benefício VIP, "
            "informe seu usuário e o nome da promoção.\n\n"
            "Nossa equipe poderá confirmar as condições.\n\n"
            "Atendimento: " + SUPPORT_URL
        )

    if texto == "2":
        return (
            "💳 DEPÓSITOS\n\n"
            "Se realizou um depósito e o valor ainda não apareceu "
            "na sua conta, entre em contato com nossa equipe.\n\n"
            "Tenha em mãos o valor, horário e comprovante. "
            "Oculte informações bancárias sensíveis.\n\n"
            "Atendimento: " + SUPPORT_URL
        )

    if texto == "3":
        return (
            "💰 SAQUES\n\n"
            "Para consultar uma solicitação de saque, "
            "informe seu usuário, valor e horário da solicitação "
            "à nossa equipe.\n\n"
            "Atendimento: " + SUPPORT_URL
        )

    if texto == "4":
        return (
            "🔐 CONTA E ACESSO\n\n"
            "Está enfrentando dificuldades para acessar sua conta "
            "ou realizar um cadastro?\n\n"
            "Descreva o problema apresentado na tela.\n\n"
            "Nunca envie sua senha ou códigos de segurança.\n\n"
            "Atendimento: " + SUPPORT_URL
        )

    if texto == "5":
        return (
            "👨‍💻 ATENDIMENTO HUMANO\n\n"
            "Para falar diretamente com nossa equipe, "
            "acesse o canal de atendimento:\n\n"
            + SUPPORT_URL
        )

    # IDENTIFICAÇÃO DE ASSUNTOS

    if any(p in texto for p in [
        "bônus", "bonus", "promoção",
        "promocao", "vip", "benefício"
    ]):
        return (
            "Para consultar bônus e benefícios VIP, "
            "informe seu usuário e qual promoção deseja verificar.\n\n"
            "Atendimento: " + SUPPORT_URL
        )

    if any(p in texto for p in [
        "depósito", "deposito", "pix",
        "depositar", "pagamento"
    ]):
        return (
            "Se o depósito foi debitado e não apareceu na conta, "
            "entre em contato com nossa equipe e informe o valor, "
            "horário e comprovante.\n\n"
            "Atendimento: " + SUPPORT_URL
        )

    if any(p in texto for p in [
        "saque", "retirada", "retirar",
        "sacar", "transferência"
    ]):
        return (
            "Para verificar seu saque, fale com nossa equipe "
            "informando seu usuário, valor e horário da solicitação.\n\n"
            "Atendimento: " + SUPPORT_URL
        )

    if any(p in texto for p in [
        "senha", "login", "entrar",
        "acesso", "cadastro", "conta"
    ]):
        return (
            "Descreva o problema que está enfrentando "
            "ao acessar sua conta.\n\n"
            "Por segurança, nunca envie sua senha "
            "ou códigos de autenticação.\n\n"
            "Atendimento: " + SUPPORT_URL
        )

    if any(p in texto for p in [
        "atendente", "humano",
        "pessoa", "suporte"
    ]):
        return (
            "Para falar com um atendente da Jogo Manga, "
            "acesse:\n\n" + SUPPORT_URL
        )

    # RESPOSTA PADRÃO

    return (
        "Obrigado por entrar em contato com a Jogo Manga!\n\n"
        "Não encontrei uma resposta automática para sua dúvida.\n\n"
        "Você pode selecionar uma das opções:\n\n"
        "1️⃣ Bônus e promoções\n"
        "2️⃣ Depósitos\n"
        "3️⃣ Saques\n"
        "4️⃣ Conta e acesso\n"
        "5️⃣ Atendimento humano\n\n"
        "Se preferir, fale diretamente com nossa equipe:\n"
        + SUPPORT_URL
    )


# ==========================================
# ENVIO DE MENSAGENS AO TELEGRAM
# ==========================================

def enviar_mensagem(
    chat_id,
    mensagem,
    business_connection_id=None
):

    if not BOT_TOKEN:
        logging.error(
            "TELEGRAM_BOT_TOKEN não configurado."
        )
        return

    dados = {
        "chat_id": chat_id,
        "text": mensagem
    }

    if business_connection_id:
        dados["business_connection_id"] = (
            business_connection_id
        )

    resposta = requests.post(
        TELEGRAM_API + "/sendMessage",
        json=dados,
        timeout=20
    )

    resposta.raise_for_status()


# ==========================================
# VERIFICAÇÃO DO SERVIDOR
# ==========================================

@app.route("/", methods=["GET"])
def inicio():

    return jsonify({
        "status": "online",
        "bot": "Jogo Manga",
        "modo": "atendimento_automatico_gratuito"
    })


# ==========================================
# WEBHOOK DO TELEGRAM
# ==========================================

@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def telegram_webhook():

    # Proteção opcional do webhook.
    # Se WEBHOOK_SECRET estiver configurado no Render,
    # precisa ser exatamente igual ao segredo do setWebhook.

    segredo = os.getenv(
        "WEBHOOK_SECRET", ""
    ).strip()

    if segredo:

        recebido = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token",
            ""
        )

        if recebido != segredo:

            logging.warning(
                "Webhook recusado: secret token não confere."
            )

            return jsonify({
                "ok": False,
                "error": "unauthorized"
            }), 403

    atualizacao = request.get_json(
        silent=True
    ) or {}

    mensagem = (
        atualizacao.get("business_message")
        or atualizacao.get("message")
    )

    if not mensagem:
        return jsonify({"ok": True})

    chat = mensagem.get("chat") or {}

    chat_id = chat.get("id")

    if not chat_id:
        return jsonify({"ok": True})

    if chat.get("type") != "private":
        return jsonify({"ok": True})

    remetente = mensagem.get("from") or {}

    if remetente.get("is_bot"):
        return jsonify({"ok": True})

    texto = (
        mensagem.get("text")
        or mensagem.get("caption")
        or ""
    )

    if texto:

        resposta = responder(texto)

    else:

        resposta = (
            "No momento, consigo atender mensagens de texto.\n\n"
            "Descreva sua dúvida ou fale com nossa equipe:\n"
            + SUPPORT_URL
        )

    try:

        enviar_mensagem(
            chat_id,
            resposta,
            mensagem.get("business_connection_id")
        )

    except Exception:

        logging.exception(
            "Erro ao enviar mensagem ao Telegram."
        )

        return jsonify({
            "ok": False
        }), 500

    return jsonify({
        "ok": True
    })


# ==========================================
# INICIALIZAÇÃO
# ==========================================

if __name__ == "__main__":

    porta = int(
        os.getenv("PORT", "10000")
    )

    app.run(
        host="0.0.0.0",
        port=porta
    )

