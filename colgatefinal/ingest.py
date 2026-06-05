"""
Inyeccion del conocimiento corporativo de Colgate-Palmolive Colombia
al KV Store del agente en OpenFang.

Uso: python ingest.py
"""

import json
import subprocess
import sys
from pathlib import Path

AGENT    = "colgate-assistant"
DATA_DIR = Path(__file__).parent / "data"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


def _set_memory(key: str, value: str) -> bool:
    result = _run(["openfang", "memory", "set", AGENT, key, value])
    if result.returncode == 0:
        print(f"  OK  {key}")
        return True
    else:
        lines = result.stderr.splitlines()
        msg = next((l for l in lines if "error" in l.lower()), result.stderr[:80])
        print(f"  SKIP {key}: {msg}")
        return False


def ingest_structured() -> int:
    print("\n[1/2] Inyectando datos estructurados (KV Store)...")
    path = DATA_DIR / "datos_estructurados.json"
    if not path.exists():
        print(f"  ERROR: {path} no encontrado")
        return 0

    data = json.loads(path.read_text(encoding="utf-8"))
    count = 0

    for section, content in data.items():
        key = f"colgate_{section}"
        value = json.dumps(content, ensure_ascii=False)
        if _set_memory(key, value):
            count += 1

    print(f"  Total: {count} entradas KV inyectadas")
    return count


def ingest_knowledge_base() -> int:
    print("\n[2/2] Inyectando base de conocimiento por bloques (KV Store)...")
    path = DATA_DIR / "knowledge_base_clean.txt"
    if not path.exists():
        print(f"  ERROR: {path} no encontrado")
        return 0

    text = path.read_text(encoding="utf-8")
    chunks = [c.strip() for c in text.split("---") if c.strip()]

    # Agrupar en bloques de ~2000 chars para no exceder limites del KV store
    block_size = 2000
    current_block = []
    current_len = 0
    blocks = []

    for chunk in chunks:
        if current_len + len(chunk) > block_size and current_block:
            blocks.append("\n---\n".join(current_block))
            current_block = [chunk]
            current_len = len(chunk)
        else:
            current_block.append(chunk)
            current_len += len(chunk)

    if current_block:
        blocks.append("\n---\n".join(current_block))

    count = 0
    for i, block in enumerate(blocks):
        key = f"colgate_kb_bloque_{i+1:03d}"
        if _set_memory(key, block):
            count += 1

    print(f"  Total: {count} bloques de conocimiento inyectados ({len(chunks)} fragmentos)")
    return count


def main() -> int:
    print("=" * 55)
    print("Ingestion Corporativa - Colgate-Palmolive Colombia")
    print("=" * 55)

    # Verificar daemon activo
    r = _run(["openfang", "health"])
    if r.returncode != 0:
        print("ERROR: Daemon no activo. Ejecute: openfang start")
        return 1
    print(f"Daemon: {r.stdout.strip().encode('ascii', errors='replace').decode('ascii')}")

    total = 0
    total += ingest_structured()
    total += ingest_knowledge_base()

    print("\n" + "=" * 55)
    print(f"Ingestion completada: {total} entradas en memoria")
    print("Verificar con: python main.py status")
    return 0


if __name__ == "__main__":
    sys.exit(main())
