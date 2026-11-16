
import os
import logging
import threading
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

MENU = (
    "Olá, sou a Lia, assistente virtual da Jogomanga! "
    "Estou aqui para ajudar. Selecione o tópico sobre o qual deseja tirar dúvidas:\n\n"
    "1️⃣ Recompensas e Promoções\n"
    "2️⃣ Questões relacionadas a parcerias\n"
    "3️⃣ Problemas com saques\n"
    "4️⃣ Conta e acesso\n"
    "5️⃣ Suporte humano\n"
    "6️⃣ Meu grupo VIP"
)

RESPOSTAS = {
    "1": (
        "Lia Support (IA) Oficial: Para qualquer dúvida sobre recompensas, "
        "entre em contato com esta especialista em recompensas para obter ajuda. "
        "Obrigada! https://t.me/Simmyonly"
    ),
    "2": (
        "Lia Support (IA) Oficial: Telegram: https://t.me/lancamentosmanga "
        "Participe deste grupo para saber mais sobre parcerias com as plataformas "
        "MANGA e T1. Obrigada!"
    ),
    "3": (
        "Lia Support (IA) Oficial: Inclua um código de comando começando "
        "com a letra W em sua solicitação de saque."
    ),
    "4": (
        "Lia Support (IA) Oficial: Descreva seu problema detalhadamente "
        "para que possamos entender melhor e ajudá-lo(a)."
    ),
    "5": (
        "Lia Support (IA) Oficial: Aguarde um momento enquanto encaminhamos "
        "sua solicitação para nossa equipe de atendimento ao cliente."
    ),
    "6": (
        "Lia Support (IA) Oficial: Para qualquer dúvida sobre seu Grupo VIP, "
        "entre em contato com este especialista em VIPs para obter ajuda. "
        "Obrigado! https://t.me/Simmyonly"
    )
}

MENSAGEM_SAQUE = (
    "Lia Support (IA) Oficial: Aguarde, seu saque está sendo processado. "
    "Os fundos chegarão em breve. Notificaremos você dentro de 10 minutos "
    "a 24 horas. Caso não tenha recebido seu pagamento, verifique novamente "
    "para obter uma atualização de confirmação. Agradecemos sua paciência."
)

MENSAGEM_ENCERRAMENTO = (
    'Lia Support (IA) Oficial: Olá, detectamos que você não respondeu. '
    'Devido à falta de comunicação, encerramos a conversa. Obrigado! '
    'Se desejar retornar ao menu, digite "menu".'
)

# Estados e temporizadores em memória
estados = {}
timers = {}
lock = threading.RLock()


def telegram_send(chat_id, text, business_connection_id=None):
    if not BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN não configurado.")
        return False

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if business_connection_id:
        payload["business_connection_id"] = business_connection_id

    try:
        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json=payload,
            timeout=20
        )

        if not response.ok:
            # Não registrar a URL, pois ela contém o token do bot.
            logging.error(
                "Telegram recusou o envio. HTTP %s. Resposta: %s",
                response.status_code,
                response.text[:1000]
            )
            return False

        return True

    except requests.RequestException as error:
        logging.error("Erro de conexão ao enviar mensagem: %s", str(error))
        return False


def cancelar_timer(chave):
    timer = timers.pop(chave, None)
    if timer:
        timer.cancel()


def agendar_timer(chave, segundos, funcao):
    cancelar_timer(chave)

    timer = threading.Timer(segundos, funcao)
    timer.daemon = True
    timers[chave] = timer
    timer.start()


def encerrar_por_inatividade(chave, chat_id, business_id):
    with lock:
        timers.pop(chave, None)

        if chave not in estados:
            return

        telegram_send(
            chat_id,
            MENSAGEM_ENCERRAMENTO,
            business_id
        )

        estados[chave] = "menu"


def mostrar_menu(chave, chat_id, business_id):
    cancelar_timer(chave)
    estados[chave] = "menu"

    telegram_send(chat_id, MENU, business_id)

    agendar_timer(
        chave,
        300,
        lambda: encerrar_por_inatividade(
            chave, chat_id, business_id
        )
    )


def finalizar_espera_saque(chave, chat_id, business_id):
    with lock:
        timers.pop(chave, None)

        if estados.get(chave) != "aguardando_saque":
            return

        telegram_send(
            chat_id,
            MENSAGEM_SAQUE,
            business_id
        )

        # Os 5 minutos começam somente após a mensagem de processamento.
        agendar_timer(
            chave,
            300,
            lambda: encerrar_por_inatividade(
                chave, chat_id, business_id
            )
        )


def processar_mensagem(chat_id, business_id, texto):
    chave = f"{chat_id}:{business_id or 'normal'}"
    texto = texto.strip()
    texto_minusculo = texto.lower()

    with lock:

        # MENU pode ser solicitado em qualquer etapa.
        if texto_minusculo in ("/start", "menu"):
            mostrar_menu(chave, chat_id, business_id)
            return

        # CORREÇÃO: qualquer opção de 1 a 6 funciona em qualquer etapa.
        # Isso também cancela os temporizadores anteriores.
        if texto in ("1", "2", "3", "4", "5", "6"):
            cancelar_timer(chave)

            if texto == "3":
                estados[chave] = "aguardando_codigo_w"
                telegram_send(
                    chat_id,
                    RESPOSTAS["3"],
                    business_id
                )
                return

            if texto == "4":
                estados[chave] = "aguardando_descricao"
                telegram_send(
                    chat_id,
                    RESPOSTAS["4"],
                    business_id
                )
                agendar_timer(
                    chave,
                    300,
                    lambda: encerrar_por_inatividade(
                        chave, chat_id, business_id
                    )
                )
                return

            estados[chave] = "menu"
            telegram_send(
                chat_id,
                RESPOSTAS[texto],
                business_id
            )

            agendar_timer(
                chave,
                300,
                lambda: encerrar_por_inatividade(
                    chave, chat_id, business_id
                )
            )
            return

        estado = estados.get(chave, "menu")

        # Recebimento da descrição do problema.
        if estado == "aguardando_descricao":
            cancelar_timer(chave)
            estados[chave] = "menu"

            # A descrição não é encaminhada automaticamente a um atendente.
            mostrar_menu(chave, chat_id, business_id)
            return

        # Recebimento do código W.
        if estado == "aguardando_codigo_w":
            if texto.upper().startswith("W"):
                cancelar_timer(chave)
                estados[chave] = "aguardando_saque"

                agendar_timer(
                    chave,
                    120,
                    lambda: finalizar_espera_saque(
                        chave, chat_id, business_id
                    )
                )
            else:
                telegram_send(
                    chat_id,
                    "Por favor, envie o código de comando começando com a letra W.",
                    business_id
                )
            return

        # Mensagem fora das opções: apresenta novamente o menu.
        mostrar_menu(chave, chat_id, business_id)


@app.route("/", methods=["GET"])
def home():
    return "Jogo Manga Support Bot online", 200


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(silent=True) or {}

    # Aceita mensagens comuns e mensagens do Telegram Business.
    mensagem = update.get("business_message") or update.get("message")

    if not mensagem:
        return jsonify({"ok": True})

    chat = mensagem.get("chat", {})
    chat_id = chat.get("id")

    if not chat_id or chat.get("type") != "private":
        return jsonify({"ok": True})

    if mensagem.get("from", {}).get("is_bot"):
        return jsonify({"ok": True})

    texto = mensagem.get("text", "")
    if not texto:
        return jsonify({"ok": True})

    business_id = mensagem.get("business_connection_id")

    try:
        processar_mensagem(
            chat_id,
            business_id,
            texto
        )
    except Exception:
        logging.exception("Erro ao processar mensagem do Telegram")

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )


