
import os
import re
import time
import threading
import logging
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# CONFIGURAÇÕES
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# CONTROLE DE ATENDIMENTO
atendimentos = {}
timers_inatividade = {}
timers_saque = {}
lock = threading.RLock()

TEMPO_INATIVIDADE = 300  # 5 minutos
TEMPO_SAQUE = 120        # 2 minutos


# MENU PRINCIPAL
MENU = """Olá, sou a Lia, assistente virtual da Jogomanga! Estou aqui para ajudar. Selecione o tópico sobre o qual deseja tirar dúvidas:

1️⃣ Recompensas e Promoções
2️⃣ Questões relacionadas a parcerias
3️⃣ Problemas com saques
4️⃣ Conta e acesso
5️⃣ Suporte humano
6️⃣ Meu grupo VIP

Digite o número da opção desejada."""


# RESPOSTAS DAS OPÇÕES
RESPOSTAS = {
    "1": """Lia Support (IA) Oficial: Para qualquer dúvida sobre recompensas, entre em contato com esta especialista em recompensas para obter ajuda. Obrigada! https://t.me/Simmyonly""",

    "2": """Lia Support (IA) Oficial: Telegram: https://t.me/lancamentosmanga Participe deste grupo para saber mais sobre parcerias com as plataformas MANGA e T1. Obrigada!""",

    "3": """Lia Support (IA) Oficial: Inclua um código de comando começando com a letra W em sua solicitação de saque.""",

    "4": """Lia Support (IA) Oficial: Descreva seu problema detalhadamente para que possamos entender melhor e ajudá-lo(a).""",

    "5": """Lia Support (IA) Oficial: Aguarde um momento enquanto encaminhamos sua solicitação para nossa equipe de atendimento ao cliente.""",

    "6": """Lia Support (IA) Oficial: Para qualquer dúvida sobre recompensas, entre em contato com este especialista em recompensas para obter ajuda. Obrigado! https://t.me/Simmyonly"""
}


# RESPOSTA APÓS 2 MINUTOS DO CÓDIGO W
RESPOSTA_SAQUE_PROCESSANDO = """Lia Support (IA) Oficial: Aguarde, seu saque está sendo processado. Os fundos chegarão em breve. Notificaremos você dentro de 10 minutos a 24 horas. Caso não tenha recebido seu pagamento, verifique novamente para obter uma atualização de confirmação. Agradecemos sua paciência."""


# ENCERRAMENTO POR INATIVIDADE
RESPOSTA_INATIVIDADE = """Lia Support (IA) Oficial: Olá, detectamos que você não respondeu. Devido à falta de comunicação, encerramos a conversa. Obrigado! Se desejar retornar ao menu, digite "menu"."""


# PALAVRAS-CHAVE CADASTRADAS
RESPOSTAS_PALAVRAS = [
    (
        ["bonus", "bônus", "recompensa", "recompensas", "promoção", "promocao"],
        """Para qualquer dúvida sobre bônus, entre em contato com este especialista em bônus para obter consultoria. Obrigado! https://t.me/Simmyonly"""
    ),
    (
        ["cooperação", "cooperacao", "parceria", "parcerias"],
        """Telegram: https://t.me/lancamentosmanga
Entre no chat para colaborações com as plataformas MANGA e T1, obrigado!"""
    ),
    (
        ["grupo vip"],
        """Se você ainda tiver dúvidas sobre sua categoria, entre em contato com Simmy. https://t.me/Simmyonly"""
    ),
    (
        [
            "não estou conseguindo sacar o dinheirinho que depositei",
            "nao estou conseguindo sacar o dinheirinho que depositei"
        ],
        """Olá, nosso plataforma possui um mecanismo de rollover. Isso significa que, após o seu depósito, você precisa apostar um montante igual ao valor depositado para cumprir os requisitos de rollover e desbloquear a barra de progresso.
Por exemplo: se você depositar 50 yuan, precisará acumular apostas de 50 yuan. Não é necessário apostar tudo de uma vez; você pode fazer apostas em várias etapas, gradualmente, até atingir o requisito e completar a barra de progresso de rollover."""
    ),
    (
        [
            "problemas no saque",
            "problema no saque",
            "meu saque não caiu",
            "meu saque nao caiu",
            "meu saque está demorando",
            "meu saque esta demorando"
        ],
        """Por favor, forneça o código de comando começando com a letra W em seu pedido de saque."""
    )
]


def enviar_mensagem(chat_id, mensagem, business_connection_id=None):
    if not BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN não configurado.")
        return

    dados = {
        "chat_id": chat_id,
        "text": mensagem
    }

    if business_connection_id:
        dados["business_connection_id"] = business_connection_id

    try:
        resposta = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json=dados,
            timeout=20
        )
        if not resposta.ok:
            logging.error("Erro ao enviar mensagem: %s", resposta.text)

    except requests.RequestException:
        logging.exception("Falha na comunicação com o Telegram.")


def chave_atendimento(chat_id, business_connection_id):
    return f"{chat_id}:{business_connection_id or 'normal'}"


def cancelar_timer(timer):
    if timer:
        timer.cancel()


def encerrar_por_inatividade(chat_id, business_connection_id, chave):
    with lock:
        atendimento = atendimentos.get(chave)

        if not atendimento:
            return

        atendimento["estado"] = "encerrado"
        atendimento["aguardando_menu"] = True
        timers_inatividade.pop(chave, None)

    enviar_mensagem(
        chat_id,
        RESPOSTA_INATIVIDADE,
        business_connection_id
    )


def reiniciar_timer_inatividade(chat_id, business_connection_id, chave):
    with lock:
        timer_antigo = timers_inatividade.get(chave)
        cancelar_timer(timer_antigo)

        timer = threading.Timer(
            TEMPO_INATIVIDADE,
            encerrar_por_inatividade,
            args=(chat_id, business_connection_id, chave)
        )

        timer.daemon = True
        timers_inatividade[chave] = timer
        timer.start()


def enviar_resposta_saque(chat_id, business_connection_id, chave):
    with lock:
        atendimento = atendimentos.get(chave)

        if not atendimento:
            return

        if atendimento.get("estado") != "aguardando_confirmacao_saque":
            return

        atendimento["estado"] = "saque_processando"
        timers_saque.pop(chave, None)

    enviar_mensagem(
        chat_id,
        RESPOSTA_SAQUE_PROCESSANDO,
        business_connection_id
    )


def agendar_resposta_saque(chat_id, business_connection_id, chave):
    with lock:
        timer_antigo = timers_saque.get(chave)
        cancelar_timer(timer_antigo)

        timer = threading.Timer(
            TEMPO_SAQUE,
            enviar_resposta_saque,
            args=(chat_id, business_connection_id, chave)
        )

        timer.daemon = True
        timers_saque[chave] = timer
        timer.start()


def normalizar(texto):
    return texto.strip().lower()


def procurar_palavra_chave(texto):
    texto = normalizar(texto)

    for palavras, resposta in RESPOSTAS_PALAVRAS:
        for palavra in palavras:
            if palavra in texto:
                return resposta

    return None


def processar_mensagem(chat_id, texto, business_connection_id=None):
    chave = chave_atendimento(chat_id, business_connection_id)
    texto_original = texto.strip()
    texto = normalizar(texto_original)

    with lock:
        if chave not in atendimentos:
            atendimentos[chave] = {
                "estado": "menu",
                "aguardando_menu": True
            }

    reiniciar_timer_inatividade(
        chat_id,
        business_connection_id,
        chave
    )

    # COMANDO MENU
    if texto == "menu":
        with lock:
            atendimentos[chave]["estado"] = "menu"
            atendimentos[chave]["aguardando_menu"] = True

        enviar_mensagem(chat_id, MENU, business_connection_id)
        return

    with lock:
        atendimento = atendimentos[chave]
        estado = atendimento.get("estado", "menu")
        aguardando_menu = atendimento.get("aguardando_menu", True)

    # MENU PRINCIPAL: ESCOLHA NUMÉRICA
    if aguardando_menu and texto in RESPOSTAS:
        with lock:
            atendimentos[chave]["aguardando_menu"] = False

        if texto == "3":
            with lock:
                atendimentos[chave]["estado"] = "aguardando_codigo_w"

        elif texto == "4":
            with lock:
                atendimentos[chave]["estado"] = "aguardando_descricao"

        elif texto == "5":
            with lock:
                atendimentos[chave]["estado"] = "suporte_humano"

        else:
            with lock:
                atendimentos[chave]["estado"] = "atendido"

        enviar_mensagem(
            chat_id,
            RESPOSTAS[texto],
            business_connection_id
        )
        return

    # RECEBIMENTO DO CÓDIGO W
    if estado == "aguardando_codigo_w":
        codigo_w = re.search(r"\bW[A-Za-z0-9_-]*", texto_original, re.IGNORECASE)

        if codigo_w:
            with lock:
                atendimentos[chave]["estado"] = "aguardando_confirmacao_saque"

            agendar_resposta_saque(
                chat_id,
                business_connection_id,
                chave
            )
        else:
            enviar_mensagem(
                chat_id,
                RESPOSTAS["3"],
                business_connection_id
            )

        return

    # CONTA E ACESSO: RECEBE A DESCRIÇÃO DO PROBLEMA
    if estado == "aguardando_descricao":
        resposta = procurar_palavra_chave(texto)

        if resposta:
            enviar_mensagem(chat_id, resposta, business_connection_id)
        else:
            enviar_mensagem(
                chat_id,
                """Por favor, explique claramente o problema que está enfrentando para que possamos entender e ajudá-lo(a) melhor.""",
                business_connection_id
            )
        return

    # IDENTIFICAÇÃO DE PALAVRAS-CHAVE EM MENSAGENS LIVRES
    resposta = procurar_palavra_chave(texto)

    if resposta:
        enviar_mensagem(chat_id, resposta, business_connection_id)
        return

    # RESPOSTA PADRÃO
    enviar_mensagem(
        chat_id,
        """Por favor, explique claramente o problema que está enfrentando para que possamos entender e ajudá-lo(a) melhor.""",
        business_connection_id
    )


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "status": "online",
        "bot": "Lia - Jogo Manga"
    })


@app.route("/telegram/webhook", methods=["POST"])
def webhook():
    if WEBHOOK_SECRET:
        secret_recebido = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        )

        if secret_recebido != WEBHOOK_SECRET:
            return jsonify({"error": "Unauthorized"}), 403

    dados = request.get_json(silent=True) or {}

    mensagem = (
        dados.get("business_message")
        or dados.get("message")
    )

    if not mensagem:
        return jsonify({"ok": True})

    chat = mensagem.get("chat", {})
    chat_id = chat.get("id")
    texto = mensagem.get("text", "")
    business_connection_id = mensagem.get("business_connection_id")

    if not chat_id or not texto:
        return jsonify({"ok": True})

    # ATENDER SOMENTE CONVERSAS PRIVADAS
    if chat.get("type") != "private":
        return jsonify({"ok": True})

    # IGNORAR MENSAGENS DE OUTROS BOTS
    remetente = mensagem.get("from", {})

    if remetente.get("is_bot"):
        return jsonify({"ok": True})

    try:
        processar_mensagem(
            chat_id,
            texto,
            business_connection_id
        )
    except Exception:
        logging.exception("Erro ao processar mensagem.")

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

