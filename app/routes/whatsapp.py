from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.services.whatsapp_service import enviar_whatsapp
from app.services.ia_agent import responder_ia

router = APIRouter(prefix="/webhook/whatsapp", tags=["WhatsApp"])

CONVERSAS = {}


class SendMessageRequest(BaseModel):
    numero: str
    mensagem: str


def limpar_numero(numero: str):
    if not numero:
        return None

    return (
        str(numero)
        .replace("@s.whatsapp.net", "")
        .replace("@c.us", "")
        .replace("+", "")
        .strip()
    )


def extrair_mensagem_webhook(payload: dict):
    """
    Extrai número, mensagem e tipo do payload UAZAPI.
    """

    data = payload.get("data", {})
    key = data.get("key", {})
    message = data.get("message", {})

    # Ignora grupos
    remote_jid = key.get("remoteJid") or data.get("remoteJid")
    if remote_jid and "@g.us" in remote_jid:
        return None, None, "grupo"

    # Ignora mensagens enviadas pelo próprio bot
    if key.get("fromMe") is True:
        return None, None, "fromMe"

    numero = (
        payload.get("number")
        or payload.get("phone")
        or payload.get("from")
        or payload.get("remoteJid")
        or data.get("number")
        or data.get("phone")
        or data.get("from")
        or remote_jid
    )

    numero = limpar_numero(numero)

    mensagem = (
        payload.get("text")
        or payload.get("body")
        or payload.get("message")
        or data.get("text")
        or data.get("body")
        or message.get("conversation")
        or message.get("extendedTextMessage", {}).get("text")
        or message.get("imageMessage", {}).get("caption")
        or message.get("videoMessage", {}).get("caption")
        or message.get("documentMessage", {}).get("caption")
    )

    tipo = "texto"

    if message.get("audioMessage"):
        tipo = "audio"
    elif message.get("imageMessage"):
        tipo = "imagem"
    elif message.get("documentMessage"):
        tipo = "documento"
    elif message.get("videoMessage"):
        tipo = "video"

    return numero, mensagem, tipo


@router.post("/send")
async def send_message(data: SendMessageRequest):
    try:
        response = enviar_whatsapp(
            numero=data.numero,
            texto=data.mensagem
        )

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return {
            "success": response.ok,
            "status_code": response.status_code,
            "response": response_body
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook para conversação automática via WhatsApp.
    """
    try:
        payload = await request.json()

        print("=" * 80)
        print("PAYLOAD WEBHOOK:", payload)
        print("=" * 80)

        numero, mensagem, tipo = extrair_mensagem_webhook(payload)

        if not numero:
            return {
                "success": False,
                "ignored": True,
                "reason": "Número não encontrado no payload.",
                "tipo": tipo,
                "payload": payload,
            }

        if not mensagem:
            resposta_audio = (
                "Olá! Para agilizar o atendimento do SAC, por favor descreva "
                "a situação por escrito e envie as informações necessárias."
            )

            response = enviar_whatsapp(numero=numero, texto=resposta_audio)

            return {
                "success": response.ok,
                "ignored": False,
                "status_code": response.status_code,
                "numero": numero,
                "tipo": tipo,
                "resposta": resposta_audio,
            }

        historico = CONVERSAS.get(numero, [])

        resposta_ia = responder_ia(
            mensagem=mensagem,
            historico=historico
        )

        historico.append({
            "role": "user",
            "content": mensagem
        })

        historico.append({
            "role": "assistant",
            "content": resposta_ia
        })

        CONVERSAS[numero] = historico[-20:]

        response = enviar_whatsapp(
            numero=numero,
            texto=resposta_ia
        )

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return {
            "success": response.ok,
            "ignored": False,
            "status_code": response.status_code,
            "numero": numero,
            "tipo": tipo,
            "mensagem": mensagem,
            "resposta": resposta_ia,
            "response": response_body,
        }

    except Exception as e:
        print("ERRO WEBHOOK:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
