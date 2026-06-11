# app/routes/whatsapp.py

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.services.ia_agent import responder_ia
from app.services.whatsapp_service import enviar_whatsapp, extrair_mensagem_webhook

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# Memória simples em RAM para manter contexto da conversa.
# Em produção, substitua por Redis, banco de dados ou tabela de mensagens.
CONVERSAS: dict[str, list[dict]] = {}


class SendMessageRequest(BaseModel):
    numero: str
    mensagem: str


@router.post("/send")
async def send_message(data: SendMessageRequest):
    try:
        response = enviar_whatsapp(
            numero=data.numero,
            texto=data.mensagem,
        )

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return {
            "success": response.ok,
            "status_code": response.status_code,
            "response": response_body,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook para conversação automática via WhatsApp.

    Fluxo:
    1. Recebe payload do UAZAPI.
    2. Extrai número e mensagem recebida.
    3. Envia mensagem para IA com histórico da conversa.
    4. Responde automaticamente no WhatsApp.
    """
    try:
        payload = await request.json()
        numero, mensagem, tipo = extrair_mensagem_webhook(payload)

        if not numero:
            return {
                "success": False,
                "ignored": True,
                "reason": "Número não encontrado no payload.",
            }

        if not mensagem:
            resposta_audio = (
                "Olá! Para agilizar o atendimento do SAC, por favor descreva "
                "a situação por escrito e envie as informações necessárias."
            )
            enviar_whatsapp(numero=numero, texto=resposta_audio)
            return {
                "success": True,
                "ignored": False,
                "numero": numero,
                "tipo": tipo,
                "resposta": resposta_audio,
            }

        historico = CONVERSAS.get(numero, [])
        resposta_ia = responder_ia(mensagem=mensagem, historico=historico)

        historico.append({"role": "user", "content": mensagem})
        historico.append({"role": "assistant", "content": resposta_ia})
        CONVERSAS[numero] = historico[-20:]

        response = enviar_whatsapp(numero=numero, texto=resposta_ia)

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return {
            "success": response.ok,
            "status_code": response.status_code,
            "numero": numero,
            "tipo": tipo,
            "resposta": resposta_ia,
            "response": response_body,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
