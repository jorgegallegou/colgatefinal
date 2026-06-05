"""
Configuracion y verificacion del puente Telegram para OpenFang.

Uso:
    python scripts/telegram_bridge.py setup   -- configurar el bridge
    python scripts/telegram_bridge.py test    -- enviar mensaje de prueba
    python scripts/telegram_bridge.py status  -- ver estado del bridge
"""

import subprocess
import sys
import os
from pathlib import Path

AGENT = "colgate-assistant"
CHANNEL = "telegram"


def _load_env() -> None:
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


def cmd_setup() -> int:
    _load_env()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("ERROR: Variable TELEGRAM_BOT_TOKEN no encontrada.")
        print()
        print("Para obtener un token:")
        print("  1. Abra Telegram y busque @BotFather")
        print("  2. Envie /newbot y siga las instrucciones")
        print("  3. Copie el token generado")
        print("  4. Agregue TELEGRAM_BOT_TOKEN=<token> al archivo .env")
        return 1

    print(f"Configurando bridge Telegram para el agente '{AGENT}'...")

    resultado = _run([
        "openfang", "bridge", "set", AGENT, CHANNEL,
        "--token", token
    ])

    if resultado.returncode != 0:
        print(f"ERROR al configurar bridge: {resultado.stderr.strip()}")
        return 1

    print("Bridge Telegram configurado correctamente.")
    print()
    print("Para iniciar el agente en Telegram ejecute:")
    print(f"  openfang hand activate {AGENT}")
    print()
    print("El bot estara disponible en Telegram una vez activado.")
    return 0


def cmd_test() -> int:
    _load_env()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN no configurado.")
        return 1

    chat_id = os.environ.get("TELEGRAM_TEST_CHAT_ID", "").strip()
    if not chat_id:
        print("ERROR: TELEGRAM_TEST_CHAT_ID no configurado.")
        print("Agregue su chat ID al archivo .env para realizar pruebas.")
        print("Puede obtenerlo enviando /start a su bot y consultando:")
        print("  https://api.telegram.org/bot<TOKEN>/getUpdates")
        return 1

    print(f"Enviando mensaje de prueba al chat {chat_id}...")

    resultado = _run([
        "openfang", "bridge", "test", AGENT, CHANNEL,
        "--chat-id", chat_id,
        "--message", "Prueba de conexion del asistente Colgate-Palmolive Colombia."
    ])

    if resultado.returncode != 0:
        print(f"ERROR: {resultado.stderr.strip()}")
        return 1

    print("Mensaje de prueba enviado correctamente.")
    return 0


def cmd_status() -> int:
    resultado = _run(["openfang", "bridge", "status", AGENT, CHANNEL])
    output = resultado.stdout.strip() or resultado.stderr.strip()
    print(output if output else "Sin informacion de estado disponible.")
    return resultado.returncode


COMMANDS = {
    "setup": cmd_setup,
    "test": cmd_test,
    "status": cmd_status,
}


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if command not in COMMANDS:
        print(__doc__)
        sys.exit(0)

    sys.exit(COMMANDS[command]())
