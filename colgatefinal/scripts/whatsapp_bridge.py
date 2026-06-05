"""
Configuracion y verificacion del canal WhatsApp para OpenFang.
Utiliza 'openfang channel' y 'openfang vault' para gestionar el token.

La variable de entorno requerida por OpenFang es: WA_ACCESS_TOKEN

Uso:
    python scripts/whatsapp_bridge.py setup   -- guardar token y habilitar canal
    python scripts/whatsapp_bridge.py status  -- ver estado del canal
    python scripts/whatsapp_bridge.py test    -- enviar mensaje de prueba
    python scripts/whatsapp_bridge.py stop    -- deshabilitar el canal
"""

import subprocess
import sys
import os
from pathlib import Path

CHANNEL = "whatsapp"
TOKEN_KEY = "WA_ACCESS_TOKEN"


def _load_env() -> None:
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def _run(args: list[str], stdin_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def cmd_setup() -> int:
    _load_env()

    token = os.environ.get(TOKEN_KEY, "").strip()
    if not token:
        print(f"ERROR: Variable {TOKEN_KEY} no encontrada en el archivo .env")
        print()
        print("Para obtener el token de WhatsApp Business (Meta Cloud API):")
        print()
        print("  1. Vaya a https://developers.facebook.com")
        print("  2. Cree una app -> Agregar producto -> WhatsApp")
        print("  3. En 'Comenzar' copie el Access Token temporal")
        print("  4. Cree el archivo .env en la raiz del proyecto con:")
        print(f"       {TOKEN_KEY}=EAAxxxxxxxxxxxxx")
        print()
        print("  Luego ejecute de nuevo: python main.py whatsapp setup")
        return 1

    # Inicializar vault si no existe
    vault_check = _run(["openfang", "vault", "list"])
    if "not initialized" in vault_check.stdout + vault_check.stderr:
        print("Inicializando vault de OpenFang...")
        _run(["openfang", "vault", "init"])
        print("  OK  Vault inicializado.")

    # Guardar token en el vault de OpenFang
    print(f"Guardando {TOKEN_KEY} en el vault de OpenFang...")
    result = _run(["openfang", "vault", "set", TOKEN_KEY], stdin_text=token)
    if result.returncode != 0:
        print(f"  ERROR en vault: {result.stderr.strip()[:120]}")
        return 1
    print(f"  OK  Token guardado en vault.")

    # Habilitar el canal
    print(f"\nHabilitando canal {CHANNEL}...")
    result = _run(["openfang", "channel", "enable", CHANNEL])
    if result.returncode != 0:
        print(f"  ERROR al habilitar canal: {result.stderr.strip()[:120]}")
        return 1
    print(f"  OK  Canal {CHANNEL} habilitado.")

    # Verificar estado
    print()
    result = _run(["openfang", "channel", "list"])
    for line in result.stdout.splitlines():
        if CHANNEL in line.lower():
            print(f"  Estado: {line.strip()}")
            break

    print()
    print("Canal WhatsApp configurado correctamente.")
    print("Siguiente paso: python main.py whatsapp test")
    return 0


def cmd_status() -> int:
    result = _run(["openfang", "channel", "list"])
    print("Estado de canales OpenFang:")
    print("-" * 50)
    print(result.stdout.strip() or result.stderr.strip())
    return result.returncode


def cmd_test() -> int:
    print(f"Enviando mensaje de prueba por {CHANNEL}...")
    result = _run(["openfang", "channel", "test", CHANNEL])
    output = result.stdout.strip() or result.stderr.strip()
    print(output if output else "Sin respuesta del servidor.")
    return result.returncode


def cmd_stop() -> int:
    print(f"Deshabilitando canal {CHANNEL}...")
    result = _run(["openfang", "channel", "disable", CHANNEL])
    if result.returncode == 0:
        print(f"  OK  Canal {CHANNEL} deshabilitado.")
    else:
        print(f"  ERROR: {result.stderr.strip()[:120]}")
    return result.returncode


COMMANDS = {
    "setup": cmd_setup,
    "status": cmd_status,
    "test": cmd_test,
    "stop": cmd_stop,
}


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command not in COMMANDS:
        print(__doc__)
        sys.exit(0)
    sys.exit(COMMANDS[command]())
