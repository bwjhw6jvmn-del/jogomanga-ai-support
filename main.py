
import os
import logging
import threading
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN else None
)

TEMPO_INATIVIDADE = 300
TEMPO_SAQUE = 60

# =========================================================
# MENSAGENS
# =========================================================

MENU_PRINCIPAL = (
    "Olá, sou a Lia, assistente virtual do Grupo Manga! "
    "Estou aqui para ajudar. Selecione sobre qual plataforma deseja tirar dúvidas:\n\n"
    "1️⃣ Grupo Manga\n"
    "2️⃣ JogoManga\n"
    "3️⃣ Grupo T1\n"
    "4️⃣ Grupo FP"
)

MENU_MANGA = (
    "Selecione o assunto sobre o qual deseja atendimento:\n\n"
    "1️⃣ Recompensas e Promoções\n"
    "2️⃣ Questões relacionadas a parcerias\n"
    "3️⃣ Problemas com saques\n"
    "4️⃣ Conta e acesso\n"
    "5️⃣ Grupo VIP"
)

MENU_JOGOMANGA = (
    "Selecione o assunto sobre o qual deseja atendimento:\n\n"
    "1️⃣ Recompensas e Promoções\n"
    "2️⃣ Questões relacionadas a parcerias\n"
    "3️⃣ Problemas com saques\n"
    "4️⃣ Conta e acesso\n"
    "5️⃣ Grupo VIP"
)

MENSAGEM_FORA_AUTONOMIA = (
    "Lia Support (IA) Oficial:\n"
    "Sinto muito, não sei como resolver isso. "
    "Por favor, aguarde até que um de nossos representantes "
    "entre nesta conversa. Obrigado!"
)

MENSAGEM_ENCERRAMENTO = (
    "Lia Support (IA) Oficial:\n"
    "Olá, detectamos que você não respondeu. "
    "Devido à falta de comunicação, encerramos a conversa. Obrigado!\n"
    'Se desejar retornar ao menu, digite "menu".'
)

MENSAGEM_SAQUE = (
    "Lia Support (IA) Oficial:\n"
    "Por favor, aguarde; seu saque está sendo processado. "
    "O valor será creditado na sua conta em breve. "
    "Manteremos você informado em um prazo de até 10 minutos até 24 horas. "
    "Se não receber os fundos, consulte novamente para obter atualizações "
    "sobre a confirmação. Obrigado pela sua paciência."
)

# =========================================================
# RESPOSTAS DO GRUPO MANGA
# =========================================================

RESPOSTAS_MANGA = {
    "1": (
        "Lia Support (IA) Oficial:\n"
        "Para qualquer dúvida sobre recompensas, entre em contato "
        "com esta especialista em recompensas para obter ajuda. Obrigada!\n"
        "https://t.me/jogomanga_rowen"
    ),

    "2": (
        "Lia Support (IA) Oficial:\n"
        "Telegram: https://t.me/lancamentosmanga\n"
        "Entre no chat para colaborações com as plataformas MANGA e T1, obrigado!"
    ),

    "3": (
        "Lia Support (IA) Oficial:\n"
        "Por favor, informe o número do pedido, que começa com a letra W, "
        "em sua solicitação de retirada."
    ),

    "4": (
        "Lia Support (IA) Oficial:\n"
        "Para solicitar ou alterar sua senha de acesso, entre em contato "
        "com nossa equipe de suporte online ou aguarde até que um de nossos "
        "representantes entre nesta conversa:\n"
        "https://direct.lc.chat/14942394\n"
        "Lembre-se: não solicitamos senhas, códigos de acesso ou qualquer "
        "tipo de pagamento. Obrigado."
    ),

    "5": (
        "Lia Support (IA) Oficial:\n"
        "Por favor, aguarde até que um de nossos representantes "
        "entre nesta conversa. Obrigado."
    )
}

# =========================================================
# RESPOSTAS DO JOGOMANGA
# =========================================================

RESPOSTAS_JOGOMANGA = {
    "1": (
        "Lia Support (IA) Oficial:\n"
        "Para qualquer dúvida sobre recompensas, entre em contato "
        "com esta especialista em recompensas para obter ajuda. Obrigada!\n"
        "https://t.me/Simmyonly"
    ),

    "2": (
        "Lia Support (IA) Oficial:\n"
        "Telegram: https://t.me/lancamentosmanga\n"
        "Entre no chat para colaborações com as plataformas MANGA e T1, obrigado!"
    ),

    "3": (
        "Lia Support (IA) Oficial:\n"
        "Por favor, informe o número do pedido, que começa com a letra W, "
        "em sua solicitação de retirada."
    ),

    "4": (
        "Lia Support (IA) Oficial:\n"
        "Para solicitar ou alterar sua senha de acesso, entre em contato "
        "com este gerente:\n"
        "https://t.me/Simmyonly\n"
        "Lembre-se: não solicitamos senhas, códigos de acesso ou qualquer "
        "tipo de pagamento. Obrigado."
    ),

    "5": (
        "Lia Support (IA) Oficial:\n"
        "Para qualquer dúvida sobre seu Grupo VIP, entre em contato "
        "com este especialista em VIPs para obter ajuda. Obrigado!\n"
        "https://t.me/Simmyonly"
    )
}

# =========================================================
# RESPOSTAS GRUPO T1 E GRUPO FP
# =========================================================

RESPOSTAS_PLATAFORMAS = {
    "t1": (
        "Lia Support (IA) Oficial:\n"
        "Desculpe, não fui programado para resolver problemas do Grupo T1. "
        "Por favor, entre em contato com o suporte online. Obrigado!\n"
        "https://direct.lc.chat/14942394"
    ),

    "fp": (
        "Lia Support (IA) Oficial:\n"
        "Desculpe, não fui programado para resolver problemas do Grupo FP. "
        "Por favor, entre em contato com o suporte online. Obrigado!\n"
        "https://direct.lc.chat/14942394"
    )
}

# =========================================================
# ESTADOS E TEMPORIZADORES
# =========================================================

estados = {}
timers = {}
lock = threading.RLock()


def cancelar_timer(chave):
    timer = timers.pop(chave, None)

    if timer:
        timer.cancel()


def telegram_send(chat_id, texto, business_connection_id=None):
    if not BOT_TOKEN or not TELEGRAM_API:
        logging.error("TELEGRAM_BOT_TOKEN não configurado.")
        return False

    payload = {
        "chat_id": chat_id,
        "text": texto
    }

    if business_connection_id:
        payload["business_connection_id"] = business_connection_id

    try:
        logging.info(
            "Tentando enviar mensagem. Chat: %s | Business: %s",
            chat_id,
            bool(business_connection_id)
        )

        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json=payload,
            timeout=20
        )

        if not response.ok:
            logging.error(
                "Falha no envio. HTTP %s. Resposta: %s",
                response.status_code,
                response.text[:1000]
            )
            return False

        resultado = response.json()

        if not resultado.get("ok"):
            logging.error("Telegram retornou erro: %s", resultado)
            return False

        logging.info("Mensagem enviada com sucesso ao Telegram.")
        return True

    except requests.RequestException:
        logging.exception("Erro de conexão ao enviar mensagem.")
        return False


def encerrar_por_inatividade(chave, chat_id, business_id):
    with lock:
        timers.pop(chave, None)

        if chave not in estados:
            return

        if estados[chave] == "encerrado":
            return

        sucesso = telegram_send(
            chat_id,
            MENSAGEM_ENCERRAMENTO,
            business_id
        )

        if sucesso:
            estados[chave] = "encerrado"
            logging.info("Atendimento encerrado por inatividade: %s", chave)


def agendar_inatividade(chave, chat_id, business_id):
    cancelar_timer(chave)

    timer = threading.Timer(
        TEMPO_INATIVIDADE,
        encerrar_por_inatividade,
        args=(chave, chat_id, business_id)
    )

    timer.daemon = True
    timers[chave] = timer
    timer.start()

    logging.info("Temporizador de inatividade iniciado: %s", chave)


def enviar_resposta(chave, chat_id, texto, business_id):
    sucesso = telegram_send(
        chat_id,
        texto,
        business_id
    )

    if sucesso:
        agendar_inatividade(chave, chat_id, business_id)

    return sucesso


def mostrar_menu_principal(chave, chat_id, business_id):
    cancelar_timer(chave)

    estados[chave] = "menu_principal"

    enviar_resposta(
        chave,
        chat_id,
        MENU_PRINCIPAL,
        business_id
    )


def mostrar_menu_plataforma(chave, chat_id, business_id, plataforma):
    cancelar_timer(chave)

    estados[chave] = f"menu_{plataforma}"

    if plataforma == "manga":
        mensagem = MENU_MANGA

    else:
        mensagem = MENU_JOGOMANGA

    enviar_resposta(
        chave,
        chat_id,
        mensagem,
        business_id
    )


# =========================================================
# TEMPORIZADOR DE SAQUE
# =========================================================

def finalizar_espera_saque(chave, chat_id, business_id):
    with lock:
        timers.pop(f"{chave}:saque", None)

        if estados.get(chave) != "aguardando_saque":
            return

        estados[chave] = "atendimento_ativo"

        enviar_resposta(
            chave,
            chat_id,
            MENSAGEM_SAQUE,
            business_id
        )

        logging.info("Mensagem de processamento de saque enviada.")


def iniciar_temporizador_saque(chave, chat_id, business_id):
    cancelar_timer(chave)

    cancelar_timer(f"{chave}:saque")

    estados[chave] = "aguardando_saque"

    timer = threading.Timer(
        TEMPO_SAQUE,
        finalizar_espera_saque,
        args=(chave, chat_id, business_id)
    )

    timer.daemon = True
    timers[f"{chave}:saque"] = timer
    timer.start()

    logging.info("Temporizador de saque de 1 minuto iniciado: %s", chave)


# =========================================================
# PROCESSAMENTO DAS MENSAGENS
# =========================================================

def processar_mensagem(chat_id, business_id, texto):
    chave = f"{chat_id}:{business_id or 'normal'}"

    texto = texto.strip()
    texto_minusculo = texto.lower()

    with lock:

        # Toda mensagem recebida cancela o temporizador
        # de inatividade de 5 minutos.
        cancelar_timer(chave)

        # Menu solicitado pelo jogador.
        if texto_minusculo in ("menu", "/start"):
            cancelar_timer(f"{chave}:saque")

            mostrar_menu_principal(
                chave,
                chat_id,
                business_id
            )
            return

        # Primeira mensagem: qualquer conteúdo apresenta o menu.
        if chave not in estados:
            mostrar_menu_principal(
                chave,
                chat_id,
                business_id
            )
            return

        estado = estados.get(chave)

        # Após encerramento, somente menu ou /start reinicia.
        if estado == "encerrado":
            return

        # -------------------------------------------------
        # MENU PRINCIPAL
        # -------------------------------------------------

        if estado == "menu_principal":

            if texto == "1":
                mostrar_menu_plataforma(
                    chave, chat_id, business_id, "manga"
                )
                return

            if texto == "2":
                mostrar_menu_plataforma(
                    chave, chat_id, business_id, "jogomanga"
                )
                return

            if texto == "3":
                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    RESPOSTAS_PLATAFORMAS["t1"],
                    business_id
                )
                return

            if texto == "4":
                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    RESPOSTAS_PLATAFORMAS["fp"],
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                MENSAGEM_FORA_AUTONOMIA,
                business_id
            )
            return

        # -------------------------------------------------
        # MENU GRUPO MANGA
        # -------------------------------------------------

        if estado == "menu_manga":

            if texto in RESPOSTAS_MANGA:

                if texto == "3":
                    estados[chave] = "aguardando_codigo_manga"

                    enviar_resposta(
                        chave,
                        chat_id,
                        RESPOSTAS_MANGA["3"],
                        business_id
                    )
                    return

                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    RESPOSTAS_MANGA[texto],
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                MENSAGEM_FORA_AUTONOMIA,
                business_id
            )
            return

        # -------------------------------------------------
        # MENU JOGOMANGA
        # -------------------------------------------------

        if estado == "menu_jogomanga":

            if texto in RESPOSTAS_JOGOMANGA:

                if texto == "3":
                    estados[chave] = "aguardando_codigo_jogomanga"

                    enviar_resposta(
                        chave,
                        chat_id,
                        RESPOSTAS_JOGOMANGA["3"],
                        business_id
                    )
                    return

                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    RESPOSTAS_JOGOMANGA[texto],
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                MENSAGEM_FORA_AUTONOMIA,
                business_id
            )
            return

        # -------------------------------------------------
        # RECEBIMENTO DO CÓDIGO DE SAQUE
        # -------------------------------------------------

        if estado in (
            "aguardando_codigo_manga",
            "aguardando_codigo_jogomanga"
        ):

            if texto.upper().startswith("W") and len(texto) > 1:

                iniciar_temporizador_saque(
                    chave,
                    chat_id,
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                MENSAGEM_FORA_AUTONOMIA,
                business_id
            )
            return

        # -------------------------------------------------
        # OUTRAS MENSAGENS
        # -------------------------------------------------

        if estado == "aguardando_saque":
            # A contagem de 1 minuto continua.
            # O jogador pode digitar "menu" para cancelá-la.
            return

        # Qualquer mensagem fora dos fluxos previstos.
        enviar_resposta(
            chave,
            chat_id,
            MENSAGEM_FORA_AUTONOMIA,
            business_id
        )


# =========================================================
# ROTAS FLASK
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "Lia Support (IA) Oficial online", 200


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(silent=True) or {}

    logging.info(
        "Atualização recebida do Telegram. Tipos: %s",
        list(update.keys())
    )

    # Prioriza mensagens do Telegram Business.
    mensagem = update.get("business_message")

    if mensagem:
        logging.info("Mensagem recebida pelo Telegram Business.")

    else:
        mensagem = update.get("message")

        if mensagem:
            logging.info("Mensagem recebida pelo chat comum.")

    if not mensagem:
        return jsonify({"ok": True})

    chat = mensagem.get("chat", {})
    chat_id = chat.get("id")

    if not chat_id or chat.get("type") != "private":
        logging.info("Mensagem ignorada: chat não privado ou sem ID.")
        return jsonify({"ok": True})

    remetente = mensagem.get("from", {})

    if remetente.get("is_bot"):
        return jsonify({"ok": True})

    texto = mensagem.get("text", "")

    if not texto:
        logging.info("Mensagem ignorada: mensagem sem texto.")
        return jsonify({"ok": True})

    business_id = mensagem.get("business_connection_id")

    if business_id:
        logging.info("ID de conexão Business recebido.")

    try:
        processar_mensagem(
            chat_id,
            business_id,
            texto
        )

    except Exception:
        logging.exception("Erro ao processar mensagem do Telegram.")

    return jsonify({"ok": True})


# =========================================================
# INICIALIZAÇÃO
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
