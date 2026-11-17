
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
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None

TEMPO_INATIVIDADE = 300
TEMPO_SAQUE = 60

# Preferências e estados ficam em memória.
# Se o Render reiniciar, os usuários precisarão escolher o idioma novamente.
idiomas = {}
estados = {}
timers = {}
lock = threading.RLock()

# =========================================================
# TEXTOS NOS TRÊS IDIOMAS
# =========================================================

TEXTOS = {
    "pt": {
        "selecao_idioma": (
            "Olá! Sou a Lia, assistente virtual do Grupo Manga.\n"
            "Selecione seu idioma para continuar:\n\n"
            "1️⃣ Português\n2️⃣ English\n3️⃣ Español (México)"
        ),
        "idioma_invalido": "Opção inválida. Escolha 1 para Português, 2 para English ou 3 para Español (México).",
        "idioma_definido": "Idioma definido: Português.\n\n",
        "menu_principal": (
            "Olá, sou a Lia, assistente virtual do Grupo Manga! "
            "Estou aqui para ajudar. Selecione sobre qual plataforma deseja tirar dúvidas:\n\n"
            "1️⃣ Grupo Manga\n2️⃣ JogoManga\n3️⃣ Grupo T1\n4️⃣ Grupo FP"
        ),
        "menu_manga": (
            "Selecione o assunto sobre o qual deseja atendimento:\n\n"
            "1️⃣ Recompensas e Promoções\n2️⃣ Questões relacionadas a parcerias\n"
            "3️⃣ Problemas com saques\n4️⃣ Conta e acesso\n5️⃣ Grupo VIP"
        ),
        "menu_jogomanga": (
            "Selecione o assunto sobre o qual deseja atendimento:\n\n"
            "1️⃣ Recompensas e Promoções\n2️⃣ Questões relacionadas a parcerias\n"
            "3️⃣ Problemas com saques\n4️⃣ Conta e acesso\n5️⃣ Grupo VIP"
        ),
        "fora_autonomia": (
            "Lia Support (IA) Oficial:\nSinto muito, não sei como resolver isso. "
            "Por favor, aguarde até que um de nossos representantes entre nesta conversa. Obrigado!"
        ),
        "encerramento": (
            "Lia Support (IA) Oficial:\nOlá, detectamos que você não respondeu. "
            "Devido à falta de comunicação, encerramos a conversa. Obrigado!\n"
            'Se desejar retornar ao menu, digite "menu".'
        ),
        "saque": (
            "Lia Support (IA) Oficial:\nPor favor, aguarde; seu saque está sendo processado. "
            "O valor será creditado na sua conta em breve. Manteremos você informado em um prazo "
            "de até 10 minutos até 24 horas. Se não receber os fundos, consulte novamente para "
            "obter atualizações sobre a confirmação. Obrigado pela sua paciência."
        ),
        "manga": {
            "1": "Lia Support (IA) Oficial:\nPara qualquer dúvida sobre recompensas, entre em contato com esta especialista em recompensas para obter ajuda. Obrigada!\nhttps://t.me/jogomanga_Rowen",
            "2": "Lia Support (IA) Oficial:\nTelegram: https://t.me/lancamentosmanga\nEntre no chat para colaborações com as plataformas MANGA e T1, obrigado!",
            "3": "Lia Support (IA) Oficial:\nPor favor, informe o número do pedido, que começa com a letra W, em sua solicitação de retirada.",
            "4": "Lia Support (IA) Oficial:\nPara solicitar ou alterar sua senha de acesso, entre em contato com nossa equipe de suporte online ou aguarde até que um de nossos representantes entre nesta conversa:\nhttps://direct.lc.chat/14942394\nLembre-se: não solicitamos senhas, códigos de acesso ou qualquer tipo de pagamento. Obrigado.",
            "5": "Lia Support (IA) Oficial:\nPara solicitar acesso ao canal VIP do Grupo Manga, entre em contato com o especialista VIP, Rowen: https://t.me/jogomanga_Rowen"
        },
        "jogomanga": {
            "1": "Lia Support (IA) Oficial:\nPara qualquer dúvida sobre recompensas, entre em contato com esta especialista em recompensas para obter ajuda. Obrigada!\nhttps://t.me/Simmyonly",
            "2": "Lia Support (IA) Oficial:\nTelegram: https://t.me/lancamentosmanga\nEntre no chat para colaborações com as plataformas MANGA e T1, obrigado!",
            "3": "Lia Support (IA) Oficial:\nPor favor, informe o número do pedido, que começa com a letra W, em sua solicitação de retirada.",
            "4": "Lia Support (IA) Oficial:\nPara solicitar ou alterar sua senha de acesso, entre em contato com este gerente:\nhttps://t.me/Simmyonly\nLembre-se: não solicitamos senhas, códigos de acesso ou qualquer tipo de pagamento. Obrigado.",
            "5": "Lia Support (IA) Oficial:\nPara qualquer dúvida sobre seu Grupo VIP, entre em contato com este especialista em VIPs para obter ajuda. Obrigado!\nhttps://t.me/Simmyonly"
        },
        "t1": "Lia Support (IA) Oficial:\nDesculpe, não fui programado para resolver problemas do Grupo T1. Por favor, entre em contato com o suporte online. Obrigado!\nhttps://direct.lc.chat/14942394",
        "fp": "Lia Support (IA) Oficial:\nDesculpe, não fui programado para resolver problemas do Grupo FP. Por favor, entre em contato com o suporte online. Obrigado!\nhttps://direct.lc.chat/19730795"
    },

    "en": {
        "selecao_idioma": (
            "Hello! I'm Lia, the Grupo Manga virtual assistant.\n"
            "Please select your language to continue:\n\n"
            "1️⃣ Português\n2️⃣ English\n3️⃣ Español (México)"
        ),
        "idioma_invalido": "Invalid option. Choose 1 for Português, 2 for English, or 3 for Español (México).",
        "idioma_definido": "Language set to English.\n\n",
        "menu_principal": (
            "Hello! I'm Lia, the Grupo Manga virtual assistant. I'm here to help. "
            "Select the platform you need help with:\n\n"
            "1️⃣ Grupo Manga\n2️⃣ JogoManga\n3️⃣ Grupo T1\n4️⃣ Grupo FP"
        ),
        "menu_manga": (
            "Select the topic you need help with:\n\n"
            "1️⃣ Rewards and Promotions\n2️⃣ Partnership inquiries\n"
            "3️⃣ Withdrawal issues\n4️⃣ Account and access\n5️⃣ VIP Group"
        ),
        "menu_jogomanga": (
            "Select the topic you need help with:\n\n"
            "1️⃣ Rewards and Promotions\n2️⃣ Partnership inquiries\n"
            "3️⃣ Withdrawal issues\n4️⃣ Account and access\n5️⃣ VIP Group"
        ),
        "fora_autonomia": (
            "Lia Support (Official):\nI'm sorry, I don't know how to resolve this. "
            "Please wait for one of our representatives to join this conversation. Thank you!"
        ),
        "encerramento": (
            "Lia Support (Official):\nHello, we noticed that you haven't replied. "
            "Due to inactivity, this conversation has been closed. Thank you!\n"
            'To return to the menu, type "menu".'
        ),
        "saque": (
            "Lia Support (Official):\nPlease wait while your withdrawal is being processed. "
            "The funds will be credited to your account soon. We will keep you updated within "
            "10 minutes to 24 hours. If you do not receive the funds, contact us again for an "
            "update on the confirmation. Thank you for your patience."
        ),
        "manga": {
            "1": "Lia Support (Official):\nFor questions about rewards, please contact our rewards specialist for assistance. Thank you!\nhttps://t.me/jogomanga_Rowen",
            "2": "Lia Support (Official):\nTelegram: https://t.me/lancamentosmanga\nJoin the chat for partnership inquiries with the MANGA and T1 platforms. Thank you!",
            "3": "Lia Support (Official):\nPlease provide the withdrawal order number. It starts with the letter W.",
            "4": "Lia Support (Official):\nTo request or change your account password, contact our online support team or wait for one of our representatives to join this conversation:\nhttps://direct.lc.chat/14942394\nPlease remember: we never ask for passwords, access codes, or any kind of payment. Thank you.",
            "5": "Lia Support (Official):\nTo request access to the Grupo Manga VIP channel, contact the VIP specialist, Rowen: https://t.me/jogomanga_Rowen"
        },
        "jogomanga": {
            "1": "Lia Support (Official):\nFor questions about rewards, please contact our rewards specialist for assistance. Thank you!\nhttps://t.me/Simmyonly",
            "2": "Lia Support (Official):\nTelegram: https://t.me/lancamentosmanga\nJoin the chat for partnership inquiries with the MANGA and T1 platforms. Thank you!",
            "3": "Lia Support (Official):\nPlease provide the withdrawal order number. It starts with the letter W.",
            "4": "Lia Support (Official):\nTo request or change your account password, contact this manager:\nhttps://t.me/Simmyonly\nPlease remember: we never ask for passwords, access codes, or any kind of payment. Thank you.",
            "5": "Lia Support (Official):\nFor questions about your VIP Group, please contact our VIP specialist for assistance. Thank you!\nhttps://t.me/Simmyonly"
        },
        "t1": "Lia Support (Official):\nSorry, I am not programmed to resolve Grupo T1 issues. Please contact online support. Thank you!\nhttps://direct.lc.chat/14942394",
        "fp": "Lia Support (Official):\nSorry, I am not programmed to resolve Grupo FP issues. Please contact online support. Thank you!\nhttps://direct.lc.chat/19730795"
    },

    "es_mx": {
        "selecao_idioma": (
            "¡Hola! Soy Lia, la asistente virtual de Grupo Manga.\n"
            "Selecciona tu idioma para continuar:\n\n"
            "1️⃣ Português\n2️⃣ English\n3️⃣ Español (México)"
        ),
        "idioma_invalido": "Opción no válida. Elige 1 para Português, 2 para English o 3 para Español (México).",
        "idioma_definido": "Idioma configurado: Español (México).\n\n",
        "menu_principal": (
            "¡Hola! Soy Lia, la asistente virtual de Grupo Manga. Estoy aquí para ayudarte. "
            "Selecciona la plataforma sobre la que necesitas información:\n\n"
            "1️⃣ Grupo Manga\n2️⃣ JogoManga\n3️⃣ Grupo T1\n4️⃣ Grupo FP"
        ),
        "menu_manga": (
            "Selecciona el tema sobre el que necesitas atención:\n\n"
            "1️⃣ Recompensas y promociones\n2️⃣ Consultas sobre colaboraciones\n"
            "3️⃣ Problemas con retiros\n4️⃣ Cuenta y acceso\n5️⃣ Grupo VIP"
        ),
        "menu_jogomanga": (
            "Selecciona el tema sobre el que necesitas atención:\n\n"
            "1️⃣ Recompensas y promociones\n2️⃣ Consultas sobre colaboraciones\n"
            "3️⃣ Problemas con retiros\n4️⃣ Cuenta y acceso\n5️⃣ Grupo VIP"
        ),
        "fora_autonomia": (
            "Lia Support (Oficial):\nLo siento, no sé cómo resolver esta situación. "
            "Por favor, espera a que uno de nuestros representantes se una a esta conversación. ¡Gracias!"
        ),
        "encerramento": (
            "Lia Support (Oficial):\nHola, notamos que no respondiste. "
            "Debido a la falta de actividad, hemos cerrado esta conversación. ¡Gracias!\n"
            'Si deseas volver al menú, escribe "menu".'
        ),
        "saque": (
            "Lia Support (Oficial):\nPor favor, espera mientras se procesa tu retiro. "
            "El dinero se acreditará en tu cuenta próximamente. Te mantendremos informado "
            "en un plazo de entre 10 minutos y 24 horas. Si no recibes los fondos, vuelve a "
            "contactarnos para consultar el estado de la confirmación. Gracias por tu paciencia."
        ),
        "manga": {
            "1": "Lia Support (Oficial):\nSi tienes dudas sobre las recompensas, comunícate con nuestra especialista en recompensas para recibir ayuda. ¡Gracias!\nhttps://t.me/jogomanga_Rowen",
            "2": "Lia Support (Oficial):\nTelegram: https://t.me/lancamentosmanga\nÚnete al chat para consultas sobre colaboraciones con las plataformas MANGA y T1. ¡Gracias!",
            "3": "Lia Support (Oficial):\nPor favor, comparte el número de pedido de tu retiro. Comienza con la letra W.",
            "4": "Lia Support (Oficial):\nPara solicitar o cambiar tu contraseña, comunícate con nuestro equipo de soporte en línea o espera a que uno de nuestros representantes se una a esta conversación:\nhttps://direct.lc.chat/14942394\nRecuerda: nunca solicitamos contraseñas, códigos de acceso ni ningún tipo de pago. Gracias.",
            "5": "Lia Support (Oficial):\nPara solicitar acceso al canal VIP de Grupo Manga, comunícate con el especialista VIP, Rowen: https://t.me/jogomanga_Rowen"
        },
        "jogomanga": {
            "1": "Lia Support (Oficial):\nSi tienes dudas sobre las recompensas, comunícate con nuestra especialista en recompensas para recibir ayuda. ¡Gracias!\nhttps://t.me/Simmyonly",
            "2": "Lia Support (Oficial):\nTelegram: https://t.me/lancamentosmanga\nÚnete al chat para consultas sobre colaboraciones con las plataformas MANGA y T1. ¡Gracias!",
            "3": "Lia Support (Oficial):\nPor favor, comparte el número de pedido de tu retiro. Comienza con la letra W.",
            "4": "Lia Support (Oficial):\nPara solicitar o cambiar tu contraseña, comunícate con este gerente:\nhttps://t.me/Simmyonly\nRecuerda: nunca solicitamos contraseñas, códigos de acceso ni ningún tipo de pago. Gracias.",
            "5": "Lia Support (Oficial):\nSi tienes dudas sobre tu Grupo VIP, comunícate con nuestro especialista VIP para recibir ayuda. ¡Gracias!\nhttps://t.me/Simmyonly"
        },
        "t1": "Lia Support (Oficial):\nLo sentimos, no estoy programada para resolver problemas de Grupo T1. Por favor, comunícate con el soporte en línea. ¡Gracias!\nhttps://direct.lc.chat/14942394",
        "fp": "Lia Support (Oficial):\nLo sentimos, no estoy programada para resolver problemas de Grupo FP. Por favor, comunícate con el soporte en línea. ¡Gracias!\nhttps://direct.lc.chat/19730795"
    }
}

CODIGOS_IDIOMA = {"1": "pt", "2": "en", "3": "es_mx"}


def t(chat_id, chave_texto):
    idioma = idiomas.get(chat_id, "pt")
    return TEXTOS[idioma][chave_texto]


# =========================================================
# FUNÇÕES DE ENVIO E TEMPORIZADORES
# =========================================================

def cancelar_timer(chave):
    timer = timers.pop(chave, None)
    if timer:
        timer.cancel()


def telegram_send(chat_id, texto, business_connection_id=None):
    if not BOT_TOKEN or not TELEGRAM_API:
        logging.error("TELEGRAM_BOT_TOKEN não configurado.")
        return False

    payload = {"chat_id": chat_id, "text": texto}

    if business_connection_id:
        payload["business_connection_id"] = business_connection_id

    try:
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

        return True

    except requests.RequestException:
        logging.exception("Erro de conexão ao enviar mensagem.")
        return False


def encerrar_por_inatividade(chave, chat_id, business_id):
    with lock:
        timers.pop(chave, None)

        if chave not in estados or estados[chave] == "encerrado":
            return

        sucesso = telegram_send(
            chat_id,
            t(chat_id, "encerramento"),
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


def enviar_resposta(chave, chat_id, texto, business_id):
    sucesso = telegram_send(chat_id, texto, business_id)

    if sucesso:
        agendar_inatividade(chave, chat_id, business_id)

    return sucesso


# =========================================================
# MENUS
# =========================================================

def mostrar_selecao_idioma(chave, chat_id, business_id):
    cancelar_timer(chave)
    estados[chave] = "selecao_idioma"

    enviar_resposta(
        chave,
        chat_id,
        TEXTOS[idiomas.get(chat_id, "pt")]["selecao_idioma"],
        business_id
    )


def mostrar_menu_principal(chave, chat_id, business_id, prefixo=""):
    cancelar_timer(chave)
    estados[chave] = "menu_principal"

    enviar_resposta(
        chave,
        chat_id,
        prefixo + t(chat_id, "menu_principal"),
        business_id
    )


def mostrar_menu_plataforma(chave, chat_id, business_id, plataforma):
    cancelar_timer(chave)
    estados[chave] = f"menu_{plataforma}"

    enviar_resposta(
        chave,
        chat_id,
        t(chat_id, "menu_" + plataforma),
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
            t(chat_id, "saque"),
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

        # Comandos globais: menu e troca de idioma.
        if texto_minusculo in ("/start", "menu"):
            cancelar_timer(f"{chave}:saque")

            if chat_id not in idiomas:
                mostrar_selecao_idioma(chave, chat_id, business_id)
            else:
                mostrar_menu_principal(chave, chat_id, business_id)

            return

        if texto_minusculo in ("idioma", "/idioma", "language", "lenguaje"):
            cancelar_timer(f"{chave}:saque")
            mostrar_selecao_idioma(chave, chat_id, business_id)
            return

        # Primeira interação: solicitar idioma.
        if chat_id not in idiomas:
            mostrar_selecao_idioma(chave, chat_id, business_id)
            return

        estado = estados.get(chave)

        # Após encerramento, somente menu ou /start reinicia.
        if estado == "encerrado":
            return

        # Escolha de idioma.
        if estado == "selecao_idioma":
            novo_idioma = CODIGOS_IDIOMA.get(texto)

            if not novo_idioma:
                enviar_resposta(
                    chave,
                    chat_id,
                    t(chat_id, "idioma_invalido"),
                    business_id
                )
                return

            idiomas[chat_id] = novo_idioma

            mostrar_menu_principal(
                chave,
                chat_id,
                business_id,
                prefixo=TEXTOS[novo_idioma]["idioma_definido"]
            )
            return

        # Menu principal.
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
                    t(chat_id, "t1"),
                    business_id
                )
                return

            if texto == "4":
                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    t(chat_id, "fp"),
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                t(chat_id, "fora_autonomia"),
                business_id
            )
            return

        # Menus Grupo Manga e JogoManga.
        if estado in ("menu_manga", "menu_jogomanga"):

            plataforma = (
                "manga"
                if estado == "menu_manga"
                else "jogomanga"
            )

            respostas = TEXTOS[idiomas[chat_id]][plataforma]

            if texto in respostas:

                if texto == "3":
                    estados[chave] = f"aguardando_codigo_{plataforma}"

                    enviar_resposta(
                        chave,
                        chat_id,
                        respostas["3"],
                        business_id
                    )
                    return

                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    respostas[texto],
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                t(chat_id, "fora_autonomia"),
                business_id
            )
            return

        # Recebimento do código de saque.
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
                t(chat_id, "fora_autonomia"),
                business_id
            )
            return

        # Durante a espera de 1 minuto, o temporizador continua ativo.
        if estado == "aguardando_saque":
            return

        # Qualquer mensagem fora dos fluxos previstos.
        enviar_resposta(
            chave,
            chat_id,
            t(chat_id, "fora_autonomia"),
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
    mensagem = update.get("business_message") or update.get("message")

    if not mensagem:
        return jsonify({"ok": True})

    chat = mensagem.get("chat", {})
    chat_id = chat.get("id")

    if not chat_id or chat.get("type") != "private":
        return jsonify({"ok": True})

    remetente = mensagem.get("from", {})

    if remetente.get("is_bot"):
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
