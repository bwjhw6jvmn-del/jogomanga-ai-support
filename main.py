
import os
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

MENU = """Olá, sou a Lia, assistente virtual da Jogomanga! Estou aqui para ajudar. Selecione o tópico sobre o qual deseja tirar dúvidas:

1️⃣ Recompensas e Promoções
2️⃣ Questões relacionadas a parcerias
3️⃣ Problemas com saques
4️⃣ Conta e acesso
5️⃣ Suporte humano
6️⃣ Meu grupo VIP"""

RESPOSTAS = {
    "1": """Lia Support (IA) Oficial: Para qualquer dúvida sobre recompensas, entre em contato com esta especialista em recompensas para obter ajuda. Obrigada! https://t.me/Simmyonly""",

    "2": """Lia Support (IA) Oficial: Telegram: https://t.me/lancamentosmanga Participe deste grupo para saber mais sobre parcerias com as plataformas MANGA e T1. Obrigada!""",

    "3": """Lia Support (IA) Oficial: Inclua um código de comando começando com a letra W em sua solicitação de saque.""",

    "4": """Lia Support (IA) Oficial: Descreva seu problema detalhadamente para que possamos entender melhor e ajudá-lo(a).""",

    "5": """Lia Support (IA) Oficial: Aguarde um momento enquanto encaminhamos sua solicitação para nossa equipe de atendimento ao cliente.""",

    "6": """Lia Support (IA) Oficial: Para qualquer dúvida sobre seu Grupo VIP, entre em contato com este especialista em VIPs para obter ajuda. Obrigado! https://t.me/Simmyonly"""
}

MENSAGEM_SAQUE = """Lia Support (IA) Oficial: Aguarde, seu saque está sendo processado. Os fundos chegarão em breve. Notificaremos você dentro de 10 minutos a 24 horas. Caso não tenha recebido seu pagamento, verifique novamente para obter uma atualização de confirmação. Agradecemos sua paciência."""

ENCERRAMENTO = """Lia Support (IA) Oficial: Olá, detectamos que você não respondeu. Devido à falta de comunicação, encerramos a conversa. Obrigado! Se desejar retornar ao menu, digite "menu"."""


conversas = {}
timers_inatividade = {}
timers_saque = {}
lock = threading.RLock()


def enviar_mensagem(chat_id, texto, business_connection_id=None):
    dados = {
        "chat_id": chat_id,
        "text": texto
    }

    if business_connection_id:
        dados["business_connection_id"] = business_connection_id

    try:
        resposta = requests.post(
            API_URL + "sendMessage",
            json=dados,
            timeout=20
        )
        resposta.raise_for_status()
        resultado = resposta.json()

        if not resultado.get("ok"):
            print("Erro do Telegram:", resultado)

        return resultado

    except Exception as erro:
        print("Erro ao enviar mensagem:", erro)
        return None


def cancelar_timer(timer_dict, chat_id):
    timer = timer_dict.pop(chat_id, None)

    if timer:
        timer.cancel()


def iniciar_timer_inatividade(chat_id, business_connection_id):
    with lock:
        cancelar_timer(timers_inatividade, chat_id)

        timer = threading.Timer(
            300,
            encerrar_por_inatividade,
            args=(chat_id, business_connection_id)
        )

        timer.daemon = True
        timers_inatividade[chat_id] = timer
        timer.start()


def encerrar_por_inatividade(chat_id, business_connection_id):
    with lock:
        conversas.pop(chat_id, None)
        timers_inatividade.pop(chat_id, None)
        cancelar_timer(timers_saque, chat_id)

    enviar_mensagem(
        chat_id,
        ENCERRAMENTO,
        business_connection_id
    )


def mostrar_menu(chat_id, business_connection_id=None):
    with lock:
        cancelar_timer(timers_inatividade, chat_id)
        cancelar_timer(timers_saque, chat_id)

        conversas[chat_id] = {"etapa": "menu"}

    enviar_mensagem(chat_id, MENU, business_connection_id)
    iniciar_timer_inatividade(chat_id, business_connection_id)


def enviar_resposta_saque(chat_id, business_connection_id):
    with lock:
        timers_saque.pop(chat_id, None)

        estado = conversas.get(chat_id)

        if not estado or estado.get("etapa") != "aguardando_saque":
            return

        conversas[chat_id] = {"etapa": "menu"}

    # Segunda mensagem: enviada 2 minutos após o código W.
    enviar_mensagem(
        chat_id,
        MENSAGEM_SAQUE,
        business_connection_id
    )

    # Os 5 minutos de inatividade começam somente agora.
    iniciar_timer_inatividade(chat_id, business_connection_id)


def processar_mensagem(chat_id, texto, business_connection_id=None):
    texto = texto.strip()

    # Comando para abrir ou retornar ao menu.
    if texto.lower() in ["/start", "start", "menu"]:
        mostrar_menu(chat_id, business_connection_id)
        return

    with lock:
        estado = conversas.get(chat_id)

    # Primeiro contato: apresenta o menu.
    if estado is None:
        mostrar_menu(chat_id, business_connection_id)
        return

    etapa = estado.get("etapa")

    # Opção 3: aguarda o código W.
    if etapa == "aguardando_codigo_w":

        if texto.upper().startswith("W"):
            with lock:
                conversas[chat_id] = {"etapa": "aguardando_saque"}

                # Cancela qualquer contagem de inatividade anterior.
                cancelar_timer(timers_inatividade, chat_id)
                cancelar_timer(timers_saque, chat_id)

                # Agenda a segunda mensagem para 2 minutos depois.
                timer = threading.Timer(
                    120,
                    enviar_resposta_saque,
                    args=(chat_id, business_connection_id)
                )

                timer.daemon = True
                timers_saque[chat_id] = timer
                timer.start()

        else:
            enviar_mensagem(
                chat_id,
                "Por favor, envie o código de comando começando com a letra W.",
                business_connection_id
            )

        return

    # Opção 3: aguarda os 2 minutos para enviar a segunda mensagem.
    if etapa == "aguardando_saque":
        # Não altera o temporizador. O comando "menu" acima
        # continua disponível para cancelar esse fluxo.
        return

    # Opção 4: recebe a descrição do problema.
    if etapa == "aguardando_descricao":
        with lock:
            conversas[chat_id] = {"etapa": "descricao_recebida"}

        iniciar_timer_inatividade(chat_id, business_connection_id)
        return

    # Após receber a descrição, uma nova mensagem retorna ao menu.
    if etapa == "descricao_recebida":
        mostrar_menu(chat_id, business_connection_id)
        return

    # Somente números de 1 a 6 selecionam opções do menu.
    if etapa == "menu" and texto in RESPOSTAS:
        cancelar_timer(timers_inatividade, chat_id)

        if texto == "3":
            with lock:
                conversas[chat_id] = {"etapa": "aguardando_codigo_w"}

            enviar_mensagem(
                chat_id,
                RESPOSTAS["3"],
                business_connection_id
            )

            # Não inicia os 5 minutos aqui.
            # A contagem começará após a segunda mensagem.

        elif texto == "4":
            with lock:
                conversas[chat_id] = {"etapa": "aguardando_descricao"}

            enviar_mensagem(
                chat_id,
                RESPOSTAS["4"],
                business_connection_id
            )

            iniciar_timer_inatividade(chat_id, business_connection_id)

        else:
            with lock:
                conversas[chat_id] = {"etapa": "menu"}

            enviar_mensagem(
                chat_id,
                RESPOSTAS[texto],
                business_connection_id
            )

            iniciar_timer_inatividade(chat_id, business_connection_id)

        return

    # Não existem palavras-chave nem respostas genéricas.
    # Uma entrada inválida no menu apresenta o menu novamente.
    mostrar_menu(chat_id, business_connection_id)


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "status": "online",
        "bot": "Lia - Suporte Jogo Manga"
    })


@app.route("/telegram/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    mensagem = (
        update.get("business_message")
        or update.get("message")
    )

    if not mensagem:
        return jsonify({"ok": True})

    chat = mensagem.get("chat", {})

    if chat.get("type") != "private":
        return jsonify({"ok": True})

    remetente = mensagem.get("from", {})

    if remetente.get("is_bot"):
        return jsonify({"ok": True})

    texto = mensagem.get("text", "")

    if not texto:
        return jsonify({"ok": True})

    chat_id = chat.get("id")
    business_connection_id = mensagem.get("business_connection_id")

    processar_mensagem(
        chat_id,
        texto,
        business_connection_id
    )

    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


