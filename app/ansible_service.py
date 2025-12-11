import json
import subprocess
import csv
from pathlib import Path

from .db import get_conn, BASE_DIR

# Carpeta data/
DATA_DIR = BASE_DIR / "data"


def parse_show_version(show_version_text: str):
    """
    Extrae modelo, versión de IOS y número de serie de 'show version'
    para IOS clásico (routers C2900 y switches C3750, etc.).
    """
    modelo = ""
    ios_version = ""
    serial = ""

    for line in show_version_text.splitlines():
        line = line.strip()

        # Versión de IOS
        if "Cisco IOS Software" in line and "Version" in line:
            partes = line.split("Version")
            if len(partes) > 1:
                ios_version = partes[1].split(",")[0].strip()

        # Modelo
        if "bytes of memory" in line and ("cisco" in line.lower()):
            tokens = line.split()
            if len(tokens) >= 2:
                modelo = tokens[1]

        # Serial
        if "Processor board ID" in line:
            serial = line.split("Processor board ID")[-1].strip()
        elif "System serial number" in line and ":" in line:
            serial = line.split(":")[-1].strip()

    return modelo, ios_version, serial


import json
import subprocess
import csv
from pathlib import Path

from .db import get_conn, BASE_DIR

# Carpeta data/
DATA_DIR = BASE_DIR / "data"


def parse_show_version(show_version_text: str):
    """
    Extrae modelo, versión de IOS y número de serie de 'show version'
    para IOS clásico (routers C2900 y switches C3750, etc.).
    """
    modelo = ""
    ios_version = ""
    serial = ""

    for line in show_version_text.splitlines():
        line = line.strip()

        # Versión de IOS
        if "Cisco IOS Software" in line and "Version" in line:
            partes = line.split("Version")
            if len(partes) > 1:
                ios_version = partes[1].split(",")[0].strip()

        # Modelo
        if "bytes of memory" in line and ("cisco" in line.lower()):
            tokens = line.split()
            if len(tokens) >= 2:
                modelo = tokens[1]

        # Serial
        if "Processor board ID" in line:
            serial = line.split("Processor board ID")[-1].strip()
        elif "System serial number" in line and ":" in line:
            serial = line.split(":")[-1].strip()

    return modelo, ios_version, serial


def correr_ansible_y_actualizar_db():
    """
    Ejecuta el playbook de Ansible, lee inventario_ansible.json,
    actualiza la tabla devices en red.db y genera inventario_ansible.csv.

    Regresa (ok, msg) para que la UI lo use.
    """
    json_path = DATA_DIR / "inventario_ansible.json"

    # 1) Ejecutar Ansible (NO usamos check=True para no tronarnos por warnings)
    cmd = ["ansible-playbook", "ansible/get_facts.yaml", "-i", "ansible/hosts.ini"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        ansible_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    except Exception as e:
        return False, f"Error al ejecutar Ansible:\n{e}"

    # 2) Leer JSON generado por el playbook
    try:
        with open(json_path, "r") as f:
            datos = json.load(f)
    except FileNotFoundError:
        # Aquí sí consideramos error real: no se generó el inventario
        return False, (
            f"No se encontró el archivo {json_path}.\n\n"
            f"Salida de ansible:\n{ansible_output}"
        )
    except Exception as e:
        return False, f"Error leyendo el inventario JSON:\n{e}"

    # 3) Volcar a la base de datos
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM devices")

        for hostname, info in datos.items():
            ip_principal = info.get("ip_principal", "")
            show_version = info.get("show_version", "")

            modelo, ios_version, serial = parse_show_version(show_version)

            cur.execute(
                "INSERT INTO devices (hostname, ip, modelo, ios_version, serial) "
                "VALUES (?, ?, ?, ?, ?)",
                (hostname, ip_principal, modelo, ios_version, serial),
            )

        conn.commit()
        conn.close()
    except Exception as e:
        return False, f"Error actualizando la base de datos:\n{e}"

    # 4) Generar CSV externo con el inventario
    try:
        conn2 = get_conn()
        cur2 = conn2.cursor()
        cur2.execute("SELECT hostname, ip, modelo, ios_version, serial FROM devices")
        filas = cur2.fetchall()
        conn2.close()

        csv_path = DATA_DIR / "inventario_ansible.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["hostname", "ip", "modelo", "ios_version", "serial"])
            for row in filas:
                writer.writerow(row)
    except Exception as e:
        return False, f"Inventario en DB OK, pero falló el CSV:\n{e}"

    # Si llegamos aquí, aunque Ansible haya tenido warnings o fallas en algún host,
    # la DB y el CSV sí se actualizaron.
    return True, "Inventario actualizado correctamente."
