"""
Servidor webhook para integrar Meta WhatsApp Cloud API con OpenFang.
Recibe mensajes de WhatsApp, los reenvía al agente y devuelve la respuesta.

Variables de entorno requeridas (ver .env.example):
    WA_VERIFY_TOKEN      Token de verificación del webhook (Meta Developer Console)
    WA_ACCESS_TOKEN      Token de acceso de WhatsApp Business API
    WA_PHONE_NUMBER_ID   ID del número de teléfono de WhatsApp Business
    OPENFANG_AGENT_ID    UUID del agente en OpenFang (ver: openfang agent list)
    OPENFANG_URL         URL de la API REST de OpenFang (default: http://127.0.0.1:50051)

Ejecutar:
    uvicorn webhook_server:app --host 0.0.0.0 --port 8000
"""

import os
import sys
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse


def _load_env() -> None:
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


_load_env()

WA_VERIFY_TOKEN    = os.environ.get("WA_VERIFY_TOKEN", "")
WA_ACCESS_TOKEN    = os.environ.get("WA_ACCESS_TOKEN", "")
WA_PHONE_NUMBER_ID = os.environ.get("WA_PHONE_NUMBER_ID", "")
OPENFANG_URL       = os.environ.get("OPENFANG_URL", "http://127.0.0.1:50051")
OPENFANG_AGENT_ID  = os.environ.get("OPENFANG_AGENT_ID", "")
WA_API_VERSION     = os.environ.get("WA_API_VERSION", "v22.0")

_REQUIRED = {
    "WA_VERIFY_TOKEN": WA_VERIFY_TOKEN,
    "WA_ACCESS_TOKEN": WA_ACCESS_TOKEN,
    "WA_PHONE_NUMBER_ID": WA_PHONE_NUMBER_ID,
    "OPENFANG_AGENT_ID": OPENFANG_AGENT_ID,
}

_missing = [k for k, v in _REQUIRED.items() if not v]
if _missing:
    print(f"ERROR: Variables de entorno faltantes: {', '.join(_missing)}")
    print("Revisa el archivo .env (copia desde .env.example)")
    sys.exit(1)

app = FastAPI(title="Colgate WhatsApp Webhook")


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode      = request.query_params.get("hub.mode")
    token     = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WA_VERIFY_TOKEN:
        print(f"Webhook verificado. Challenge: {challenge}")
        return PlainTextResponse(content=challenge)

    print(f"Verificacion fallida. Token recibido: {token!r}")
    raise HTTPException(status_code=403, detail="Token de verificacion incorrecto")


@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()

    try:
        value = body["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return {"status": "ignored"}

        message     = value["messages"][0]
        from_number = message["from"]
        msg_type    = message.get("type", "")

        if msg_type == "text":
            user_text = message["text"]["body"]
        elif msg_type == "interactive":
            user_text = message["interactive"].get("button_reply", {}).get("title", "")
        else:
            return {"status": "unsupported_type"}

        print(f"[WA] {from_number}: {user_text}")

        agent_reply = await _query_agent(user_text, from_number)
        print(f"[Agente] {agent_reply}")

        await _send_whatsapp(from_number, agent_reply)

    except (KeyError, IndexError) as e:
        print(f"Error procesando payload: {e}")

    return {"status": "ok"}


async def _query_agent(text: str, session_id: str) -> str:
    url     = f"{OPENFANG_URL}/api/agents/{OPENFANG_AGENT_ID}/message"
    payload = {"message": text, "session_id": session_id}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r    = await client.post(url, json=payload)
            data = r.json()
            return data.get("response") or data.get("message") or "No pude procesar tu consulta."
    except Exception as e:
        print(f"Error consultando agente OpenFang: {e}")
        return "En este momento no pude procesar tu consulta. Por favor intenta de nuevo."


async def _send_whatsapp(to: str, text: str) -> None:
    url = f"https://graph.facebook.com/{WA_API_VERSION}/{WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code != 200:
                print(f"Error WA API {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Error enviando mensaje WhatsApp: {e}")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agent_id": OPENFANG_AGENT_ID,
        "phone_id": WA_PHONE_NUMBER_ID,
        "openfang_url": OPENFANG_URL,
    }


if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor webhook en http://0.0.0.0:8000")
    print(f"Verify token: {WA_VERIFY_TOKEN}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
