# app/services/whatsapp_service.py

from typing import Any, Dict, Optional, Tuple

import requests
from app.config import UAZAPI_TOKEN, UAZAPI_URL


def enviar_whatsapp(numero: str, texto: str):
    response = requests.post(
        f"{UAZAPI_URL}/send/text",
        json={
            "number": numero,
            "text": texto
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "token": UAZAPI_TOKEN
        },
        timeout=30
    )

    print("[UAZAPI]", response.status_code, response.text)

    return response


def extrair_mensagem_webhook(
    payload: Dict[str, Any],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Tenta extrair número, texto e tipo da mensagem recebida no webhook.
    Compatível com Python 3.9.

    Retorna: (numero, texto, tipo)
    """
    data = payload.get("data") or payload.get("message") or payload

    if not isinstance(data, dict):
        data = payload

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
        or data.get("content")
        or payload.get("text")
        or payload.get("body")
    )

    # Alguns webhooks chegam como {"text": {"body": "..."}}
    if isinstance(texto, dict):
        texto = texto.get("body") or texto.get("text") or texto.get("message")

    # Alguns webhooks chegam como message.conversation ou message.extendedTextMessage.text
    message_data = data.get("message")
    if not texto and isinstance(message_data, dict):
        texto = (
            message_data.get("conversation")
            or (message_data.get("extendedTextMessage") or {}).get("text")
            or (message_data.get("text") or {}).get("body")
        )

    if numero:
        numero = str(numero).replace(
            "@s.whatsapp.net", "").replace("@c.us", "")

    if texto:
        texto = str(texto).strip()

    if tipo:
        tipo = str(tipo)

    return numero, texto, tipo
