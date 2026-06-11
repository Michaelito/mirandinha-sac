# app/services/whatsapp_service.py

import requests
from app.config import UAZAPI_URL, UAZAPI_TOKEN


def enviar_whatsapp(numero: str, texto: str):
    """Envia mensagem de texto pelo UAZAPI."""
    response = requests.post(
        f"{UAZAPI_URL}/send/text",
        json={
            "number": numero,
            "text": texto,
            "linkPreview": False,
            "readchat": True,
            "delay": 0,
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "token": UAZAPI_TOKEN,
        },
        timeout=30,
    )

    return response


def extrair_mensagem_webhook(payload: dict) -> tuple[str | None, str | None, str | None]:
    """
    Tenta extrair número, texto e tipo da mensagem recebida no webhook.
    Mantido flexível para diferentes formatos de payload do UAZAPI.

    Retorna: (numero, texto, tipo)
    """
    data = payload.get("data") or payload.get("message") or payload

    tipo = (
        data.get("type")
        or data.get("messageType")
        or payload.get("type")
        or payload.get("event")
    )

    numero = (
        data.get("from")
        or data.get("number")
        or data.get("phone")
        or data.get("remoteJid")
        or data.get("chatId")
        or payload.get("from")
        or payload.get("number")
        or payload.get("phone")
    )

    texto = (
        data.get("text")
        or data.get("body")
        or data.get("message")
        or data.get("content")
        or payload.get("text")
        or payload.get("body")
        or payload.get("message")
    )

    # Alguns webhooks chegam como {"text": {"body": "..."}}
    if isinstance(texto, dict):
        texto = texto.get("body") or texto.get("text") or texto.get("message")

    # Alguns webhooks chegam como message.conversation ou message.extendedTextMessage.text
    if not texto and isinstance(data.get("message"), dict):
        msg = data["message"]
        texto = (
            msg.get("conversation")
            or (msg.get("extendedTextMessage") or {}).get("text")
            or (msg.get("text") or {}).get("body")
        )

    if numero:
        numero = str(numero).replace("@s.whatsapp.net", "").replace("@c.us", "")

    return numero, texto, tipo
