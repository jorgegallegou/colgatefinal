# Agente Conversacional Corporativo — Colgate-Palmolive Colombia
### Módulo 3 · Ruta B: Sistema Operativo Agéntico (OpenFang 0.6.9)
**Universidad Autónoma de Occidente · Técnicas de Inteligencia Artificial**

---

## Descripción

Bot de WhatsApp que atiende consultas de consumidores sobre Colgate-Palmolive Colombia en tiempo real, con memoria corporativa inyectada por RAG y operaciones autónomas de inteligencia competitiva ejecutadas en segundo plano.

## Arquitectura

```
Usuario WhatsApp
      │
      ▼ (WebSocket Baileys)
Baileys Gateway  ──────────────────  Node.js  puerto 3009
      │          resolveAgentId()
      │          getOrCreateSession(phone)
      │          toWhatsApp(markdown)
      │
      ▼ POST /api/agents/{uuid}/message?session_id={sid}
OpenFang Kernel  ──────────────────  Rust  puerto 4200
      │          KV Store  (NIT, contactos, sedes)
      │          Vector Store  (235 fragmentos RAG)
      │          Sesiones JSONL por usuario
      │          Hands autónomos (cada 6h / semanal)
      │
      ▼ HTTPS
Mistral API  ───────────────────────  mistral-small-latest
```

## Hands Autónomos

| Hand | Tipo | Schedule | Propósito |
|---|---|---|---|
| `colgate-intelligence-hand` | Collector (Opción B) | cada 6 horas | Inteligencia competitiva: P&G, Unilever, tendencias mercado |
| `colgate-service-hand` | Custom (Opción C) | lunes 9 AM | Calidad de servicio: opiniones consumidores en redes |

Activar manualmente:
```bash
openfang hand activate collector --name colgate-intelligence
openfang hand activate lead     --name colgate-leads
```

## Estructura del Repositorio

```
colgatefinal/
├── hand.toml                  # Manifiesto del agente, modelo, memoria, Hands y canal WhatsApp
├── .env.example               # Plantilla de variables de entorno (sin credenciales)
├── .gitignore
│
├── scraper.py                 # Web scraping sitio oficial Colgate Colombia
├── scraper_wikipedia.py       # Scraping artículo Wikipedia Colgate-Palmolive
├── scraper_youtube.py         # Transcripciones canal YouTube oficial
├── clean_knowledge_base.py    # Limpieza y normalización del KB (~235 fragmentos)
├── build_vectorstore.py       # Inyección en Vector Store de OpenFang
│
├── webhook_server.py          # FastAPI webhook alternativo (Meta Cloud API)
├── config.py                  # Configuración centralizada
│
├── tsne_analysis.py           # Análisis t-SNE de intenciones de usuario (bonus +10%)
│
├── data/
│   ├── knowledge_base_clean.txt   # KB limpia lista para inyección
│   ├── datos_estructurados.json   # KV Store: NIT, contactos, sedes, marcas
│   ├── paginas_raw.json
│   ├── wikipedia_raw.json
│   └── youtube_raw.json
│
├── INFORME_TECNICO.md         # Informe técnico completo (fuente)
└── INFORME_TECNICO.pdf        # Informe técnico compilado (entrega)
```

> El gateway de WhatsApp (`index.js`) vive en `C:\Users\<user>\.openfang\whatsapp-gateway\` y no se versiona por contener credenciales de sesión de Baileys.

## Configuración Rápida

### 1. Variables de entorno

```bash
cp .env.example .env
# Completar: MISTRAL_API_KEY, WA_ACCESS_TOKEN, OPENFANG_AGENT_ID
```

### 2. Iniciar OpenFang

```bash
openfang start
openfang status   # verificar que colgate-assistant aparece Running
```

### 3. Iniciar gateway WhatsApp

```bash
cd C:\Users\<user>\.openfang\whatsapp-gateway
set OPENFANG_DEFAULT_AGENT=<uuid-del-agente>
set OPENFANG_URL=http://127.0.0.1:4200
node index.js
# Escanear QR con WhatsApp en el primer arranque
```

### 4. Verificar

```bash
curl -X POST http://127.0.0.1:4200/api/agents/<uuid>/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola"}'
# Esperado: "Hola, soy el asistente virtual de Colgate-Palmolive Colombia..."
```

## Variables de Entorno

| Variable | Descripción |
|---|---|
| `MISTRAL_API_KEY` | API key de Mistral AI (console.mistral.ai) |
| `WA_ACCESS_TOKEN` | Token de sesión WhatsApp Web (Baileys) |
| `WA_PHONE_NUMBER_ID` | ID del número WhatsApp Business |
| `WA_VERIFY_TOKEN` | Token de verificación webhook (valor libre) |
| `OPENFANG_URL` | URL del daemon OpenFang (default: `http://127.0.0.1:4200`) |
| `OPENFANG_AGENT_ID` | UUID del agente `colgate-assistant` |

## Análisis t-SNE (Bonus)

```bash
uv run python tsne_analysis.py
# Genera tsne_conversaciones.png con clusters de intenciones de usuario
```

Requiere sesiones activas en `~/.openfang/workspaces/colgate-assistant/sessions/`.
Con menos de 5 sesiones usa datos de ejemplo representativos.

## Tecnologías

- **OpenFang 0.6.9** — Agent OS (kernel Rust, WASM sandbox)
- **Baileys** (`@whiskeysockets/baileys`) — WhatsApp Web protocol bridge
- **Mistral AI** (`mistral-small-latest`) — LLM provider
- **Python 3.14** + `uv` — scripts de ingesta y análisis
- **FastAPI** — webhook alternativo (Meta Cloud API)
- **scikit-learn / matplotlib** — t-SNE y visualización

## Licencia

Proyecto académico — Universidad Autónoma de Occidente, 2026.
