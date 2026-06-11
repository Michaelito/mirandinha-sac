from fastapi import FastAPI
from app.routes.whatsapp import router as whatsapp_router

app = FastAPI(title="Agente IA WhatsApp")
app.include_router(whatsapp_router, prefix="/webhook")


# uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
