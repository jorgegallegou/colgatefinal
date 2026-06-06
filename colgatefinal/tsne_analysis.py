"""
Análisis t-SNE de conversaciones del agente Colgate-Palmolive Colombia
Ruta B - Módulo 3 - Bonus +10%

Extrae sesiones JSONL de OpenFang, vectoriza con embeddings y visualiza
clústeres de intenciones de usuario mediante t-SNE.
"""

import json
import os
import glob
import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
from mistralai.client import Mistral

# ── Configuración ───────────────────────────────────────────────────────────

SESSIONS_DIR = os.path.expanduser(
    r"~\.openfang\workspaces\colgate-assistant\sessions"
)
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
OUTPUT_PLOT = "tsne_conversaciones.png"
MIN_MESSAGES = 2  # sesiones con al menos N mensajes de usuario


# ── 1. Extracción de sesiones ────────────────────────────────────────────────

def load_sessions(sessions_dir: str, min_messages: int = 2):
    """Carga sesiones JSONL y extrae texto de usuario."""
    sessions = []
    jsonl_files = glob.glob(os.path.join(sessions_dir, "*.jsonl"))

    for path in jsonl_files:
        session_id = os.path.splitext(os.path.basename(path))[0]
        user_msgs = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get("role") == "user" and entry.get("content"):
                        content = entry["content"]
                        if isinstance(content, str) and len(content) > 1:
                            user_msgs.append(content)
        except (json.JSONDecodeError, OSError):
            continue

        if len(user_msgs) >= min_messages:
            combined = " | ".join(user_msgs)
            sessions.append({"session_id": session_id, "text": combined, "messages": user_msgs})

    return sessions


# ── 2. Vectorización con Mistral Embeddings ──────────────────────────────────

def get_embeddings(texts: list[str], api_key: str) -> np.ndarray:
    """Genera embeddings usando Mistral embed."""
    client = Mistral(api_key=api_key)
    response = client.embeddings.create(
        model="mistral-embed",
        inputs=texts,
    )
    return np.array([e.embedding for e in response.data])


# ── 3. Clasificación de intenciones (reglas simples) ─────────────────────────

INTENT_RULES = {
    "Productos y marcas": ["producto", "pasta", "jabón", "crema", "dental", "cepillo",
                           "colgate", "palmolive", "hill", "protex", "suavitel"],
    "Puntos de venta": ["donde", "comprar", "conseguir", "supermercado", "éxito",
                        "carulla", "d1", "jumbo", "tienda", "precio"],
    "Atención al cliente": ["teléfono", "contacto", "servicio", "horario", "línea",
                             "whatsapp", "correo", "email", "ayuda"],
    "Historia / Empresa": ["historia", "fundación", "empresa", "fundó", "colombia",
                           "años", "1806", "palmolive", "origen"],
    "Sostenibilidad": ["ambiental", "sostenibilidad", "reciclaje", "carbono",
                       "empaques", "ecológico", "verde", "política"],
    "Empleo / RRHH": ["trabajo", "hoja de vida", "empleo", "vacante", "postular",
                      "recurso humano", "convocatoria"],
    "Saludo / General": ["hola", "buenos", "buenas", "gracias", "ok", "listo",
                         "bien", "todo", "qué tal"],
}


def classify_intent(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for intent, keywords in INTENT_RULES.items():
        scores[intent] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Otros"


# ── 4. Visualización t-SNE ───────────────────────────────────────────────────

INTENT_COLORS = {
    "Productos y marcas":   "#e74c3c",
    "Puntos de venta":      "#3498db",
    "Atención al cliente":  "#2ecc71",
    "Historia / Empresa":   "#9b59b6",
    "Sostenibilidad":       "#1abc9c",
    "Empleo / RRHH":        "#f39c12",
    "Saludo / General":     "#95a5a6",
    "Otros":                "#bdc3c7",
}


def plot_tsne(embeddings: np.ndarray, labels: list[str], output_path: str):
    perplexity = min(30, max(5, len(embeddings) // 3))
    scaler = StandardScaler()
    scaled = scaler.fit_transform(embeddings)

    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        max_iter=1000,
        random_state=42,
        learning_rate="auto",
        init="pca",
    )
    coords = tsne.fit_transform(scaled)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("#ffffff")

    unique_labels = sorted(set(labels))
    for label in unique_labels:
        idx = [i for i, l in enumerate(labels) if l == label]
        color = INTENT_COLORS.get(label, "#bdc3c7")
        ax.scatter(
            coords[idx, 0], coords[idx, 1],
            c=color, label=label, s=120, alpha=0.85, edgecolors="white", linewidths=0.8,
        )

    ax.set_title(
        "Análisis t-SNE — Intenciones de Usuarios\nAgente Colgate-Palmolive Colombia (WhatsApp)",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.set_xlabel("Dimensión t-SNE 1", fontsize=11)
    ax.set_ylabel("Dimensión t-SNE 2", fontsize=11)
    ax.legend(
        loc="upper right", fontsize=9, framealpha=0.9,
        title="Intención detectada", title_fontsize=10,
    )
    ax.grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Grafico guardado en: {output_path}")
    plt.close()


# ── 5. Reporte de clústeres ──────────────────────────────────────────────────

def cluster_report(sessions: list[dict], labels: list[str]):
    import sys
    from collections import Counter
    # Force UTF-8 output
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    counts = Counter(labels)
    total = len(labels)
    print("\n" + "="*55)
    print("REPORTE DE INTENCIONES - COLGATE-PALMOLIVE COLOMBIA")
    print("="*55)
    print(f"Total de sesiones analizadas: {total}")
    print()
    for intent, count in counts.most_common():
        pct = (count / total) * 100
        bar = "#" * int(pct / 3)
        print(f"  {intent:<30} {bar:<20} {count:3} ({pct:.1f}%)")
    print()

    print("ANÁLISIS DE CLÚSTERES:")
    dominante = counts.most_common(1)[0][0]
    print(f"  • El clúster dominante es '{dominante}': ", end="")
    if dominante == "Productos y marcas":
        print("los consumidores buscan principalmente información sobre el portafolio.")
    elif dominante == "Saludo / General":
        print("la mayoría de interacciones son saludos iniciales — el agente\n"
              "    responde correctamente redirigiendo hacia consultas corporativas.")
    elif dominante == "Atención al cliente":
        print("usuarios escalan al canal humano con frecuencia.")
    else:
        print("revisar manualmente las sesiones para interpretar el patrón.")
    if counts.get("Puntos de venta", 0) > 0:
        print("  • Clúster 'Puntos de venta' visible: necesidad de un localizador")
        print("    de tiendas integrado en el agente.")
    if counts.get("Atención al cliente", 0) > 0:
        print("  • Clúster 'Atención al cliente': usuarios escalan al canal humano.")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not MISTRAL_API_KEY:
        raise EnvironmentError("MISTRAL_API_KEY no configurado. Ejecutar: set MISTRAL_API_KEY=<key>")

    print(f"Cargando sesiones desde: {SESSIONS_DIR}")
    sessions = load_sessions(SESSIONS_DIR, min_messages=MIN_MESSAGES)
    print(f"Sesiones válidas encontradas: {len(sessions)}")

    if len(sessions) < 5:
        print(
            "ADVERTENCIA: menos de 5 sesiones. "
            "El análisis t-SNE es más informativo con 20+ sesiones.\n"
            "Se usarán datos de ejemplo para demostración."
        )
        # Datos de ejemplo representativos (para demostración sin sesiones suficientes)
        sessions = [
            {"text": "hola buenos dias necesito información sobre los productos de colgate", "messages": []},
            {"text": "donde puedo comprar pasta colgate en cali supermercados", "messages": []},
            {"text": "cual es el telefono de atencion al cliente de colgate colombia", "messages": []},
            {"text": "historia de colgate palmolive cuándo llegó a colombia", "messages": []},
            {"text": "politicas ambientales sostenibilidad colgate reciclaje empaques", "messages": []},
            {"text": "quiero enviar mi hoja de vida empleo colgate palmolive", "messages": []},
            {"text": "precio crema dental colgate blancorepair donde conseguir", "messages": []},
            {"text": "jabón palmolive aloe vera cuanto cuesta punto de venta", "messages": []},
            {"text": "productos hill science diet mascotas colombia", "messages": []},
            {"text": "horario atención servicio al cliente linea gratuita 018000", "messages": []},
            {"text": "colgate total protección completa ingredientes fluoruro", "messages": []},
            {"text": "qué es suavitel producto hogar categorías", "messages": []},
            {"text": "emisiones carbono cero netas 2040 meta sostenibilidad", "messages": []},
            {"text": "NIT empresa colgate palmolive colombia razón social", "messages": []},
            {"text": "planta producción yumbo valle del cauca colgate", "messages": []},
            {"text": "hola buenas como están gracias por la información", "messages": []},
            {"text": "programa becas responsabilidad social colgate fundación", "messages": []},
            {"text": "protex desodorante men women colombia donde venden", "messages": []},
            {"text": "ajax limpiador multiusos hogar precios presentaciones", "messages": []},
            {"text": "quiero trabajar en colgate convocatoria recursos humanos", "messages": []},
        ]

    texts = [s["text"] for s in sessions]
    labels = [classify_intent(t) for t in texts]

    print("Generando embeddings con Mistral...")
    embeddings = get_embeddings(texts, MISTRAL_API_KEY)

    cluster_report(sessions, labels)

    print("Ejecutando t-SNE...")
    plot_tsne(embeddings, labels, OUTPUT_PLOT)
    os.startfile(OUTPUT_PLOT)


if __name__ == "__main__":
    main()