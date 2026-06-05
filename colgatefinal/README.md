# Agente Conversacional — Colgate-Palmolive Colombia

**Módulo 3 · Ruta B: Sistema Operativo Agéntico**
Universidad Autónoma de Occidente · Técnicas de Inteligencia Artificial · 2026

---

## Descripción

Bot de WhatsApp que atiende consultas de consumidores sobre Colgate-Palmolive Colombia en tiempo real. Tiene memoria corporativa construida con web scraping real de la empresa, distingue entre usuarios (cada conversación es independiente) y ejecuta vigilancia competitiva de forma autónoma cada 6 horas.

---

## Arquitectura

```
Usuario WhatsApp
      │
      ▼  WebSocket (protocolo WhatsApp Web)
┌─────────────────────────────────┐
│  Baileys Gateway                │  Node.js · puerto 3009
│  ~/.openfang/whatsapp-gateway/  │
└──────────────┬──────────────────┘
               │  POST /api/agents/{uuid}/message?session_id={sid}
               ▼
┌─────────────────────────────────┐
│  OpenFang Kernel                │  Rust · puerto 4200
│  Agente: colgate-assistant      │
│  · KV Store   (NIT, contactos)  │
│  · Vector Store (235 fragmentos)│
│  · Sesiones por usuario         │
│  · Hands autónomos              │
└──────────────┬──────────────────┘
               │  HTTPS
               ▼
         Mistral AI
     mistral-small-latest
```

---

## Hands Autónomos

Procesos que corren en segundo plano sin intervención humana.

| Hand | Frecuencia | Función |
|---|---|---|
| `colgate-intelligence-hand` | Cada 6 horas | Vigilancia competitiva: P&G, Unilever, tendencias |
| `colgate-service-hand` | Lunes 9 AM | Opiniones de consumidores en redes sociales |

---

## Configuración

### 1. Variables de entorno

```bash
cp .env.example .env
# Editar .env con: MISTRAL_API_KEY, WA_ACCESS_TOKEN, OPENFANG_AGENT_ID
```

| Variable | Descripción |
|---|---|
| `MISTRAL_API_KEY` | API key de Mistral AI — console.mistral.ai |
| `WA_ACCESS_TOKEN` | Token de acceso WhatsApp Business |
| `WA_PHONE_NUMBER_ID` | ID del número WhatsApp Business |
| `WA_VERIFY_TOKEN` | Token de verificación webhook (valor libre) |
| `OPENFANG_URL` | URL del daemon OpenFang (default: `http://127.0.0.1:4200`) |
| `OPENFANG_AGENT_ID` | UUID del agente — obtener con `openfang agent list` |

### 2. Iniciar OpenFang y registrar el agente

```bash
openfang start
python main.py setup        # verifica OpenFang, Mistral y registra el agente
```

### 3. Inyectar conocimiento corporativo

```bash
python main.py ingest       # carga KV Store y Vector Store (~235 fragmentos)
```

### 4. Activar Hands autónomos

```bash
python main.py hand         # activa colgate-intelligence-hand y colgate-service-hand
```

### 5. Iniciar gateway WhatsApp

```bash
# En PowerShell, desde la carpeta del gateway:
cd $env:USERPROFILE\.openfang\whatsapp-gateway
$env:OPENFANG_DEFAULT_AGENT = "<uuid-del-agente>"
$env:OPENFANG_URL = "http://127.0.0.1:4200"
node index.js
# Escanear el QR con WhatsApp en el primer arranque
```

### 6. Verificar

```bash
python main.py status       # estado del agente, KV Store, canal y Hands
```

---

## Estructura del Repositorio

```
colgatefinal/
│
├── hand.toml                  # Manifiesto del agente: modelo, memoria, Hands y canal WA
├── main.py                    # CLI: setup / ingest / hand / status / whatsapp
├── pyproject.toml             # Dependencias Python (uv)
├── .env.example               # Plantilla de variables de entorno (sin credenciales)
│
├── scripts/
│   ├── ingest.py              # Inyección de conocimiento en KV Store y Vector Store
│   └── whatsapp_bridge.py     # Helper de configuración del canal WhatsApp
│
├── webhook_server.py          # FastAPI webhook alternativo (Meta Cloud API)
├── tsne_analysis.py           # Análisis t-SNE de intenciones de usuario (bonus)
│
├── informe.css                # Estilos del PDF (tipografía Inter + JetBrains Mono)
├── INFORME_TECNICO.md         # Informe técnico (fuente)
├── INFORME_TECNICO.pdf        # Informe técnico (entrega)
│
└── data/
    ├── knowledge_base_clean.txt   # Base de conocimiento (~235 fragmentos)
    └── datos_estructurados.json   # NIT, teléfonos, sedes, marcas
```

> El gateway de WhatsApp (`index.js`) no está en el repositorio: contiene la sesión activa de Baileys, equivalente a las credenciales de la cuenta de WhatsApp.

---

## Análisis t-SNE (Bonus)

Visualiza los tipos de preguntas que hacen los usuarios agrupados por intención.

```bash
uv run python tsne_analysis.py
# Genera: tsne_conversaciones.png
```

Con menos de 5 sesiones reales usa datos de ejemplo representativos.

---

## Tecnologías

| Componente | Tecnología |
|---|---|
| Agent OS | OpenFang 0.6.9 (kernel Rust, WASM sandbox) |
| WhatsApp bridge | Baileys `@whiskeysockets/baileys` |
| LLM | Mistral AI `mistral-small-latest` |
| Scripts | Python 3.14 + `uv` |
| Webhook alternativo | FastAPI + uvicorn |
| Análisis | scikit-learn, matplotlib |
