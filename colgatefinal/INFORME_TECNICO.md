# Informe Técnico Final — Módulo 3
## Agente Conversacional Corporativo: Colgate-Palmolive Colombia
### Ruta B — Sistema Operativo Agéntico (OpenFang 0.6.9)

| | |
|---|---|
| **Institución** | Universidad Autónoma de Occidente |
| **Asignatura** | Técnicas de Inteligencia Artificial |
| **Autor** | Jorge Mario Gallego Uribe |
| **Correo** | jorge_mario.gallego@uao.edu.co |
| **Fecha** | 5 de junio de 2026 |
| **Repositorio** | https://github.com/jorgegallegou/colgatefinal |

---

## 1. Introducción

Este informe documenta el desarrollo de un agente de inteligencia artificial conversacional para Colgate-Palmolive Colombia, implementado como parte del Módulo 3 del curso de Técnicas de Inteligencia Artificial.

El proyecto sigue la **Ruta B: Sistema Operativo Agéntico**, que exige desplegar el agente sobre OpenFang 0.6.9, un kernel especializado para agentes de IA. El resultado es un bot de WhatsApp que atiende consultas de consumidores las 24 horas, con conocimiento real de la empresa, y que además realiza vigilancia competitiva de forma autónoma sin que nadie lo tenga que activar manualmente.

---

## 2. Problema Identificado y Solución Implementada

### El problema

Colgate-Palmolive Colombia atiende consultas de consumidores a través de su línea gratuita **018000520800**, pero ese canal opera únicamente de lunes a viernes de 8:00 AM a 6:00 PM. Fuera de ese horario no hay ningún canal digital automatizado disponible.

Los consumidores necesitan respuestas sobre:
- Dónde comprar productos en su ciudad
- Información nutricional o de composición de productos
- Historia y políticas de la empresa
- Datos de contacto y ubicación de sedes

### La solución

Se construyó un agente conversacional accesible por **WhatsApp** que:

1. Responde en cualquier momento del día, sin intervención humana.
2. Conoce la empresa porque fue entrenado con información real extraída del sitio web oficial, Wikipedia y el canal de YouTube de Colgate Colombia.
3. Distingue entre usuarios: cada persona tiene su propia conversación, sin que se mezclen los datos de unos y otros.
4. Busca noticias sobre la competencia cada 6 horas de forma autónoma.

---

## 3. Evolución desde el Módulo 2

El Módulo 2 produjo un prototipo funcional pero con limitaciones de producción. El Módulo 3 resuelve esas limitaciones:

| Dimensión | Módulo 2 (Prototipo) | Módulo 3 (Producción) |
|---|---|---|
| Interfaz de usuario | Streamlit (web local) | WhatsApp (canal masivo real) |
| Orquestación del agente | LangChain + script Python | OpenFang Agent OS (kernel Rust) |
| Memoria | SQLite local | KV Store + Vector Store nativos |
| Usuarios simultáneos | 1 (sesión única) | Ilimitados (sesión por teléfono) |
| Autonomía | 0 % — solo reactivo | Hands autónomos en background |
| Canal de mensajería | HTTP local (localhost) | WhatsApp Web (Baileys, puerto 3009) |
| Modelo LLM | OpenAI / Ollama (experimental) | Mistral Small (mistral-small-latest) |
| Aislamiento de seguridad | Sin aislamiento | WASM sandbox por agente |

La diferencia más importante es la **autonomía**: en el Módulo 2 el agente solo respondía cuando alguien le escribía. En el Módulo 3 el agente también trabaja en segundo plano, recolectando información del mercado sin que nadie lo ordene.

---

## 4. Arquitectura del Sistema

### 4.1 Componentes

El sistema tiene tres capas principales:

```
Usuario WhatsApp
      │
      │  (protocolo WhatsApp Web — WebSocket)
      ▼
┌─────────────────────────────────────────┐
│  GATEWAY BAILEYS                        │
│  Node.js — Puerto 3009                  │
│  Archivo: index.js                      │
│                                         │
│  Responsabilidades:                     │
│  • Recibir mensajes de WhatsApp         │
│  • Crear sesión única por teléfono      │
│  • Convertir Markdown a formato WA      │
│  • Enviar respuesta de vuelta           │
└──────────────────┬──────────────────────┘
                   │
                   │  POST /api/agents/{uuid}/message?session_id={sid}
                   ▼
┌─────────────────────────────────────────┐
│  OPENFANG KERNEL                        │
│  Rust — Puerto 4200                     │
│  Agent OS 0.6.9                         │
│                                         │
│  Agente activo: colgate-assistant       │
│  UUID: 4fe45ca6-d6dc-4ca6-8590-...     │
│                                         │
│  Memoria del agente:                    │
│  • KV Store: NIT, teléfonos, sedes      │
│  • Vector Store: 235 fragmentos RAG     │
│  • Sesiones JSONL: una por usuario      │
│                                         │
│  Hands (agentes autónomos):             │
│  • colgate-intelligence-hand (6h)       │
│  • colgate-service-hand (lunes 9 AM)    │
└──────────────────┬──────────────────────┘
                   │
                   │  HTTPS
                   ▼
┌─────────────────────────────────────────┐
│  MISTRAL AI (nube)                      │
│  Modelo: mistral-small-latest           │
│  Temperatura: 0.3                       │
│  Latencia promedio: < 800 ms            │
└─────────────────────────────────────────┘
```

### 4.2 Flujo de una conversación

1. El usuario escribe por WhatsApp.
2. El **Gateway Baileys** recibe el mensaje y consulta si ya existe una sesión para ese número de teléfono. Si no existe, la crea.
3. El Gateway envía el mensaje a **OpenFang** incluyendo el ID de sesión del usuario.
4. OpenFang busca en el **Vector Store** los 3 fragmentos de conocimiento más relevantes (RAG).
5. Construye el prompt: contexto corporativo + historial de conversación + pregunta actual.
6. Envía el prompt a **Mistral**, recibe la respuesta.
7. OpenFang devuelve la respuesta al Gateway.
8. El Gateway limpia el formato Markdown y envía el texto al usuario por WhatsApp.

---

## 5. Por qué Mistral y no Ollama

El taller sugiere usar Ollama (modelo local) para mantener los datos dentro de la organización. Este proyecto usó **Mistral API** (servicio en la nube) por razones técnicas concretas:

| Criterio | Ollama (local) | Mistral API |
|---|---|---|
| Soberanía de datos | Total — datos no salen del equipo | Parcial — Mistral es empresa francesa, sujeta a GDPR |
| Tiempo de respuesta | 8–15 s en CPU; 1–3 s con GPU | < 800 ms siempre |
| Disponibilidad | Depende del equipo del desarrollador | 99.9 % de uptime garantizado |
| Calidad en español | Aceptable (Llama 3.2 / Gemma) | Superior (Mistral Small entrenado en europeo) |

La decisión de usar Mistral no es definitiva. La arquitectura está preparada para cambiar de proveedor con **dos líneas** en `hand.toml`:

```toml
[model]
provider = "ollama"
model    = "llama3.2"
```

OpenFang detecta Ollama automáticamente en `localhost:11434`. No hay que tocar ningún otro archivo.

---

## 6. Por qué OpenFang y no LangChain

LangChain es una librería de Python. OpenFang es un sistema operativo para agentes. La diferencia es equivalente a la diferencia entre un script y un servidor.

| Capacidad | LangChain | OpenFang |
|---|---|---|
| Multi-sesión | Manual (programar por cuenta propia) | Nativo (`POST /sessions`) |
| Aislamiento de seguridad | Sin aislamiento | WASM — cada agente en su propio módulo |
| Canales de mensajería | Integrar librerías externas | Nativo (WhatsApp, Telegram, HTTP) |
| Agentes en background | No existe | Sistema de Hands (cron nativo) |
| Consumo de RAM | Variable | ~32 MB en reposo (kernel Rust) |

En producción, LangChain hubiera requerido construir la lógica de sesiones, el canal WhatsApp y los jobs automáticos desde cero. OpenFang los provee nativamente.

---

## 7. Conocimiento Corporativo — Cómo se Construyó la Base de Datos

### 7.1 Fuentes de datos

La información que el agente conoce proviene del **Módulo 1 de Web Scraping**:

| Fuente | Contenido | Fragmentos |
|---|---|---|
| Sitio oficial Colgate Colombia | Productos, historia, sedes, contacto | ~95 |
| Wikipedia (Colgate-Palmolive) | Historia global, cifras, subsidiarias | ~45 |
| Canal YouTube oficial | Transcripciones de 8 videos corporativos | ~95 |
| **Total** | | **~235 fragmentos** |

### 7.2 Dos tipos de memoria

El agente usa **dos tipos de almacenamiento** según el tipo de información:

**KV Store** — para datos exactos que no cambian:
```
NIT:              890.300.546-6
Línea gratuita:   018000520800
Sede principal:   Cra 7 # 71-52, Torre B, Bogotá
Fundación:        1806 (Nueva York) / 1943 (Colombia)
```

**Vector Store** — para conocimiento semántico (permite búsqueda por significado):
Los 235 fragmentos de texto se convierten en vectores numéricos con Mistral Embeddings. Cuando el usuario hace una pregunta, el sistema busca los 3 fragmentos más parecidos semánticamente y los incluye en el prompt del LLM.

---

## 8. Hands — Agentes Autónomos

Los Hands son procesos que se ejecutan solos, según un calendario programado, sin que nadie los active. Se definen en `hand.toml`.

### 8.1 Hand 1 — Inteligencia Competitiva (Opción B)

```toml
[[hands]]
name     = "colgate-intelligence-hand"
type     = "collector"
schedule = "0 */6 * * *"   # cada 6 horas
```

Cada 6 horas este agente busca en la web noticias sobre:
- Colgate-Palmolive Colombia
- Competidores: P&G (Crest), Unilever (Dove)
- Tendencias del mercado de higiene en Colombia

Si detecta palabras como `crisis`, `recall`, `demanda` o `retiro`, genera una alerta. Los resultados se guardan en la memoria del agente principal y quedan disponibles para responder preguntas sobre el mercado.

### 8.2 Hand 2 — Calidad de Servicio (Opción C)

```toml
[[hands]]
name     = "colgate-service-hand"
type     = "custom"
schedule = "0 9 * * 1"     # cada lunes a las 9:00 AM
```

Cada lunes revisa opiniones de consumidores en redes sobre Colgate Colombia. Genera un reporte JSON con patrones de quejas y los almacena en memoria.

### 8.3 Activación por CLI — Evidencia

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

Estado del sistema verificado el 5 de junio de 2026 a las 22:00:

```
AGENTE                    ESTADO     UUID
--------------------------------------------------------
colgate-assistant         Running    4fe45ca6-d6dc-...
colgate-intelligence-hand Running    2a658329-d5ce-...
colgate-service-hand      Running    2dbac136-e137-...
colgate-intelligence      Running    eaacc74d-d002-...
colgate-leads             Running    c28987f0-2c95-...
```

---

## 9. Reporte de Inteligencia Generado de Forma Autónoma

El agente `colgate-intelligence-hand` ejecutó **2 ciclos autónomos** el 5 de junio de 2026 (18:44 y 19:43), buscando en 4 fuentes web por ciclo. El siguiente es un extracto del Ciclo 2:

---

**Intelligence Report | 2026-06-05 | Ciclo 2 | Fuentes procesadas: 4**

**Hallazgos principales:**

- **Nuevo CMO Global:** Ram Raghavan fue designado Chief Marketing Officer global de Colgate-Palmolive en junio de 2026. Supervisa las marcas Colgate, Palmolive, Hill's Pet Nutrition, elmex, Suavitel y Fabuloso.

- **Nuevo producto:** Colgate Optic White Pro Series lanzado en marzo de 2026. Contiene 5 % de complejo de peróxido de hidrógeno y tecnología ActivShine. Precio sugerido: USD 9.99. Compite en el segmento de blanqueamiento premium en casa.

- **Sostenibilidad:** La estrategia 2030 confirma: 96 % de empaques reciclables (meta 100 %), 83 % de operaciones con energía renovable, cero emisiones netas para 2040.

- **Inversores:** Colgate-Palmolive India programó reuniones en junio 2026 con Bank of America y J.P. Morgan.

| Entidad | Tipo | Relevancia |
|---|---|---|
| Ram Raghavan | Persona | Global CMO desde junio 2026 |
| Optic White Pro Series | Producto | Nuevo lanzamiento premium |
| Estrategia 2030 | Iniciativa | Sostenibilidad corporativa |

*Este reporte fue generado y almacenado automáticamente. El agente `colgate-assistant` puede responder preguntas sobre él en tiempo real.*

---

## 10. Pruebas en Producción — WhatsApp

El sistema fue probado con **3 usuarios reales simultáneos** desde diferentes teléfonos: Natalia, Daniel Gallego y Jhonathan (usuario UAO).

### Conversación documentada (Jhonathan, 5 de junio de 2026)

```
[16:09] Jhonathan → Hola
[16:09]    Bot   → Hola, soy el asistente virtual de Colgate-Palmolive Colombia.
                   ¿En qué puedo ayudarte?

[16:10] Jhonathan → Cual es la historia de la compañia?
[16:10]    Bot   → Colgate-Palmolive fue fundada en 1806 por William Colgate en
                   Nueva York. Llegó a Colombia en 1943, estableciéndose en
                   Cartagena. Hoy opera desde Yumbo, Valle del Cauca...

[16:11] Jhonathan → Cuales son sus politicas ambientales?
[16:11]    Bot   → *Reducción de emisiones:* cero emisiones netas para 2040.
                   *Energías renovables:* 83 % de operaciones actuales.
                   *Empaques:* 96 % reciclables, meta 100 % en 2025.

[16:11] Jhonathan → Cual es el NIT?
[16:11]    Bot   → El NIT de Colgate-Palmolive Colombia es *890.300.546-6*.
```

### Capacidades verificadas

- Historia corporativa (fundación 1806, llegada a Colombia 1943, planta Yumbo)
- Datos exactos: NIT, línea gratuita, sedes
- Portafolio de productos por categoría (dental, hogar, personal care, mascotas)
- Distribuidores por ciudad (Éxito, Carulla, D1, Jumbo en Cali)
- Políticas ambientales y sostenibilidad

---

## 11. Problemas Encontrados y Cómo se Resolvieron

| Problema | Causa | Solución |
|---|---|---|
| Bot no respondía | El gateway enviaba el nombre del agente (`colgate-assistant`) donde la API espera un UUID | Función `resolveAgentId()`: hace `GET /api/agents` para traducir nombre → UUID antes de cada consulta |
| Mensajes perdidos | El JID multi-device (`@lid`) se convertía erróneamente a `@s.whatsapp.net` | Se usa el `remoteJid` original sin ninguna transformación |
| Texto con símbolos extraños | El LLM devolvía `###`, `**negrita**`, `---` que WhatsApp no interpreta | Función `toWhatsApp()`: convierte `**` → `*`, elimina `###`, preserva listas con `-` |
| Un usuario recibía el nombre de otro | Sesión global única + memoria diaria activa inyectaba nombres de conversaciones anteriores | Sesión independiente por teléfono + instrucción explícita en el prompt de no usar nombres del contexto |

### Detalle del bug de contaminación de usuarios

Este fue el problema más crítico. El flujo del error era:

1. Natalia escribe por primera vez → el agente aprende su nombre.
2. OpenFang guarda ese dato en un archivo de memoria diaria.
3. Jhonathan escribe más tarde → OpenFang inyecta la memoria del día en la nueva conversación.
4. El agente saluda: *"¡Hola Natalia!"* aunque Jhonathan nunca se presentó.

La solución tiene tres partes:
- **Sesiones aisladas:** cada número de teléfono tiene su propio contexto JSONL.
- **Archivo de memoria limpio:** se eliminó el archivo `2026-06-05.md` que contenía el nombre de Natalia.
- **Instrucción en el prompt:** *"IGNORA cualquier nombre del contexto de memoria diaria. NUNCA incluyas un nombre en el saludo inicial."*

---

## 12. Análisis t-SNE de Intenciones (Bonus +10 %)

Se implementó un análisis de clustering para identificar los tipos de preguntas que hacen los usuarios al agente.

**Proceso:**
1. Se extraen los mensajes de usuario de cada sesión JSONL.
2. Se generan embeddings con `mistral-embed` (vectores de 1024 dimensiones).
3. Se reduce la dimensionalidad de 1024 a 2 dimensiones con t-SNE.
4. Se visualiza el resultado con colores por intención detectada.

**Categorías de intención clasificadas:**

| Categoría | Descripción |
|---|---|
| Productos y marcas | Consultas sobre el portafolio (pasta, jabón, crema) |
| Puntos de venta | Dónde comprar, precios, distribuidores |
| Atención al cliente | Teléfonos, horarios, formas de contacto |
| Historia / Empresa | Fundación, Colombia, cifras corporativas |
| Sostenibilidad | Políticas ambientales, reciclaje, emisiones |
| Empleo / RRHH | Vacantes, hojas de vida, convocatorias |
| Saludo / General | Apertura de conversación |

El script se ejecuta con:
```bash
uv run python tsne_analysis.py
# Genera: tsne_conversaciones.png
```

Si hay menos de 5 sesiones reales usa datos de ejemplo representativos para demostración.

---

## 13. Estructura del Repositorio

```
colgatefinal/
│
├── hand.toml                  # Manifiesto del agente: modelo, memoria, Hands y canal WA
├── main.py                    # CLI gestor: setup / ingest / hand / status / whatsapp
├── pyproject.toml             # Dependencias Python (uv)
├── .env.example               # Plantilla de variables de entorno (sin credenciales)
├── .gitignore
│
├── scripts/
│   ├── ingest.py              # Inyección de KB en KV Store y Vector Store de OpenFang
│   └── whatsapp_bridge.py     # Helper de configuración del canal WhatsApp
│
├── webhook_server.py          # FastAPI webhook alternativo (Meta Cloud API)
├── tsne_analysis.py           # Análisis t-SNE de intenciones de usuario (bonus +10 %)
│
├── informe.css                # Estilos para generación del PDF (tipografía Inter)
├── INFORME_TECNICO.md         # Informe técnico completo
│
└── data/
    ├── knowledge_base_clean.txt   # Base de conocimiento (~235 fragmentos)
    └── datos_estructurados.json   # Datos exactos: NIT, teléfonos, sedes, marcas
```

El PDF se genera con:
```bash
pandoc INFORME_TECNICO.md -o INFORME_TECNICO.html --standalone --css=informe.css
chrome --headless --print-to-pdf=INFORME_TECNICO.pdf --no-margins INFORME_TECNICO.html
```

> El gateway de WhatsApp (`index.js`) no está en el repositorio porque contiene la sesión activa de Baileys (equivalente a un cookie de sesión de WhatsApp). Se almacena localmente en `C:\Users\JM\.openfang\whatsapp-gateway\`.

---

## 14. Conclusiones

**Sobre la arquitectura:** OpenFang Agent OS demostró ser adecuado para un despliegue de producción real. Las funcionalidades de sesiones aisladas, canal WhatsApp nativo y Hands autónomos habrían requerido semanas de desarrollo adicional con LangChain.

**Sobre la autonomía:** El sistema de Hands transforma al agente de herramienta reactiva a sistema proactivo. El reporte de inteligencia competitiva generado automáticamente el 5 de junio de 2026 (CMO Ram Raghavan, Optic White Pro Series) es evidencia concreta de este comportamiento.

**Sobre el aislamiento de usuarios:** La contaminación entre sesiones fue el problema de producción más importante. Su solución confirmó que en sistemas multiusuario el aislamiento de contexto debe ser parte del diseño desde el principio, no un parche posterior.

**Sobre el proveedor de LLM:** La decisión de usar Mistral en lugar de Ollama fue un trade-off entre soberanía de datos (Ollama local) y disponibilidad con calidad en español (Mistral). La arquitectura permite cambiar de proveedor en minutos si los requerimientos cambian.
