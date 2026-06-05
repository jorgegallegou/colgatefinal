# Colgate-Palmolive Colombia — WhatsApp Conversational Agent

> Corporate AI agent deployed on WhatsApp. Answers consumer queries 24/7 using RAG over real company data, with autonomous competitive intelligence running in the background.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![OpenFang](https://img.shields.io/badge/OpenFang-0.6.9-orange)
![Mistral](https://img.shields.io/badge/Mistral-small--latest-purple)
![License](https://img.shields.io/badge/License-Academic-lightgrey)

---

## Overview

This project implements a production-grade conversational agent for Colgate-Palmolive Colombia using **OpenFang 0.6.9** as the agent operating system. The agent is accessible via WhatsApp and is backed by a knowledge base built from official company sources (web scraping, Wikipedia, YouTube).

Key capabilities:

- **Real-time Q&A** — answers questions about products, stores, history, sustainability and contact info
- **Per-user session isolation** — each phone number gets its own conversation context
- **RAG retrieval** — 235 knowledge fragments indexed in a vector store (Mistral Embeddings)
- **Autonomous Hands** — background agents that collect competitive intelligence every 6 hours

---

## Architecture

```
WhatsApp User
      │
      │  WhatsApp Web Protocol (WebSocket)
      ▼
┌──────────────────────────────────────┐
│  Baileys Gateway                     │
│  Node.js · Port 3009                 │
│  ~/.openfang/whatsapp-gateway/       │
└─────────────────┬────────────────────┘
                  │  POST /api/agents/{uuid}/message?session_id={sid}
                  ▼
┌──────────────────────────────────────┐
│  OpenFang Kernel                     │
│  Rust · Port 4200                    │
│                                      │
│  Agent: colgate-assistant            │
│  ├─ KV Store   (NIT, phones, HQ)     │
│  ├─ Vector Store (235 fragments)     │
│  ├─ JSONL sessions (per user)        │
│  └─ Autonomous Hands (cron)          │
└─────────────────┬────────────────────┘
                  │  HTTPS
                  ▼
        Mistral AI Cloud
      mistral-small-latest
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| [OpenFang](https://openfang.sh) | 0.6.9 | Agent OS — install with `curl -fsSL https://openfang.sh/install \| sh` |
| Node.js | 18+ | For the Baileys WhatsApp gateway |
| Python | 3.14 | Managed with `uv` |
| [Mistral AI API key](https://console.mistral.ai) | — | Free tier available |

---

## Getting Started

### 1. Clone and configure

```bash
git clone https://github.com/jorgegallegou/colgatefinal.git
cd colgatefinal

cp .env.example .env
# Fill in MISTRAL_API_KEY, WA_ACCESS_TOKEN, OPENFANG_AGENT_ID
```

### 2. Install Python dependencies

```bash
pip install uv
uv sync
```

### 3. Start OpenFang and register the agent

```bash
openfang start
python main.py setup
```

`setup` verifies OpenFang connectivity, validates the Mistral API key, and registers `colgate-assistant` from `hand.toml`.

### 4. Load the knowledge base

```bash
python main.py ingest
```

Injects structured data (NIT, phones, offices) into the KV Store and 235 text fragments into the Vector Store.

### 5. Activate autonomous Hands

```bash
python main.py hand
```

Starts `colgate-intelligence-hand` (every 6 hours) and `colgate-service-hand` (Mondays 9 AM).

### 6. Start the WhatsApp gateway

```powershell
cd $env:USERPROFILE\.openfang\whatsapp-gateway
$env:OPENFANG_DEFAULT_AGENT = "<agent-uuid>"
$env:OPENFANG_URL = "http://127.0.0.1:4200"
node index.js
# Scan the QR code with WhatsApp on first run
```

### 7. Verify

```bash
python main.py status
```

---

## Configuration

All secrets are loaded from `.env`. Copy `.env.example` to get started — it contains no real credentials.

| Variable | Required | Description |
|---|---|---|
| `MISTRAL_API_KEY` | Yes | Mistral AI API key |
| `WA_ACCESS_TOKEN` | Yes | WhatsApp Business access token |
| `WA_PHONE_NUMBER_ID` | Yes | WhatsApp Business phone number ID |
| `WA_VERIFY_TOKEN` | Yes | Webhook verification token (any string) |
| `OPENFANG_URL` | No | OpenFang daemon URL (default: `http://127.0.0.1:4200`) |
| `OPENFANG_AGENT_ID` | Yes | Agent UUID — get it with `openfang agent list` |

---

## Autonomous Hands

Hands are background agents defined in `hand.toml` that run on a schedule without human intervention.

| Hand | Type | Schedule | Purpose |
|---|---|---|---|
| `colgate-intelligence-hand` | Collector | Every 6 hours | Competitive intelligence: P&G, Unilever, market trends |
| `colgate-service-hand` | Custom | Mondays 9 AM | Consumer sentiment monitoring on social media |

Intelligence reports are stored in the agent's memory and are available for RAG queries.

---

## Project Structure

```
colgatefinal/
│
├── hand.toml                  # Agent manifest: model, memory, Hands, WhatsApp channel
├── main.py                    # CLI: setup / ingest / hand / status / whatsapp
├── pyproject.toml             # Python dependencies (uv)
├── .env.example               # Environment variables template
│
├── scripts/
│   ├── ingest.py              # Loads KB into OpenFang KV Store and Vector Store
│   └── whatsapp_bridge.py     # WhatsApp channel configuration helper
│
├── webhook_server.py          # Alternative FastAPI webhook (Meta Cloud API)
├── tsne_analysis.py           # t-SNE intent clustering analysis (bonus)
│
├── informe.css                # PDF stylesheet (Inter + JetBrains Mono)
├── INFORME_TECNICO.md         # Technical report
│
└── data/
    ├── knowledge_base_clean.txt   # Clean knowledge base (~235 fragments)
    └── datos_estructurados.json   # Structured data: NIT, phones, offices, brands
```

> The WhatsApp gateway (`index.js`) is not versioned — it contains the active Baileys session, equivalent to the account's login credentials.

---

## t-SNE Intent Analysis (Bonus)

Visualizes user query clusters by detected intent using Mistral Embeddings.

```bash
uv run python tsne_analysis.py
# Output: tsne_conversaciones.png
```

Falls back to 20 representative example sessions when fewer than 5 real sessions exist.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent OS | OpenFang 0.6.9 (Rust kernel, WASM sandbox) |
| WhatsApp bridge | Baileys `@whiskeysockets/baileys` (Node.js) |
| LLM | Mistral AI `mistral-small-latest` |
| Embeddings | Mistral `mistral-embed` (1024 dims) |
| Scripts | Python 3.14 + `uv` |
| Webhook (alt.) | FastAPI + uvicorn |
| Visualization | scikit-learn, matplotlib |

---

## License

Academic project — Universidad Autónoma de Occidente, 2026.
