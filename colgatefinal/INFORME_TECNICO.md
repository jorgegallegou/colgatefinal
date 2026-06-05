# Informe Técnico Final — Módulo 3
## Agente Conversacional Corporativo: Colgate-Palmolive Colombia
### Ruta B — Sistema Operativo Agéntico (OpenFang 0.6.9)

**Institución:** Universidad Autónoma de Occidente  
**Asignatura:** Técnicas de Inteligencia Artificial  
**Autor:** Jorge Mario Gallego Uribe  
**Correo:** jorge_mario.gallego@uao.edu.co  
**Fecha:** 5 de junio de 2026  
**Repositorio:** https://github.com/jorgegallegou/colgatefinal

---

## 1. Problema y Solución

**Necesidad identificada:** Colgate-Palmolive Colombia no disponía de un canal digital automatizado para atender consultas de consumidores sobre productos, puntos de venta, políticas ambientales, historia corporativa e información de contacto fuera del horario laboral. El servicio al cliente telefónico (018000520800) opera únicamente de lunes a viernes de 8:00 AM a 6:00 PM.

**Solución implementada:** Un agente conversacional corporativo desplegado en WhatsApp que responde en tiempo real las 24 horas, extrae información de una base de conocimiento vectorial construida con datos reales de la empresa (web scraping del Módulo 1), y ejecuta tareas de inteligencia competitiva de forma autónoma en segundo plano mediante el sistema de "Hands" de OpenFang.

---

## 2. Evolución Arquitectónica: Módulo 2 → Módulo 3

| Dimensión | Módulo 2 (Prototipo) | Módulo 3 (Producción) |
|---|---|---|
| **Interfaz de usuario** | Streamlit (web local) | WhatsApp (canal masivo real) |
| **Orquestación** | LangChain + script Python | OpenFang Agent OS (kernel Rust) |
| **Memoria** | Checkpointer en SQLite local | KV Store + Vector Store nativos de OpenFang |
| **Usuarios simultáneos** | 1 (sesión única) | N (sesiones aisladas por número de teléfono) |
| **Autonomía** | 0% reactivo | Hands autónomos en background (cron 6h / semanal) |
| **Canales** | HTTP local | WhatsApp Web (Baileys bridge, puerto 3009) |
| **Modelo LLM** | OpenAI / Ollama (experimental) | Mistral Small (mistral-small-latest) |
| **Seguridad** | Sin aislamiento | WASM sandbox (cada agente en su propio módulo) |

---

## 3. Arquitectura Ruta B — Justificación de Decisiones Técnicas

### 3.1 Agent OS (OpenFang) vs LangChain tradicional

OpenFang abstrae la orquestación de agentes en un kernel escrito en Rust, ofreciendo ventajas clave para un despliegue de producción:

- **Seguridad en WASM:** Cada agente se ejecuta en un módulo WebAssembly aislado, impidiendo que un agente comprometido afecte al sistema anfitrión o a otros agentes.
- **Gestión de RAM:** El kernel de OpenFang consume ~32 MB en reposo y optimiza la ventana de contexto automáticamente (compresión de historial).
- **Multi-sesión nativa:** El endpoint `POST /api/agents/{id}/sessions` crea sesiones aisladas por usuario, garantizando que el historial de conversación no se filtre entre clientes.
- **Cross-Channel Canonical Sessions:** Un mismo agente puede atender simultáneamente WhatsApp, Telegram u otros canales manteniendo contexto separado por canal y usuario.

### 3.2 Justificación: Mistral API vs Ollama local

El taller recomienda Ollama (modelo local) para garantizar soberanía de datos. Este proyecto optó por **Mistral API** por las siguientes razones técnicas justificadas:

| Criterio | Ollama (local) | Mistral API (elegido) |
|---|---|---|
| **Soberanía de datos** | Total (datos no salen del equipo) | Parcial (Mistral AI es empresa francesa, sujeta a GDPR europeo) |
| **Latencia** | Alta (CPU: 8-15s; GPU disponible: 1-3s) | Baja (< 800ms promedio) |
| **Disponibilidad** | Depende del hardware del desarrollador | 99.9% SLA |
| **Compatibilidad** | API OpenAI-compatible | API nativa + compatible con OpenAI |
| **Migración** | Un cambio de `provider` en `hand.toml` | — |
| **Calidad del modelo** | Llama-3.2 / Gemma (aceptable) | Mistral Small (superior en español) |

**Nota importante:** La arquitectura está diseñada para ser agnóstica al proveedor. Cambiar de Mistral API a Ollama requiere únicamente modificar dos líneas en `hand.toml`:
```toml
[model]
provider = "ollama"
model = "llama3.2"
```
Y configurar Ollama localmente. OpenFang detecta Ollama automáticamente en `localhost:11434`.

---

## 4. HAND.toml — Configuración de Operaciones Autónomas

El manifiesto `hand.toml` define la identidad, memoria, canal y capacidades autónomas del agente:

### 4.1 Hand 1 — Inteligencia Competitiva (Opción B: Collector Hand)

```toml
[[hands]]
name = "colgate-intelligence-hand"
type = "collector"
schedule = "0 */6 * * *"          # Ejecución cada 6 horas
targets = [
    "Colgate-Palmolive Colombia noticias",
    "higiene bucal Colombia mercado tendencias",
    "Procter Gamble Crest Colombia",
    "Unilever Dove Colombia competencia",
    "pasta de dientes Colombia precio consumidor",
    "productos limpieza hogar Colombia lanzamiento"
]
alert_keywords = ["crisis", "recall", "retiro", "demanda", "alerta", "competencia"]
store_to_memory = true
```

**Propósito:** Monitoreo automatizado de menciones de competidores (P&G, Unilever) y alertas de crisis de marca. Los resultados se almacenan en la memoria del agente y están disponibles para responder preguntas sobre el mercado.

### 4.2 Hand 2 — Calidad de Servicio al Consumidor (Opción C: Custom Hand)

```toml
[[hands]]
name = "colgate-service-hand"
type = "custom"
schedule = "0 9 * * 1"             # Ejecución cada lunes a las 9:00 AM
targets = [
    "Colgate Colombia redes sociales opinion",
    "Colgate Colombia comentarios consumidores",
    "Palmolive Colombia resenas productos"
]
alert_keywords = ["queja", "reclamo", "defectuoso", "problema", "mal servicio"]
output_format = "json_report"
report_destination = "memory"
```

**Propósito:** Seguimiento semanal de retroalimentación de consumidores en canales digitales. Genera un reporte JSON que el agente puede utilizar para identificar patrones de insatisfacción.

### 4.3 Activación vía CLI — Evidencia de ejecución

Los Hands se activan con el comando `openfang hand activate <id>`:

```bash
$ openfang hand activate collector --name colgate-intelligence
Hand 'collector' activated
  instance : a5d6fdcf-5212-45f0-bcdb-db94559d1e9d
  name     : colgate-intelligence
  agent    : colgate-intelligence

$ openfang hand activate lead --name colgate-leads
Hand 'lead' activated
  instance : 813038f7-b23a-440e-849d-d8e34ee65a7f
  name     : colgate-leads
  agent    : colgate-leads
```

Estado verificado con `curl http://127.0.0.1:4200/api/agents` (5 de junio de 2026, 22:00):

```
AGENTE                              ESTADO       UUID
------------------------------------------------------------------------
colgate-leads                       Running      c28987f0-2c95-555a-a0d6
colgate-intelligence-hand           Running      2a658329-d5ce-5766-8d49
colgate-service-hand                Running      2dbac136-e137-5eb2-8106
colgate-assistant                   Running      4fe45ca6-d6dc-4ca6-8590
colgate-intelligence                Running      eaacc74d-d002-5b9e-8481
```

Los agentes `colgate-intelligence-hand` y `colgate-service-hand` definidos en `hand.toml` son los que ejecutan el trabajo autónomo programado. Los agentes `colgate-intelligence` y `colgate-leads` son las instancias activadas interactivamente vía CLI para demostración.

---

## 5. Migración del Conocimiento Corporativo

### 5.1 Fuentes de datos (Módulo 1 — Web Scraping)

| Fuente | Tipo | Registros | Fragmentos vectorizados |
|---|---|---|---|
| Sitio oficial Colgate Colombia | HTML + JSON | 47 páginas | ~95 fragmentos |
| Wikipedia (Colgate-Palmolive) | Texto estructurado | 1 artículo | ~45 fragmentos |
| Canal YouTube oficial | Transcripciones | 8 videos | ~95 fragmentos |
| **Total** | | | **~235 fragmentos** |

### 5.2 Proceso de inyección en OpenFang

```python
# KV Store: datos estructurados (NIT, contactos, sedes, marcas)
openfang memory set --agent colgate-assistant nit "890.300.546-6"
openfang memory set --agent colgate-assistant linea_gratuita "018000520800"

# Vector Store: base de conocimiento semántica (RAG)
openfang knowledge inject --agent colgate-assistant --file knowledge_base_clean.txt
```

El agente utiliza `top_k = 3` para recuperar los 3 fragmentos más relevantes en cada consulta.

---

## 6. Canal de Interacción — WhatsApp

### 6.1 Diagrama End-to-End

```
Usuario WhatsApp
       │
       │ (mensaje de texto / voz / emoji)
       ▼
┌──────────────────────┐
│  Meta Servers         │   (WhatsApp Web Protocol)
│  @s.whatsapp.net      │
│  @lid (multi-device)  │
└──────────┬───────────┘
           │ (WebSocket Baileys)
           ▼
┌──────────────────────┐
│  Baileys Gateway      │   Node.js — Puerto 3009
│  index.js             │   C:\Users\JM\.openfang\whatsapp-gateway\
│  - resolveAgentId()   │   Funciones clave:
│  - getOrCreateSession │     ✓ UUID resolution (nombre → UUID)
│  - toWhatsApp()       │     ✓ Sesión aislada por teléfono
│  - sock.sendMessage() │     ✓ Markdown → formato WhatsApp
└──────────┬───────────┘
           │ POST /api/agents/{uuid}/message?session_id={sid}
           ▼
┌──────────────────────┐
│  OpenFang Kernel      │   Rust — Puerto 4200
│  Agent OS 0.6.9       │   Componentes activos:
│  colgate-assistant    │     ✓ KV Store (datos estructurados)
│  UUID: 4fe45ca6...    │     ✓ Vector Store (RAG semántico)
│                       │     ✓ Sesiones por usuario (JSONL)
│  Hands activos:       │     ✓ Collector Hand (cada 6h)
│  - colgate-intelligence│     ✓ Custom Hand (cada lunes)
│  - colgate-service    │
└──────────┬───────────┘
           │ HTTPS (Mistral API)
           ▼
┌──────────────────────┐
│  Mistral AI (Cloud)   │   mistral-small-latest
│  temperature = 0.3    │   ~800ms latencia promedio
└──────────┬───────────┘
           │
           ▼
  Respuesta → Gateway → WhatsApp → Usuario
```

### 6.2 Gestión de multi-usuario (aislamiento de sesiones)

**Problema encontrado en producción:** Un usuario de nombre "Natalia" inició una sesión. El sistema original utilizaba una única sesión global, contaminando las conversaciones subsiguientes (otros usuarios recibían "¡Hola Natalia!").

**Solución implementada:**
1. `POST /api/agents/{id}/sessions` crea una sesión UUID única por número de teléfono
2. El `session_id` se pasa como query param: `?session_id={uuid}`
3. `working_memory = false` evita la inyección de contexto diario entre sesiones
4. El `system_prompt` incluye regla explícita: *"Al iniciar la conversación, saluda SIEMPRE con la frase genérica... NUNCA incluyas un nombre en el saludo inicial"*

---

## 7. Bugs Resueltos en Producción

| Bug | Causa Raíz | Solución |
|---|---|---|
| **Bot no respondía** | OpenFang recibía el nombre del agente en lugar del UUID; `POST /api/agents/colgate-assistant/message` retornaba `{"error":"Invalid agent ID"}` | Función `resolveAgentId()`: `GET /api/agents` para resolver nombre → UUID |
| **Mensajes perdidos** | JID `@lid` (multi-device) se convertía a `@s.whatsapp.net` incorrecto | Usar `remoteJid` directamente sin transformación |
| **Caracteres Markdown** | El LLM generaba `###`, `**negrita**`, `---` que WhatsApp no renderiza | Función `toWhatsApp()`: convierte `**` → `*`, elimina `###`, preserva listas `-` |
| **Contaminación multi-usuario** | Sesión global única + `working_memory` activo inyectaba nombres de usuarios anteriores | Sesiones per-usuario + eliminación del archivo de memoria + instrucción de saludo genérico |

---

## 8. Evidencia de Comportamiento Autónomo — Intelligence Report Real

El agente `colgate-intelligence-hand` ejecutó **2 ciclos autónomos** el 5 de junio de 2026 (18:44 y 19:43), procesando 4 fuentes web en cada ciclo sin intervención humana. A continuación, extracto del Ciclo 2:

---

**Intelligence Report: Colgate-Palmolive | Fecha: 2026-06-05 | Ciclo: 2 | Fuentes: 4**

**Cambios clave detectados:**
- **Liderazgo:** Ram Raghavan designado **Global Chief Marketing Officer** (junio 2026). Responsable de Colgate, Palmolive, Hill's Pet Nutrition, elmex, Suavitel, Fabuloso y EltaMD.
- **Innovación:** Lanzamiento de **Colgate Optic White Pro Series** (marzo 2026) — 5% Hydrogen Peroxide Complex, tecnología ActivShine, MSRP $9.99. Segmento: blanqueamiento premium en casa.
- **Inversores:** Colgate-Palmolive India programa reuniones para junio 2026 con Bank of America India Conference y J.P. Morgan Fireside Chat Series.
- **Sostenibilidad:** Estrategia 2030 confirmada: 100% empaques reciclables (actualmente 96%), 83% energía renovable en operaciones, meta cero emisiones netas para 2040.

**Mapa de entidades detectadas:**

| Entidad | Tipo | Relevancia |
|---|---|---|
| Ram Raghavan | Persona | Global CMO desde junio 2026 |
| Colgate Optic White Pro Series | Producto | Nuevo lanzamiento premium |
| Bank of America / J.P. Morgan | Organización | Inversores institucionales |
| Estrategia 2030 | Iniciativa | Sostenibilidad corporativa |

*Reporte almacenado automáticamente en memoria del agente → disponible para consultas RAG del `colgate-assistant`.*

---

## 9. Resultados y Prueba en Vivo — WhatsApp

El sistema fue probado en producción con 3 usuarios reales simultáneos:
- **Natalia** (contacto de prueba inicial)
- **Daniel Gallego** (segundo teléfono, sesión aislada confirmada)
- **Jhonathan** (usuario UAO, conversación de 18 mensajes documentada)

Capacidades verificadas vía WhatsApp:
- Historia de la empresa (fundación 1806, llegada a Colombia 1943, planta Yumbo)
- NIT: 890.300.546-6
- Línea gratuita: 018000520800
- Productos por categoría (dental care, hogar, personal care, mascotas Hill's)
- Distribuidores por ciudad (Éxito, Carulla, D1, Jumbo en Cali)
- Políticas ambientales (cero emisiones netas 2040, empaques reciclables 2025)

**Conversación documentada (Jhonathan, 5 de junio 2026):**

```
[16:09] Jhonathan: Hola
[16:09] Bot: Hola, soy el asistente virtual de Colgate-Palmolive Colombia.
             ¿En qué puedo ayudarte?
[16:10] Jhonathan: Cual es la historia de la compañia?
[16:10] Bot: Colgate-Palmolive fue fundada en 1806 por William Colgate en
             Nueva York... llegó a Colombia en 1943, estableciéndose en
             Cartagena. Actualmente opera desde Yumbo, Valle del Cauca...
[16:11] Jhonathan: Cuales son sus politicas ambientales?
[16:11] Bot: *Reducción de emisiones:* cero emisiones netas para 2040...
             *Energías renovables:* 83% de operaciones con energía renovable...
[16:11] Jhonathan: Cual es el NIT?
[16:11] Bot: El NIT de Colgate-Palmolive Colombia es *890.300.546-6*.
```

---

## 10. Repositorio y Estructura del Proyecto

```
colgatefinal/
├── hand.toml              # Manifiesto del agente + Hands (Ruta B)
├── .env.example           # Plantilla de variables de entorno (sin credenciales)
├── .gitignore             # Protege .env, __pycache__, etc.
├── webhook_server.py      # FastAPI webhook (Meta Cloud API — alternativa)
├── build_vectorstore.py   # Inyección de KB en Vector Store
├── clean_knowledge_base.py# Limpieza y normalización del KB
├── scraper.py             # Web scraping Colgate Colombia
├── scraper_wikipedia.py   # Scraping Wikipedia
├── scraper_youtube.py     # Scraping YouTube transcripciones
├── data/
│   ├── knowledge_base_clean.txt   # Base de conocimiento limpia
│   ├── datos_estructurados.json   # KV Store: contactos, NIT, sedes
│   └── *.json                     # Datos crudos de scraping
└── config.py              # Configuración centralizada

# Fuera del repo (datos sensibles / runtime):
C:\Users\JM\.openfang\
├── config.toml            # Configuración global OpenFang
├── whatsapp-gateway\
│   └── index.js           # Gateway Baileys con todos los fixes
└── workspaces\colgate-assistant\
    ├── memory\            # Memoria diaria (working_memory)
    └── sessions\          # Sesiones JSONL por usuario
```

**Commits principales:**
1. `4e87913` — Initial commit: agente base + canal WhatsApp
2. `1f03a7f` — Fix multi-user isolation and WhatsApp format
3. `09aa109` — Fix greeting contamination: explicit name-free greeting instruction
4. `db98415` — Add PDF report, t-SNE visualization, and analysis dependencies
5. `a2e5b8d` — Add hands evidence, intelligence reports, README

---

## 11. Conclusiones

- **OpenFang Agent OS** demuestra ser una solución de producción robusta para agentes conversacionales corporativos, superando las limitaciones de los prototipos LangChain/Streamlit en cuanto a multi-usuario, autonomía y canales de mensajería.
- El **sistema de Hands** permite que el agente no sea únicamente reactivo, sino que acumule inteligencia competitiva de forma autónoma sin intervención humana.
- La **gestión de sesiones per-usuario** es fundamental en entornos WhatsApp con múltiples consumidores simultáneos y debe implementarse desde el diseño, no como corrección posterior.
- El uso de **Mistral API** en lugar de Ollama local es una decisión de trade-off entre soberanía de datos (Ollama) y disponibilidad/calidad (Mistral), y la arquitectura permite cambiar de proveedor en minutos sin modificar el código.
