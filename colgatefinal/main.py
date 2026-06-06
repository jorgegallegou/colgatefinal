"""
Gestor del Agente Corporativo Colgate-Palmolive - Ruta B (OpenFang Agent OS)

Comandos disponibles:
    python main.py setup      -- verificar entorno (OpenFang + Mistral)
    python main.py ingest     -- inyectar conocimiento corporativo
    python main.py hand       -- activar Hands configurados en hand.toml
    python main.py status     -- ver estado del agente
    python main.py whatsapp   -- configurar bridge WhatsApp
    python main.py dashboard  -- abrir dashboard local (puerto 4200)
"""

import json
import os
import re
import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path

AGENT = "colgate-assistant"
MISTRAL_MODEL = "mistral-small-latest"
DASHBOARD_URL = "http://127.0.0.1:4200"
HANDS = ["colgate-intelligence-hand", "colgate-service-hand"]


def _run(args: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Ejecuta un subproceso y devuelve el resultado con encoding UTF-8."""
    return subprocess.run(args, capture_output=capture, text=True, encoding="utf-8")


def _clean(text: str) -> str:
    """Elimina caracteres no-ASCII para evitar errores en consolas Windows."""
    return text.encode("ascii", errors="ignore").decode("ascii")


def _get_agent_uuid(agent_name: str) -> str:
    """Extrae el UUID del agente desde la salida de 'openfang agent list'."""
    r = _run(["openfang", "agent", "list", "--json"])
    if r.returncode == 0:
        try:
            agents = json.loads(r.stdout)
            if isinstance(agents, list):
                for a in agents:
                    if a.get("name") == agent_name:
                        return a.get("id", "")
        except (json.JSONDecodeError, AttributeError):
            pass
    # Fallback: buscar UUID en la salida de texto plano
    r = _run(["openfang", "agent", "list"])
    uuid_re = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
    for line in r.stdout.splitlines():
        if agent_name in line:
            m = uuid_re.search(line)
            if m:
                return m.group(0)
    return ""


def _load_env() -> None:
    """Carga variables de entorno desde .env sin sobrescribir las ya definidas en el sistema."""
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def cmd_setup(_args=None) -> int:
    """Verifica OpenFang, la API key de Mistral y registra el agente desde hand.toml."""
    print("=" * 55)
    print("Verificacion del Entorno - Ruta B OpenFang Agent OS")
    print("=" * 55)

    # Verificar OpenFang
    print("\n[1/3] OpenFang...")
    result = _run(["openfang", "--version"])
    if result.returncode != 0:
        print("  ERROR: OpenFang no encontrado.")
        print("  Instalar con:")
        print("    curl -fsSL https://openfang.sh/install | sh")
        return 1
    print(f"  OK  {result.stdout.strip()}")

    # Verificar Mistral API Key
    print("\n[2/3] Mistral API...")
    _load_env()
    mistral_key = os.environ.get("MISTRAL_API_KEY", "")
    if not mistral_key:
        print("  ERROR: MISTRAL_API_KEY no encontrada.")
        print("  Agrega la clave en el archivo .env (ver .env.example)")
        return 1
    print(f"  OK  MISTRAL_API_KEY detectada (modelo: {MISTRAL_MODEL})")

    # Verificar agente en OpenFang
    print("\n[3/3] Registro del agente...")
    lista = _run(["openfang", "agent", "list"])
    if AGENT in lista.stdout:
        print(f"  OK  Agente '{AGENT}' ya registrado.")
    else:
        result = _run(["openfang", "agent", "spawn", "hand.toml"])
        if result.returncode == 0 or "already exists" in result.stderr:
            print(f"  OK  Agente '{AGENT}' registrado desde hand.toml.")
        else:
            lines = result.stderr.splitlines()
            error_line = next((l for l in lines if "ERROR" in l or "error" in l.lower()), result.stderr[:120])
            print(f"  AVISO: {error_line}")

    uuid = _get_agent_uuid(AGENT)
    if uuid:
        print(f"  UUID: {uuid}")
        current_env_id = os.environ.get("OPENFANG_AGENT_ID", "")
        if current_env_id != uuid:
            print(f"  ACCION: Actualiza OPENFANG_AGENT_ID={uuid} en tu archivo .env")
    else:
        print("  AVISO: No se pudo extraer el UUID. Verificalo con: openfang agent list")

    print()
    print("Entorno listo.")
    print("Siguiente paso: python main.py ingest")
    return 0


def cmd_ingest(_args=None) -> int:
    """Delega la ingesta de conocimiento a scripts/ingest.py."""
    print("=" * 55)
    print("Ingestion de Conocimiento Corporativo")
    print("=" * 55)

    script = Path("scripts/ingest.py")
    if not script.exists():
        print(f"ERROR: No se encontro {script}")
        return 1

    result = subprocess.run(
        [sys.executable, str(script)],
        encoding="utf-8"
    )
    return result.returncode


def cmd_hand(args) -> int:
    """Activa y configura los Hands autónomos de vigilancia e inteligencia competitiva."""
    # Hand 1: Collector - inteligencia competitiva (Opcion B del taller)
    # Hand 2: Researcher - calidad de servicio al consumidor (Opcion C)
    hands_config = [
        {
            "id": "collector",
            "instance_name": "colgate-intelligence-hand",
            "settings": {
                "target_subject": "Colgate-Palmolive Colombia competidores higiene bucal cuidado personal",
                "collection_depth": "deep",
                "update_frequency": "every_6h",
                "focus_area": "competitor",
                "alert_on_changes": "true",
                "report_format": "markdown",
                "max_sources_per_cycle": "30",
                "track_sentiment": "true",
            },
        },
        {
            "id": "researcher",
            "instance_name": "colgate-service-hand",
            "settings": {
                "research_depth": "deep",
                "output_format": "markdown",
            },
        },
    ]

    filter_name = getattr(args, "name", None)
    if filter_name:
        hands_config = [h for h in hands_config if h["instance_name"] == filter_name]
        if not hands_config:
            print(f"ERROR: Hand '{filter_name}' no encontrado.")
            return 1

    print("Activando Hands del agente...")
    print()

    exitcode = 0
    for hand in hands_config:
        hid = hand["id"]
        name = hand["instance_name"]

        print(f"[{hid}] Activando como '{name}'...")
        result = _run(["openfang", "hand", "activate", hid, "--name", name])
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "already" in stderr.lower():
                print(f"  OK  '{name}' ya estaba activo.")
            else:
                lines = stderr.splitlines()
                msg = next((l for l in lines if "error" in l.lower()), stderr[:120])
                print(f"  ERROR: {msg}")
                exitcode = 1
                continue
        else:
            print(f"  OK  Activado.")

        set_flags = []
        for k, v in hand["settings"].items():
            set_flags += ["--set", f"{k}={v}"]

        if set_flags:
            result = _run(["openfang", "hand", "config", hid] + set_flags)
            if result.returncode == 0:
                print(f"  OK  Configuracion aplicada ({len(hand['settings'])} parametros).")
            else:
                lines = result.stderr.splitlines()
                msg = next((l for l in lines if "error" in l.lower()), result.stderr[:80])
                print(f"  AVISO configuracion: {msg}")
        print()

    if exitcode == 0:
        print(f"Hands activos. Dashboard: {DASHBOARD_URL}")
    return exitcode


def cmd_status(_args=None) -> int:
    """Muestra el estado del daemon, agente, memoria, canal WhatsApp y Hands activos."""
    print("=" * 55)
    print("Estado del Sistema - Colgate-Palmolive Agent OS")
    print("=" * 55)

    print("\n[Daemon]")
    r = _run(["openfang", "health"])
    print(f"  {_clean(r.stdout.strip() or r.stderr.strip())}")

    print(f"\n[Agente: {AGENT}]")
    r = _run(["openfang", "agent", "list"])
    for line in r.stdout.splitlines():
        if AGENT in line:
            print(f"  {_clean(line.strip())}")
            break

    print("\n[Memoria KV Store]")
    r = _run(["openfang", "memory", "list", AGENT])
    try:
        kv_data = json.loads(r.stdout)
        pairs = kv_data.get("kv_pairs", [])
        user_pairs = [p for p in pairs if not p["key"].startswith("__")]
        print(f"  {len(user_pairs)} pares corporativos  |  {len(pairs)} total (incluye internos)")
        for p in user_pairs[:5]:
            val_preview = _clean(str(p["value"])[:50].replace("\n", " "))
            print(f"    {p['key']}: {val_preview}")
        if len(user_pairs) > 5:
            print(f"    ... y {len(user_pairs) - 5} mas")
    except (json.JSONDecodeError, AttributeError):
        lines = [line for line in r.stdout.splitlines() if line.strip()]
        print(f"  {len(lines)} entradas")

    print("\n[Canal WhatsApp]")
    r = _run(["openfang", "vault", "list"])
    vault_has_token = "WA_ACCESS_TOKEN" in r.stdout
    r2 = _run(["openfang", "channel", "list"])
    for line in r2.stdout.splitlines():
        if "whatsapp" in line.lower():
            status = _clean(line.strip())
            if "Missing env" in status and vault_has_token:
                status = status.replace("Missing env", "Ready (token en vault)")
            print(f"  {status}")
            break

    print("\n[Hands Activos]")
    r = _run(["openfang", "hand", "active"])
    hand_lines = [l for l in r.stdout.splitlines() if l.strip() and "INSTANCE" not in l and "---" not in l]
    if hand_lines:
        for line in hand_lines:
            print(f"  {_clean(line.strip())}")
    else:
        print("  Ninguno activo")

    print(f"\nDashboard: {DASHBOARD_URL}")
    return 0


def cmd_whatsapp(args) -> int:
    """Delega la configuración del canal WhatsApp a scripts/whatsapp_bridge.py."""
    script = Path("scripts/whatsapp_bridge.py")
    subcommand = getattr(args, "subcommand", "setup") or "setup"

    result = subprocess.run(
        [sys.executable, str(script), subcommand],
        encoding="utf-8"
    )
    return result.returncode


def cmd_dashboard(_args=None) -> int:
    """Abre el dashboard local de OpenFang en el navegador predeterminado."""
    print(f"Abriendo dashboard en {DASHBOARD_URL}")
    webbrowser.open(DASHBOARD_URL)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos con todos los subcomandos disponibles."""
    parser = argparse.ArgumentParser(
        description="Gestor del Agente Corporativo Colgate-Palmolive (Ruta B - OpenFang)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Flujo de despliegue:
  1. python main.py setup       # Verificar OpenFang y Mistral API
  2. python main.py ingest      # Inyectar base de conocimiento
  3. python main.py whatsapp    # Configurar bridge WhatsApp
  4. python main.py hand        # Activar monitoreo autonomo
  5. python main.py status      # Verificar estado final
        """
    )

    sub = parser.add_subparsers(dest="command", metavar="comando")

    sub.add_parser("setup", help="Verificar e inicializar el entorno (OpenFang + Mistral API)")

    sub.add_parser("ingest", help="Inyectar conocimiento corporativo (KV Store)")

    hand_p = sub.add_parser("hand", help="Activar Hands configurados en hand.toml")
    hand_p.add_argument(
        "--name", metavar="HAND_NAME",
        help="Activar solo este hand (por defecto activa todos)"
    )

    sub.add_parser("status", help="Ver estado del agente en OpenFang")

    wa_p = sub.add_parser("whatsapp", help="Configurar bridge WhatsApp (puerto 3009)")
    wa_p.add_argument(
        "subcommand", nargs="?", default="setup",
        choices=["setup", "status", "test", "stop"],
        help="Subcomando: setup (default), status, stop"
    )

    sub.add_parser("dashboard", help=f"Abrir dashboard local ({DASHBOARD_URL})")

    return parser


HANDLERS = {
    "setup": cmd_setup,
    "ingest": cmd_ingest,
    "hand": cmd_hand,
    "status": cmd_status,
    "whatsapp": cmd_whatsapp,
    "dashboard": cmd_dashboard,
}


def main() -> None:
    """Punto de entrada: parsea el subcomando y despacha al handler correspondiente."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    handler = HANDLERS[args.command]
    sys.exit(handler(args))


if __name__ == "__main__":
    main()
