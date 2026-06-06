# Agente Conversacional Corporativo — Colgate-Palmolive Colombia

> Agente de IA desplegado en WhatsApp. Atiende consultas de consumidores las 24 horas mediante RAG sobre datos reales de la empresa, con vigilancia competitiva autónoma ejecutándose en segundo plano.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![OpenFang](https://img.shields.io/badge/OpenFang-0.6.9-orange)
![Mistral](https://img.shields.io/badge/Mistral-small--latest-purple)
![Licencia](https://img.shields.io/badge/Licencia-Académica-lightgrey)

---

## Descripción general

Este proyecto implementa un agente conversacional corporativo para Colgate-Palmolive Colombia usando **OpenFang 0.6.9** como sistema operativo agéntico. El agente es accesible vía WhatsApp y está respaldado por una base de conocimiento construida a partir de fuentes oficiales de la empresa (scraping web, Wikipedia, YouTube).

Capacidades principales:

- **Respuestas en tiempo real** — productos, puntos de venta, historia, sostenibilidad y contacto
- **Aislamiento de sesiones por usuario** — cada número de teléfono tiene su propio contexto de conversación
- **Recuperación semántica (RAG)** — 235 fragmentos indexados en un Vector Store con Mistral Embeddings
- **Hands autónomos** — agentes en background que recolectan inteligencia competitiva cada 6 horas

---

## Arquitectura

```
Usuario WhatsApp
      │
      │  Protocolo WhatsApp Web (WebSocket)
      ▼
┌──────────────────────────────────────┐
│  Gateway Baileys                     │
│  Node.js · Puerto 3009               │
│  ~/.openfang/whatsapp-gateway/       │
└─────────────────┬────────────────────┘
                  │  POST /api/agents/{uuid}/message?session_id={sid}
                  ▼
┌──────────────────────────────────────┐
│  OpenFang Kernel                     │
│  Rust · Puerto 4200                  │
│                                      │
│  Agente: colgate-assistant           │
│  ├─ KV Store      (NIT, contactos)   │
│  ├─ Vector Store  (235 fragmentos)   │
│  ├─ Sesiones JSONL (por usuario)     │
│  └─ Hands autónomos (cron)           │
└─────────────────┬────────────────────┘
                  │  HTTPS
                  ▼
          Mistral AI Cloud
       mistral-small-latest
```

---

## Requisitos previos

| Requisito | Versión | Notas |
|---|---|---|
| [OpenFang](https://openfang.sh) | 0.6.9 | Agent OS — instalar con `curl -fsSL https://openfang.sh/install \| sh` |
| Node.js | 18+ | Para el gateway Baileys de WhatsApp |
| Python | 3.14 | Gestionado con `uv` |
| [Mistral AI API key](https://console.mistral.ai) | — | Nivel gratuito disponible |

---

## Inicio rápido

### 1. Clonar y configurar

```bash
git clone https://github.com/jorgegallegou/colgatefinal.git
cd colgatefinal

cp .env.example .env
# Completar: MISTRAL_API_KEY, WA_ACCESS_TOKEN, OPENFANG_AGENT_ID
```

### 2. Instalar dependencias Python

```bash
pip install uv
uv sync
```

### 3. Iniciar OpenFang y registrar el agente

```bash
openfang start
python main.py setup
```

`setup` realiza tres verificaciones en orden: confirma que el daemon OpenFang responde en el puerto 4200, valida que `MISTRAL_API_KEY` está presente en el entorno, y registra el agente `colgate-assistant` desde `hand.toml` con `openfang agent spawn`. Si el agente ya existe, lo omite sin error. Al finalizar imprime el UUID asignado — copie ese valor en `OPENFANG_AGENT_ID` del `.env`.

### 4. Cargar la base de conocimiento

```bash
python main.py ingest
```

Ejecuta `scripts/ingest.py` en dos fases:

1. **KV Store** — lee `data/datos_estructurados.json` e inyecta cada par clave-valor vía `POST /api/agents/{id}/memory/kv`. Almacena datos exactos: NIT, línea gratuita, sedes, marcas.
2. **Vector Store** — lee `data/knowledge_base_clean.txt`, divide el contenido en fragmentos y los envía como mensajes de tipo `knowledge`. OpenFang los vectoriza con `mistral-embed` (1024 dims) y los indexa para búsqueda semántica. Total: ~235 fragmentos.

### 5. Activar Hands autónomos

```bash
python main.py hand
```

Activa dos agentes en background mediante `openfang hand activate`:

- `colgate-intelligence-hand` (tipo `collector`) — cron `0 */6 * * *`, busca en web y noticias sobre Colgate Colombia y competidores. Almacena hallazgos en memoria del agente principal.
- `colgate-service-hand` (tipo `custom`) — cron `0 9 * * 1`, consolida opiniones de consumidores en redes. Genera reporte JSON.

Si alguno ya estaba activo, el comando lo detecta y continúa sin error.

### 6. Iniciar el gateway de WhatsApp

```powershell
cd $env:USERPROFILE\.openfang\whatsapp-gateway
$env:OPENFANG_DEFAULT_AGENT = "<uuid-del-agente>"
$env:OPENFANG_URL = "http://127.0.0.1:4200"
node index.js
# Escanear el código QR con WhatsApp en el primer arranque
```

El gateway usa Baileys para conectarse al protocolo WhatsApp Web vía WebSocket. En el primer arranque genera un QR — escanearlo vincula la sesión. A partir de ese momento el proceso mantiene la conexión activa. Por cada mensaje entrante: resuelve el UUID del agente, crea o recupera la sesión del número de teléfono, consulta OpenFang y convierte la respuesta de Markdown a formato nativo de WhatsApp antes de enviarla.

### 7. Verificar el estado

```bash
python main.py status
```

Reporta: estado del daemon OpenFang, UUID y estado del agente `colgate-assistant`, número de pares en el KV Store, estado del canal WhatsApp y lista de Hands activos.

---

## Configuración

Todos los secretos se cargan desde `.env`. Copie `.env.example` para comenzar — no contiene credenciales reales.

| Variable | Requerida | Descripción |
|---|---|---|
| `MISTRAL_API_KEY` | Sí | API key de Mistral AI |
| `WA_ACCESS_TOKEN` | Sí | Token de acceso WhatsApp Business |
| `WA_PHONE_NUMBER_ID` | Sí | ID del número de teléfono WhatsApp Business |
| `WA_VERIFY_TOKEN` | Sí | Token de verificación del webhook (valor libre) |
| `OPENFANG_URL` | No | URL del daemon OpenFang (por defecto: `http://127.0.0.1:4200`) |
| `OPENFANG_AGENT_ID` | Sí | UUID del agente — obtener con `openfang agent list` |

---

## Hands Autónomos

Los Hands son agentes en background definidos en `hand.toml` que se ejecutan de forma programada sin intervención humana.

| Hand | Tipo | Frecuencia | Propósito |
|---|---|---|---|
| `colgate-intelligence-hand` | Collector | Cada 6 horas | Vigilancia competitiva: P&G, Unilever, tendencias del mercado |
| `colgate-service-hand` | Custom | Lunes 9 AM | Monitoreo de opiniones de consumidores en redes sociales |

Los reportes de inteligencia se almacenan en la memoria del agente y quedan disponibles para consultas RAG.

---

## Estructura del proyecto

```
colgatefinal/
│
├── hand.toml                  # Manifiesto del agente: modelo, memoria, Hands y canal WA
├── main.py                    # CLI: setup / ingest / hand / status / whatsapp
├── pyproject.toml             # Dependencias Python (uv)
├── .env.example               # Plantilla de variables de entorno
│
├── scripts/
│   ├── ingest.py              # Inyección de KB en KV Store y Vector Store de OpenFang
│   └── whatsapp_bridge.py     # Helper de configuración del canal WhatsApp
│
├── webhook_server.py          # Webhook FastAPI alternativo (Meta Cloud API)
├── tsne_analysis.py           # Análisis de clustering de intenciones vía t-SNE
│
├── informe.css                # Estilos del PDF (Inter + JetBrains Mono)
├── INFORME_TECNICO.md         # Informe técnico del proyecto
│
└── data/
    ├── knowledge_base_clean.txt   # Base de conocimiento (~235 fragmentos)
    └── datos_estructurados.json   # NIT, teléfonos, sedes, marcas
```

> El gateway de WhatsApp (`index.js`) no está en el repositorio — contiene la sesión activa de Baileys, equivalente a las credenciales de acceso de la cuenta.

---

## Análisis de clustering de intenciones

Visualiza los tipos de consulta de los usuarios agrupados por intención usando Mistral Embeddings y t-SNE.

```bash
uv run python tsne_analysis.py
# Salida: tsne_conversaciones.png
```

Con menos de 5 sesiones reales el script usa un conjunto de 20 conversaciones de ejemplo representativas.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Agent OS | OpenFang 0.6.9 (kernel Rust, sandbox WASM) |
| Canal WhatsApp | Baileys `@whiskeysockets/baileys` (Node.js) |
| LLM | Mistral AI `mistral-small-latest` |
| Embeddings | Mistral `mistral-embed` (1024 dimensiones) |
| Scripts | Python 3.14 + `uv` |
| Webhook | FastAPI + uvicorn |
| Visualización | scikit-learn, matplotlib |

---

## Licencia

Proyecto académico — Universidad Autónoma de Occidente, 2026.
