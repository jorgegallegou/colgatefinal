"""
Ingesta de conocimiento corporativo de Colgate-Palmolive en OpenFang.

Módulo 2 — Pipeline de datos:
  - KV Store: datos estructurados (NIT, contactos, FAQs) desde datos_estructurados.json
  - Vector Store: base de conocimiento textual desde knowledge_base_clean.txt,
    vectorizada automáticamente por OpenFang con nomic-embed-text (1024 dims).

Uso:
    python scripts/ingest.py
    python main.py ingest
"""

import json
import subprocess
import sys
import time
from pathlib import Path

AGENT = "colgate-assistant"
DATA_PATH = Path("data/datos_estructurados.json")
KB_PATH = Path("data/knowledge_base_clean.txt")

CHUNK_SEPARATOR = "---"
MIN_CHUNK_LENGTH = 80
# Chunks mas grandes para reducir llamadas al modelo de embeddings
CHUNKS_PER_MESSAGE = 5


def _run(args: list[str]) -> subprocess.CompletedProcess:
    """Ejecuta un comando de CLI y captura stdout/stderr en UTF-8."""
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


def ensure_daemon() -> bool:
    result = _run(["openfang", "health"])
    if result.returncode == 0:
        return True
    print("  El daemon no esta corriendo. Iniciando...")
    subprocess.Popen(
        ["openfang", "start"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(4)
    result = _run(["openfang", "health"])
    if result.returncode != 0:
        print("  ERROR: No se pudo iniciar el daemon. Ejecute 'openfang start' manualmente.")
        return False
    print("  OK  Daemon iniciado.")
    return True


def ingest_kv_store() -> None:
    """Inyecta datos estructurados (contactos, FAQs, sedes) en el KV Store del agente."""
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    pares: dict[str, str] = {
        "empresa_nombre": data["informacion_corporativa"]["nombre_legal"],
        "empresa_nit": data["informacion_corporativa"]["nit"],
        "empresa_sede": data["informacion_corporativa"]["sede_principal_colombia"],
        "empresa_fundacion": data["informacion_corporativa"]["fundacion_global"],
        "empresa_fundador": data["informacion_corporativa"]["fundador"],
        "empresa_paises": str(data["informacion_corporativa"]["presencia_paises"]),
        "empresa_sector": data["informacion_corporativa"]["sector"],
        "empresa_web": data["contacto"]["sitio_web"],
        "telefono_gratuito": data["contacto"]["linea_gratuita"],
        "whatsapp": data["contacto"]["whatsapp"],
        "correo": data["contacto"]["correo_consumidor"],
        "horario_telefono": data["horarios_atencion"]["linea_telefonica"],
        "horario_whatsapp": data["horarios_atencion"]["whatsapp"],
        "horario_chat_web": data["horarios_atencion"]["chat_web"],
        "marcas": ", ".join(data["marcas_principales_colombia"]),
        "programa_social": data["programas_sociales"]["programa_sonrisas_brillantes"],
        "sostenibilidad": data["sostenibilidad"]["compromiso_ambiental"],
    }

    for sede in data.get("sedes_colombia", []):
        ciudad_key = (
            sede["ciudad"].lower()
            .replace(" ", "_")
            .replace("á", "a").replace("é", "e")
            .replace("í", "i").replace("ó", "o").replace("ú", "u")
            .replace("ñ", "n")
        )
        pares[f"sede_{ciudad_key}"] = f"{sede['tipo']} - {sede['direccion']}"

    for i, faq in enumerate(data.get("preguntas_frecuentes", []), 1):
        pares[f"faq_{i:02d}"] = f"P: {faq['pregunta']} R: {faq['respuesta']}"

    print(f"Inyectando {len(pares)} pares al KV Store del agente '{AGENT}'...")
    ok = errors = 0
    for clave, valor in pares.items():
        resultado = _run(["openfang", "memory", "set", AGENT, clave, valor])
        if resultado.returncode == 0:
            print(f"  OK  {clave}")
            ok += 1
        else:
            stderr = resultado.stderr.strip()
            lines = stderr.splitlines()
            msg = next((l for l in lines if "error" in l.lower()), stderr[:80])
            print(f"  ERROR  {clave}: {msg}")
            errors += 1

    print(f"\nKV Store: {ok} OK, {errors} errores de {len(pares)} pares.\n")


def ingest_vector_store() -> None:
    """
    OpenFang embeds y almacena en el Vector Store los mensajes que recibe el agente.
    Enviamos la knowledge base en bloques consolidados via 'openfang message'.
    """
    if not KB_PATH.exists():
        print(f"ERROR: No se encontro {KB_PATH}")
        return

    raw_text = KB_PATH.read_text(encoding="utf-8")
    raw_chunks = raw_text.split(CHUNK_SEPARATOR)
    chunks = [c.strip() for c in raw_chunks if len(c.strip()) >= MIN_CHUNK_LENGTH]

    # Agrupar chunks para reducir el numero de llamadas al modelo
    bloques: list[str] = []
    for i in range(0, len(chunks), CHUNKS_PER_MESSAGE):
        grupo = chunks[i: i + CHUNKS_PER_MESSAGE]
        bloque = "\n\n".join(grupo)
        bloques.append(bloque)

    print(f"Inyectando {len(chunks)} fragmentos ({len(bloques)} bloques) al Vector Store...")
    print("(OpenFang embeds cada mensaje automaticamente con nomic-embed-text)")
    print()

    ok = errors = 0
    for i, bloque in enumerate(bloques, 1):
        # Prefijo que indica al agente que almacene este contenido como conocimiento
        mensaje = f"[CONOCIMIENTO CORPORATIVO - BLOQUE {i}/{len(bloques)}]\n{bloque}"
        resultado = _run(["openfang", "message", AGENT, mensaje])
        if resultado.returncode == 0:
            ok += 1
            print(f"  OK  Bloque {i}/{len(bloques)}")
        else:
            errors += 1
            lines = resultado.stderr.splitlines()
            msg = next((l for l in lines if "error" in l.lower()), resultado.stderr[:80])
            print(f"  ERROR bloque {i}: {msg}")

    print(f"\nVector Store: {ok} OK, {errors} errores de {len(bloques)} bloques.\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Ingestion de Conocimiento Corporativo - Colgate-Palmolive")
    print("=" * 60)
    print()

    print("Verificando daemon OpenFang...")
    if not ensure_daemon():
        sys.exit(1)
    print()

    print("Paso 1: KV Store (datos estructurados y FAQs)")
    print("-" * 40)
    ingest_kv_store()

    print("Paso 2: Vector Store (base de conocimiento completa)")
    print("-" * 40)
    ingest_vector_store()

    print("Ingestion completada.")
    print("Verificar estado con: python main.py status")
