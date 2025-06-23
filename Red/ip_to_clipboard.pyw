#!/usr/bin/env python3
"""
ip_to_clipboard.py
Obtiene la IP “externa” de la interfaz de salida y la copia al portapapeles.
Funciona en Windows y Linux.  Usa:
  - pyperclip (si está disponible)             ►  pip install pyperclip
  - clip      (Windows, viene por defecto)
  - xclip     (Linux, paquete habitual)
"""

import os
import platform
import socket
import subprocess
import sys
from shutil import which

def get_primary_ip() -> str:
    """
    Devuelve la IP local que el equipo usaría para conectarse a internet.
    No realiza tráfico real; solo consulta la tabla de rutas.
    """
    try:
        # Abrimos un socket UDP “falso” contra un host externo
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        # Caso sin red o sin interfaz: 127.0.0.1 como último recurso
        return "127.0.0.1"

def copy_to_clipboard(text: str) -> None:
    """
    Copia texto al portapapeles de forma multiplataforma.
    Orden de preferencia:
      1) pyperclip
      2) clip (Windows)
      3) xclip (Linux)
    Lanza RuntimeError si no encuentra ningún método.
    """
    # 1) Intentar pyperclip
    try:
        import pyperclip  # import local dentro de la función
        pyperclip.copy(text)
        return
    except ModuleNotFoundError:
        pass  # Continuamos con los métodos nativos
    except Exception as exc:  # pyperclip instalado pero falló
        raise RuntimeError(f"pyperclip no pudo copiar: {exc}") from exc

    system = platform.system().lower()

    # 2) Windows: usar clip
    if "windows" in system and which("clip"):
        subprocess.run("clip", text=True, input=text, check=True)
        return

    # 3) Linux (o WSL ↔ xclip)
    if which("xclip"):
        subprocess.run(["xclip", "-selection", "clipboard"], text=True,
                       input=text, check=True)
        return

    raise RuntimeError("No se encontró ninguna forma de acceder al portapapeles.\n"
                       "Instala pyperclip (`pip install pyperclip`) o bien "
                       "asegúrate de tener 'clip' (Windows) o 'xclip' (Linux).")

def main() -> None:
    ip = get_primary_ip()
    try:
        copy_to_clipboard(ip)
        print(f"IP detectada: {ip}\nCopiada al portapapeles ✅")
    except RuntimeError as err:
        print(f"IP detectada: {ip}\n⚠️  {err}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
