
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
# IDIOMAS
# =========================================================

IDIOMAS = {
    "1": "pt",
    "2": "en",
    "3": "es"
}

idiomas = {}

TEXTOS = {
    "pt": {
        "selecao": (
            "Olá! Sou a Lia, assistente virtual do Grupo Manga.\n"
            "Selecione seu idioma para continuar:\n\n"
            "1️⃣ Português\n"
            "2️⃣ English\n"
            "3️⃣ Español (México)"
        ),
        "idioma_invalido": (
            "Opção inválida. Por favor, escolha:\n\n"
            "1️⃣ Português\n"
            "2️⃣ English\n"
            "3️⃣ Español (México)"
        ),
        "idioma_definido": "Idioma definido para Português.",
        "menu_principal": (
            "Olá, sou a Lia, assistente virtual do Grupo Manga! "
            "Estou aqui para ajudar. Selecione sobre qual plataforma deseja tirar dúvidas:\n\n"
            "1️⃣ Grupo Manga\n"
            "2️⃣ JogoManga\n"
            "3️⃣ Grupo T1\n"
            "4️⃣ Grupo FP"
        ),
        "menu_plataforma": (
            "Selecione o assunto sobre o qual deseja atendimento:\n\n"
            "1️⃣ Recompensas e Promoções\n"
            "2️⃣ Questões relacionadas a parcerias\n"
            "3️⃣ Problemas com saques\n"
            "4️⃣ Conta e acesso\n"
            "5️⃣ Grupo VIP"
        ),
        "fora_autonomia": (
            "Lia Support (IA) Oficial:\n"
            "Sinto muito, não sei como resolver isso. "
            "Por favor, aguarde até que um de nossos representantes "
            "entre nesta conversa. Obrigado!"
        ),
        "encerramento": (
            "Lia Support (IA) Oficial:\n"
            "Olá, detectamos que você não respondeu. "
            "Devido à falta de comunicação, encerramos a conversa. Obrigado!\n"
            'Se desejar retornar ao menu, digite "menu".'
        ),
        "saque": (
            "Lia Support (IA) Oficial:\n"
            "Por favor, aguarde; seu saque está sendo processado. "
            "O valor será creditado na sua conta em breve. "
            "Manteremos você informado em um prazo de até 10 minutos até 24 horas. "
            "Se não receber os fundos, consulte novamente para obter atualizações "
            "sobre a confirmação. Obrigado pela sua paciência."
        ),
        "manga": {
            "1": (
                "Lia Support (IA) Oficial:\n"
                "Para qualquer dúvida sobre recompensas, entre em contato "
                "com esta especialista em recompensas para obter ajuda. Obrigada!\n"
                "https://t.me/jogomanga_Rowen"
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
                "Para solicitar acesso ao canal VIP do Grupo Manga, entre em contato com o specialist VIP, Rowen: https://t.me/jogomanga_Rowen"
            )
        },
        "jogomanga": {
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
        },
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
            "https://direct.lc.chat/19730795"
        )
    },

    "en": {
        "selecao": (
            "Hello! I'm Lia, Grupo Manga's virtual assistant.\n"
            "Please select your language to continue:\n\n"
            "1️⃣ Português\n"
            "2️⃣ English\n"
            "3️⃣ Español (México)"
        ),
        "idioma_invalido": (
            "Invalid option. Please choose:\n\n"
            "1️⃣ Português\n"
            "2️⃣ English\n"
            "3️⃣ Español (México)"
        ),
        "idioma_definido": "Language set to English.",
        "menu_principal": (
            "Hello! I'm Lia, Grupo Manga's virtual assistant. "
            "I'm here to help. Select the platform you need assistance with:\n\n"
            "1️⃣ Grupo Manga\n"
            "2️⃣ JogoManga\n"
            "3️⃣ Grupo T1\n"
            "4️⃣ Grupo FP"
        ),
        "menu_plataforma": (
            "Please select the topic you need assistance with:\n\n"
            "1️⃣ Rewards and Promotions\n"
            "2️⃣ Partnership inquiries\n"
            "3️⃣ Withdrawal issues\n"
            "4️⃣ Account and access\n"
            "5️⃣ VIP Group"
        ),
        "fora_autonomia": (
            "Lia Support (Official AI):\n"
            "I'm sorry, I don't know how to resolve this issue. "
            "Please wait until one of our representatives joins this conversation. Thank you!"
        ),
        "encerramento": (
            "Lia Support (Official AI):\n"
            "Hello, we noticed that you haven't responded. "
            "Due to inactivity, we have closed this conversation. Thank you!\n"
            'If you wish to return to the menu, type "menu".'
        ),
        "saque": (
            "Lia Support (Official AI):\n"
            "Please wait while your withdrawal is being processed. "
            "The amount will be credited to your account shortly. "
            "We will keep you informed within 10 minutes to 24 hours. "
            "If you do not receive the funds, please contact us again for an update "
            "on the confirmation. Thank you for your patience."
        ),
        "manga": {
            "1": (
                "Lia Support (Official AI):\n"
                "For any questions about rewards, please contact our rewards specialist for assistance. Thank you!\n"
                "https://t.me/jogomanga_Rowen"
            ),
            "2": (
                "Lia Support (Official AI):\n"
                "Telegram: https://t.me/lancamentosmanga\n"
                "Join the chat for partnership opportunities with the MANGA and T1 platforms. Thank you!"
            ),
            "3": (
                "Lia Support (Official AI):\n"
                "Please provide the order number for your withdrawal request. It starts with the letter W."
            ),
            "4": (
                "Lia Support (Official AI):\n"
                "To request or change your login password, contact our online support team or wait for one of our representatives to join this conversation:\n"
                "https://direct.lc.chat/14942394\n"
                "Remember: we never ask for passwords, access codes, or any kind of payment. Thank you."
            ),
            "5": (
                "Lia Support (Official AI):\n"
                "To request access to the Grupo Manga VIP channel, contact the VIP specialist, Rowen: https://t.me/jogomanga_Rowen"
            )
        },
        "jogomanga": {
            "1": (
                "Lia Support (Official AI):\n"
                "For any questions about rewards, please contact our rewards specialist for assistance. Thank you!\n"
                "https://t.me/Simmyonly"
            ),
            "2": (
                "Lia Support (Official AI):\n"
                "Telegram: https://t.me/lancamentosmanga\n"
                "Join the chat for partnership opportunities with the MANGA and T1 platforms. Thank you!"
            ),
            "3": (
                "Lia Support (Official AI):\n"
                "Please provide the order number for your withdrawal request. It starts with the letter W."
            ),
            "4": (
                "Lia Support (Official AI):\n"
                "To request or change your login password, contact this manager:\n"
                "https://t.me/Simmyonly\n"
                "Remember: we never ask for passwords, access codes, or any kind of payment. Thank you."
            ),
            "5": (
                "Lia Support (Official AI):\n"
                "For any questions about your VIP Group, please contact our VIP specialist for assistance. Thank you!\n"
                "https://t.me/Simmyonly"
            )
        },
        "t1": (
            "Lia Support (Official AI):\n"
            "Sorry, I am not programmed to resolve Grupo T1 issues. "
            "Please contact online support. Thank you!\n"
            "https://direct.lc.chat/14942394"
        ),
        "fp": (
            "Lia Support (Official AI):\n"
            "Sorry, I am not programmed to resolve Grupo FP issues. "
            "Please contact online support. Thank you!\n"
            "https://direct.lc.chat/19730795"
        )
    },

    "es": {
        "selecao": (
            "¡Hola! Soy Lia, la asistente virtual de Grupo Manga.\n"
            "Selecciona tu idioma para continuar:\n\n"
            "1️⃣ Português\n"
            "2️⃣ English\n"
            "3️⃣ Español (México)"
        ),
        "idioma_invalido": (
            "Opción no válida. Por favor, selecciona:\n\n"
            "1️⃣ Português\n"
            "2️⃣ English\n"
            "3️⃣ Español (México)"
        ),
        "idioma_definido": "Idioma configurado en Español.",
        "menu_principal": (
            "¡Hola! Soy Lia, la asistente virtual de Grupo Manga. "
            "Estoy aquí para ayudarte. Selecciona la plataforma sobre la que necesitas información:\n\n"
            "1️⃣ Grupo Manga\n"
            "2️⃣ JogoManga\n"
            "3️⃣ Grupo T1\n"
            "4️⃣ Grupo FP"
        ),
        "menu_plataforma": (
            "Selecciona el tema sobre el que necesitas atención:\n\n"
            "1️⃣ Recompensas y promociones\n"
            "2️⃣ Consultas sobre colaboraciones\n"
            "3️⃣ Problemas con retiros\n"
            "4️⃣ Cuenta y acceso\n"
            "5️⃣ Grupo VIP"
        ),
        "fora_autonomia": (
            "Lia Support (IA) Oficial:\n"
            "Lo siento, no sé cómo resolver este problema. "
            "Por favor, espera hasta que uno de nuestros representantes se una a esta conversación. ¡Gracias!"
        ),
        "encerramento": (
            "Lia Support (IA) Oficial:\n"
            "Hola, detectamos que no has respondido. "
            "Debido a la falta de comunicación, hemos cerrado esta conversación. ¡Gracias!\n"
            'Si deseas volver al menú, escribe "menu".'
        ),
        "saque": (
            "Lia Support (IA) Oficial:\n"
            "Por favor, espera mientras se procesa tu retiro. "
            "El importe se acreditará en tu cuenta próximamente. "
            "Te mantendremos informado en un plazo de entre 10 minutos y 24 horas. "
            "Si no recibes los fondos, vuelve a consultarnos para obtener información "
            "sobre la confirmación. Gracias por tu paciencia."
        ),
        "manga": {
            "1": (
                "Lia Support (IA) Oficial:\n"
                "Si tienes alguna duda sobre las recompensas, comunícate con nuestra especialista en recompensas para recibir ayuda. ¡Gracias!\n"
                "https://t.me/jogomanga_Rowen"
            ),
            "2": (
                "Lia Support (IA) Oficial:\n"
                "Telegram: https://t.me/lancamentosmanga\n"
                "Únete al chat para colaboraciones con las plataformas MANGA y T1. ¡Gracias!"
            ),
            "3": (
                "Lia Support (IA) Oficial:\n"
                "Por favor, proporciona el número de pedido de tu solicitud de retiro. Comienza con la letra W."
            ),
            "4": (
                "Lia Support (IA) Oficial:\n"
                "Para solicitar o cambiar tu contraseña de acceso, comunícate con nuestro equipo de soporte en línea o espera a que uno de nuestros representantes se una a esta conversación:\n"
                "https://direct.lc.chat/14942394\n"
                "Recuerda: nunca solicitamos contraseñas, códigos de acceso ni ningún tipo de pago. Gracias."
            ),
            "5": (
                "Lia Support (IA) Oficial:\n"
                "Para solicitar acceso al canal VIP de Grupo Manga, comunícate con la especialista VIP, Rowen: https://t.me/jogomanga_Rowen"
            )
        },
        "jogomanga": {
            "1": (
                "Lia Support (IA) Oficial:\n"
                "Si tienes alguna duda sobre las recompensas, comunícate con nuestra especialista en recompensas para recibir ayuda. ¡Gracias!\n"
                "https://t.me/Simmyonly"
            ),
            "2": (
                "Lia Support (IA) Oficial:\n"
                "Telegram: https://t.me/lancamentosmanga\n"
                "Únete al chat para colaboraciones con las plataformas MANGA y T1. ¡Gracias!"
            ),
            "3": (
                "Lia Support (IA) Oficial:\n"
                "Por favor, proporciona el número de pedido de tu solicitud de retiro. Comienza con la letra W."
            ),
            "4": (
                "Lia Support (IA) Oficial:\n"
                "Para solicitar o cambiar tu contraseña de acceso, comunícate con este gerente:\n"
                "https://t.me/Simmyonly\n"
                "Recuerda: nunca solicitamos contraseñas, códigos de acceso ni ningún tipo de pago. Gracias."
            ),
            "5": (
                "Lia Support (IA) Oficial:\n"
                "Si tienes alguna duda sobre tu Grupo VIP, comunícate con nuestro especialista VIP para recibir ayuda. ¡Gracias!\n"
                "https://t.me/Simmyonly"
            )
        },
        "t1": (
            "Lia Support (IA) Oficial:\n"
            "Lo sentimos, no estamos programados para resolver problemas de Grupo T1. "
            "Por favor, comunícate con el soporte en línea. ¡Gracias!\n"
            "https://direct.lc.chat/14942394"
        ),
        "fp": (
            "Lia Support (IA) Oficial:\n"
            "Lo sentimos, no estamos programados para resolver problemas de Grupo FP. "
            "Por favor, comunícate con el soporte en línea. ¡Gracias!\n"
            "https://direct.lc.chat/19730795"
        )
    }
}


# =========================================================
# ESTADOS E TEMPORIZADORES
# =========================================================

estados = {}
timers = {}
lock = threading.RLock()


def obter_idioma(user_id):
    return idiomas.get(user_id, "pt")


def obter_texto(user_id, chave):
    idioma = obter_idioma(user_id)
    return TEXTOS[idioma][chave]


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


def enviar_resposta(chave, chat_id, user_id, texto, business_id):
    sucesso = telegram_send(chat_id, texto, business_id)

    if sucesso:
        agendar_inatividade(
            chave,
            chat_id,
            user_id,
            business_id
        )

    return sucesso


def encerrar_por_inatividade(chave, chat_id, user_id, business_id):
    with lock:
        timers.pop(chave, None)

        if chave not in estados:
            return

        if estados[chave] == "encerrado":
            return

        sucesso = telegram_send(
            chat_id,
            obter_texto(user_id, "encerramento"),
            business_id
        )

        if sucesso:
            estados[chave] = "encerrado"
            logging.info("Atendimento encerrado por inatividade: %s", chave)


def agendar_inatividade(chave, chat_id, user_id, business_id):
    cancelar_timer(chave)

    timer = threading.Timer(
        TEMPO_INATIVIDADE,
        encerrar_por_inatividade,
        args=(chave, chat_id, user_id, business_id)
    )

    timer.daemon = True
    timers[chave] = timer
    timer.start()

    logging.info("Temporizador de inatividade iniciado: %s", chave)


# =========================================================
# MENUS E SELEÇÃO DE IDIOMA
# =========================================================

def mostrar_selecao_idioma(chave, chat_id, user_id, business_id):
    cancelar_timer(chave)
    estados[chave] = "selecao_idioma"

    idioma_atual = obter_idioma(user_id)

    telegram_send(
        chat_id,
        TEXTOS[idioma_atual]["selecao"],
        business_id
    )


def mostrar_menu_principal(chave, chat_id, user_id, business_id):
    cancelar_timer(chave)
    cancelar_timer(f"{chave}:saque")

    estados[chave] = "menu_principal"

    enviar_resposta(
        chave,
        chat_id,
        user_id,
        obter_texto(user_id, "menu_principal"),
        business_id
    )


def mostrar_menu_plataforma(
    chave,
    chat_id,
    user_id,
    business_id,
    plataforma
):
    cancelar_timer(chave)

    estados[chave] = f"menu_{plataforma}"

    enviar_resposta(
        chave,
        chat_id,
        user_id,
        obter_texto(user_id, "menu_plataforma"),
        business_id
    )


# =========================================================
# TEMPORIZADOR DE SAQUE
# =========================================================

def finalizar_espera_saque(chave, chat_id, user_id, business_id):
    with lock:
        timers.pop(f"{chave}:saque", None)

        if estados.get(chave) != "aguardando_saque":
            return

        estados[chave] = "atendimento_ativo"

        enviar_resposta(
            chave,
            chat_id,
            user_id,
            obter_texto(user_id, "saque"),
            business_id
        )

        logging.info("Mensagem de processamento de saque enviada.")


def iniciar_temporizador_saque(chave, chat_id, user_id, business_id):
    cancelar_timer(chave)
    cancelar_timer(f"{chave}:saque")

    estados[chave] = "aguardando_saque"

    timer = threading.Timer(
        TEMPO_SAQUE,
        finalizar_espera_saque,
        args=(chave, chat_id, user_id, business_id)
    )

    timer.daemon = True
    timers[f"{chave}:saque"] = timer
    timer.start()

    logging.info("Temporizador de saque de 1 minuto iniciado: %s", chave)


# =========================================================
# PROCESSAMENTO DAS MENSAGENS
# =========================================================

def processar_mensagem(chat_id, business_id, user_id, texto):
    chave = f"{chat_id}:{business_id or 'normal'}"

    texto = texto.strip()
    texto_minusculo = texto.lower()

    with lock:

        # -------------------------------------------------
        # TROCAR IDIOMA
        # -------------------------------------------------

        if texto_minusculo in ("idioma", "/idioma"):
            cancelar_timer(chave)
            cancelar_timer(f"{chave}:saque")

            mostrar_selecao_idioma(
                chave,
                chat_id,
                user_id,
                business_id
            )
            return

        # -------------------------------------------------
        # SELEÇÃO DE IDIOMA
        # Esta verificação precisa vir antes dos menus.
        # -------------------------------------------------

        if estados.get(chave) == "selecao_idioma":

            novo_idioma = IDIOMAS.get(texto)

            if not novo_idioma:
                telegram_send(
                    chat_id,
                    TEXTOS[obter_idioma(user_id)]["idioma_invalido"],
                    business_id
                )
                return

            # Salva o idioma escolhido para o usuário.
            idiomas[user_id] = novo_idioma

            logging.info(
                "Idioma %s definido para o usuário %s",
                novo_idioma,
                user_id
            )

            # Envia automaticamente o menu no idioma escolhido.
            mostrar_menu_principal(
                chave,
                chat_id,
                user_id,
                business_id
            )
            return

        # -------------------------------------------------
        # PRIMEIRO CONTATO
        # -------------------------------------------------

        if user_id not in idiomas:
            mostrar_selecao_idioma(
                chave,
                chat_id,
                user_id,
                business_id
            )
            return

        # -------------------------------------------------
        # MENU SOLICITADO PELO USUÁRIO
        # -------------------------------------------------

        if texto_minusculo in ("menu", "/start"):
            cancelar_timer(chave)
            cancelar_timer(f"{chave}:saque")

            mostrar_menu_principal(
                chave,
                chat_id,
                user_id,
                business_id
            )
            return

        # Toda mensagem recebida cancela o temporizador
        # de inatividade de 5 minutos.
        cancelar_timer(chave)

        estado = estados.get(chave)

        # -------------------------------------------------
        # APÓS ENCERRAMENTO
        # -------------------------------------------------

        if estado == "encerrado":
            return

        # -------------------------------------------------
        # MENU PRINCIPAL
        # -------------------------------------------------

        if estado == "menu_principal":

            if texto == "1":
                mostrar_menu_plataforma(
                    chave,
                    chat_id,
                    user_id,
                    business_id,
                    "manga"
                )
                return

            if texto == "2":
                mostrar_menu_plataforma(
                    chave,
                    chat_id,
                    user_id,
                    business_id,
                    "jogomanga"
                )
                return

            if texto == "3":
                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    user_id,
                    obter_texto(user_id, "t1"),
                    business_id
                )
                return

            if texto == "4":
                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    user_id,
                    obter_texto(user_id, "fp"),
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                user_id,
                obter_texto(user_id, "fora_autonomia"),
                business_id
            )
            return

        # -------------------------------------------------
        # MENU GRUPO MANGA
        # -------------------------------------------------

        if estado == "menu_manga":

            respostas = TEXTOS[obter_idioma(user_id)]["manga"]

            if texto in respostas:

                if texto == "3":
                    estados[chave] = "aguardando_codigo_manga"

                    enviar_resposta(
                        chave,
                        chat_id,
                        user_id,
                        respostas["3"],
                        business_id
                    )
                    return

                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    user_id,
                    respostas[texto],
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                user_id,
                obter_texto(user_id, "fora_autonomia"),
                business_id
            )
            return

        # -------------------------------------------------
        # MENU JOGOMANGA
        # -------------------------------------------------

        if estado == "menu_jogomanga":

            respostas = TEXTOS[obter_idioma(user_id)]["jogomanga"]

            if texto in respostas:

                if texto == "3":
                    estados[chave] = "aguardando_codigo_jogomanga"

                    enviar_resposta(
                        chave,
                        chat_id,
                        user_id,
                        respostas["3"],
                        business_id
                    )
                    return

                estados[chave] = "atendimento_ativo"

                enviar_resposta(
                    chave,
                    chat_id,
                    user_id,
                    respostas[texto],
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                user_id,
                obter_texto(user_id, "fora_autonomia"),
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
                    user_id,
                    business_id
                )
                return

            enviar_resposta(
                chave,
                chat_id,
                user_id,
                obter_texto(user_id, "fora_autonomia"),
                business_id
            )
            return

        # -------------------------------------------------
        # AGUARDANDO SAQUE
        # -------------------------------------------------

        if estado == "aguardando_saque":
            # A contagem de 1 minuto continua.
            # O jogador pode digitar "menu" para cancelá-la.
            return

        # -------------------------------------------------
        # OUTRAS MENSAGENS
        # -------------------------------------------------

        enviar_resposta(
            chave,
            chat_id,
            user_id,
            obter_texto(user_id, "fora_autonomia"),
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

    user_id = remetente.get("id")

    if not user_id:
        logging.info("Mensagem ignorada: usuário sem ID.")
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
            user_id,
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
