from netmiko import ConnectHandler
from .db import get_conn

# ===========================
# Dispositivos de la red
# ===========================

SWITCHES = [
    {
        "device_type": "cisco_ios",
        "host": "192.168.1.11",   # SW1
        "username": "cisco",
        "password": "cisco99",
        "secret": "cisco99",
        "port": 22,
    },
    {
        "device_type": "cisco_ios",
        "host": "192.168.1.12",   # SW2
        "username": "cisco",
        "password": "cisco99",
        "secret": "cisco99",
        "port": 22,
    },
    {
        "device_type": "cisco_ios",
        "host": "192.168.1.1",    # SW_CORE
        "username": "cisco",
        "password": "cisco99",
        "secret": "cisco99",
        "port": 22,
    },
]

ROUTERS = [
    {
        "device_type": "cisco_ios",
        "host": "192.168.1.254",  # R1
        "username": "cisco",
        "password": "cisco",
        "secret": "cisco",
        "port": 22,
    },
]


# ===========================
# Helpers de MAC
# ===========================

def _hex_solo(texto: str) -> str:
    return "".join(c for c in texto.lower() if c in "0123456789abcdef")


def _mac_canonica_desde_hex(hex12: str) -> str:
    if len(hex12) != 12:
        return hex12.lower()
    return f"{hex12[0:4]}.{hex12[4:8]}.{hex12[8:12]}"


def mac_canonica_desde_token(token: str) -> str | None:
    limpio = _hex_solo(token)
    if len(limpio) != 12:
        return None
    return _mac_canonica_desde_hex(limpio)


def mac_canonica_en_linea(linea: str) -> str | None:
    for token in linea.split():
        mac = mac_canonica_desde_token(token)
        if mac:
            return mac
    return None


def _normalizar_mac_para_busqueda(mac: str) -> str:
    """Devuelve solo los 12 hex en minúsculas, sin separadores."""
    return _hex_solo(mac)


# ===========================
# ARP: IP <-> MAC
# ===========================

def resolver_ip_a_mac(ip_address: str) -> str | None:
    """
    Busca en las tablas ARP la MAC asociada a una IP.
    """
    comandos = [
        f"show ip arp {ip_address}",
        "show ip arp",
        "show arp",
    ]

    dispositivos = [
        {
            "device_type": "cisco_ios",
            "host": "192.168.1.1",  # SW_CORE
            "username": "cisco",
            "password": "cisco99",
            "secret": "cisco99",
            "port": 22,
        },
    ] + ROUTERS

    for dev in dispositivos:
        try:
            conn = ConnectHandler(**dev)
            conn.enable()

            for cmd in comandos:
                output = conn.send_command(cmd)
                for line in output.splitlines():
                    if ip_address in line:
                        mac = mac_canonica_en_linea(line)
                        if mac:
                            conn.disconnect()
                            return mac
            conn.disconnect()
        except Exception:
            continue

    return None


def resolver_mac_a_ip(mac_address: str) -> str | None:
    """
    Busca en las tablas ARP la IP asociada a una MAC.
    """
    objetivo = _normalizar_mac_para_busqueda(mac_address)

    comandos = [
        "show ip arp",
        "show arp",
    ]

    dispositivos = [
        {
            "device_type": "cisco_ios",
            "host": "192.168.1.1",  # SW_CORE
            "username": "cisco",
            "password": "cisco99",
            "secret": "cisco99",
            "port": 22,
        },
    ] + ROUTERS

    for dev in dispositivos:
        try:
            conn = ConnectHandler(**dev)
            conn.enable()

            for cmd in comandos:
                output = conn.send_command(cmd)
                for line in output.splitlines():
                    mac_en_linea = mac_canonica_en_linea(line)
                    if not mac_en_linea:
                        continue
                    if _normalizar_mac_para_busqueda(mac_en_linea) == objetivo:
                        partes = line.split()
                        if len(partes) >= 2:
                            ip = partes[1]
                            conn.disconnect()
                            return ip
            conn.disconnect()
        except Exception:
            continue

    return None


def buscar_vlan_por_arp(ip_address: str):
    """
    Intenta obtener VLAN e interfaz lógica (ej. Vlan10) desde la tabla ARP
    del SW_CORE (192.168.1.1). Regresa (vlan, interface) o (None, None).
    """
    dev = {
        "device_type": "cisco_ios",
        "host": "192.168.1.1",   # SW_CORE
        "username": "cisco",
        "password": "cisco99",
        "secret": "cisco99",
        "port": 22,
    }

    comandos = [
        f"show ip arp {ip_address}",
        "show ip arp",
        "show arp",
    ]

    try:
        conn = ConnectHandler(**dev)
        conn.enable()

        for cmd in comandos:
            output = conn.send_command(cmd)
            for line in output.splitlines():
                if ip_address in line:
                    partes = line.split()
                    if len(partes) < 3:
                        continue
                    interfaz = partes[-1]  # normalmente Vlan10
                    vlan = None
                    digitos = "".join(ch for ch in interfaz if ch.isdigit())
                    if digitos:
                        vlan = digitos
                    conn.disconnect()
                    return vlan, interfaz

        conn.disconnect()
    except Exception:
        pass

    return None, None


# ===========================
# Buscar dispositivo en inventario (DB)
# ===========================
def buscar_dispositivo_en_inventario_por_ip(ip_address: str):
    """
    Si la IP corresponde a un switch/router en la tabla devices, regresa un dict.
    Se compara en Python con strip() para evitar problemas de espacios.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT hostname, ip, modelo, ios_version, serial FROM devices")
    filas = cur.fetchall()
    conn.close()

    ip_busqueda = ip_address.strip()

    for hostname, ip, modelo, ios_version, serial in filas:
        if (ip or "").strip() == ip_busqueda:
            return {
                "ip": ip.strip(),
                "mac": None,
                "switch_ip": ip.strip(),
                "vlan": None,
                "interface": None,
                "raw": f"Dispositivo inventariado: {hostname} ({modelo})",
                "raw_line": f"Inventario: {hostname} {ip} {modelo}",
                "hostname": hostname,
                "modelo": modelo,
                "ios": ios_version,
                "serial": serial,
                "es_dispositivo": True,
            }

    return None

# ===========================
# Búsqueda por MAC
# ===========================

def find_by_mac(mac_address: str, permitir_puertos_altos: bool = False):
    """
    Busca por MAC y regresa lista de resultados con IP, VLAN, interfaz y switch.
    Cada elemento es un dict con:
      ip, mac, switch_ip, vlan, interface, raw, raw_line

    Si permitir_puertos_altos=False:
        descarta puertos 45 en adelante (Fa1/0/45, Fa1/0/46, etc).
    Si permitir_puertos_altos=True:
        NO aplica ese filtro (útil para IPs de R1 / SWs).
    """
    mac_norm = mac_canonica_desde_token(mac_address)
    if not mac_norm:
        return []

    # Intentar resolver IP desde ARP
    ip = resolver_mac_a_ip(mac_norm)

    resultados = []
    objetivo_hex = _normalizar_mac_para_busqueda(mac_norm)

    for sw in SWITCHES:
        try:
            conn = ConnectHandler(**sw)
            conn.enable()

            output = conn.send_command("show mac address-table")
            conn.disconnect()

            for line in output.splitlines():
                mac_line = mac_canonica_en_linea(line)
                if not mac_line:
                    continue
                if _normalizar_mac_para_busqueda(mac_line) != objetivo_hex:
                    continue

                partes = line.split()

                # ---------- VLAN: primer token que sea puro número ----------
                vlan = "?"
                for tok in partes:
                    if tok.isdigit():
                        vlan = tok
                        break

                # ---------- INTERFACE: último token que tenga "/" o sea CPU ---
                interface = "?"
                for tok in reversed(partes):
                    if ("/" in tok) or (tok.upper() == "CPU"):
                        interface = tok
                        break

                # ---- FILTRO DE PUERTOS 45+ (solo si NO se permiten) ----
                if not permitir_puertos_altos:
                    num_str = "".join(ch for ch in interface if ch.isdigit())
                    if num_str:
                        try:
                            num = int(num_str[-2:])  # últimos 2 dígitos como número de puerto
                            if num >= 45:
                                continue
                        except ValueError:
                            pass
                # --------------------------------------------------------

                resultados.append({
                    "ip": ip,
                    "mac": mac_norm,
                    "switch_ip": sw["host"],
                    "vlan": vlan,
                    "interface": interface,
                    "raw": line.strip(),
                    "raw_line": line.strip(),
                    "es_dispositivo": False,
                })

        except Exception as e:
            resultados.append({
                "ip": ip,
                "mac": mac_norm,
                "switch_ip": sw["host"],
                "vlan": None,
                "interface": None,
                "raw": f"ERROR: {e}",
                "raw_line": f"ERROR: {e}",
                "error": str(e),
                "es_dispositivo": False,
            })

    return resultados


# ===========================
# Búsqueda por IP
# ===========================

def find_by_ip(ip_address: str):
    """
    Busca por IP:
      1) Intenta resolver la MAC con ARP.
      2) Si hay MAC, llama a find_by_mac.
         - Si la IP también está en el inventario (R1 / SWs),
           se permiten puertos altos (45+).
         - Si NO está en inventario, se filtran puertos altos.
         - Si aún así no hay resultados, se hace fallback al inventario.
      3) Si no hay MAC, busca directo en inventario.

    Regresa (lista_de_resultados, mac_encontrada)
    """
    ip_busqueda = ip_address.strip()

    # ¿Esta IP está en el inventario (devices)?
    dev = buscar_dispositivo_en_inventario_por_ip(ip_busqueda)

    # 1) Intentamos vía ARP
    mac = resolver_ip_a_mac(ip_busqueda)

    if mac:
        # Si es un dispositivo inventariado (R1, SW_CORE, SW1, SW2),
        # permitimos puertos altos porque normalmente están en 45+.
        permitir_altos = dev is not None

        resultados = find_by_mac(mac, permitir_puertos_altos=permitir_altos)

        if resultados:
            for r in resultados:
                r["ip"] = ip_busqueda
                # Si también está en inventario, marcamos como dispositivo
                # para que el botón de "Cambiar VLAN" quede desactivado.
                if dev is not None:
                    r["es_dispositivo"] = True
            return resultados, mac

        # Si no hubo resultados (por ejemplo, no aparece en la MAC table
        # por algún motivo), pero está en inventario, devolvemos el
        # registro de inventario al menos.

        if dev is not None:
            # Intentamos completar VLAN / interfaz lógica desde ARP del SW_CORE
            vlan_hint, iface_hint = buscar_vlan_por_arp(ip_busqueda)

            dev["mac"] = mac
            dev["vlan"] = vlan_hint
            dev["interface"] = iface_hint

            return [dev], mac


        # MAC existe pero no hay ni MAC table ni inventario
        return [], mac

    # 2) Si no salió en ARP, lo buscamos como dispositivo inventariado
    if dev is not None:
        return [dev], None

    # 3) Nada
    return [], None
