from netmiko import ConnectHandler

def cambiar_vlan(switch_ip: str, interfaz: str, vlan_nueva: str) -> str:
    """
    Cambia la VLAN de un puerto en un switch Cisco.

    - switch_ip: IP del switch (ej. 192.168.1.11)
    - interfaz: nombre de la interfaz (Fa1/0/2, Gi0/1, FastEthernet0/3, etc.)
    - vlan_nueva: número de VLAN en texto (ej. "10")

    Regresa la salida de Netmiko como string.
    Lanza Exception si algo sale mal.
    """

    device = {
        "device_type": "cisco_ios",
        "host": switch_ip,
        "username": "cisco",
        "password": "cisco99",
        "secret": "cisco99",
        "port": 22,
    }

    try:
        conn = ConnectHandler(**device)
        conn.enable()

        interfaz = interfaz.strip()
        vlan_nueva = vlan_nueva.strip()

        comandos = [
            f"interface {interfaz}",
            "switchport mode access",
            f"switchport access vlan {vlan_nueva}",
            "shutdown",
            "no shutdown", 
            "end",
            "wr"
        ]

        salida = conn.send_config_set(comandos)
        conn.disconnect()
        return salida

    except Exception as e:
        raise Exception(f"Error al cambiar VLAN en {switch_ip} ({interfaz} -> VLAN {vlan_nueva}): {e}")
