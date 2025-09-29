import serial
import time
import pandas as pd
import os
import re

# 🔹 Limpiar pantalla según el SO
def limpiar_pantalla_consola():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

# 🔹 Enviar comando al router
def enviar_comando_al_equipo(puerto_serial, comando_para_enviar, retraso=1):
    puerto_serial.write((comando_para_enviar + "\r\n").encode())  # CRLF
    time.sleep(retraso)
    respuesta_del_equipo = puerto_serial.read(puerto_serial.in_waiting).decode(errors="ignore")
    return respuesta_del_equipo

# 🔹 Obtener número de serie desde "show inventory"
def obtener_numero_de_serie(conexion_serial):
    enviar_comando_al_equipo(conexion_serial, "terminal length 0")  # evitar paginación
    salida_inventario = enviar_comando_al_equipo(conexion_serial, "show inventory", retraso=2)
    coincidencia_serie = re.search(r"SN:\s*([A-Z0-9]+)", salida_inventario)
    if coincidencia_serie:
        return coincidencia_serie.group(1)
    return None

# 🔹 Configuración de dispositivo
def configurar_dispositivo_individual(puerto_com, nombre_host, nombre_usuario, clave_secreta, nombre_dominio):
    try:
        conexion_activa = serial.Serial(puerto_com, baudrate=9600, timeout=1)
        time.sleep(2)
        print(f"\n🔗 Conectado al dispositivo en {puerto_com} ({nombre_host})")

        serial_obtenido = obtener_numero_de_serie(conexion_activa)
        if not serial_obtenido:
            print("⚠ No se pudo obtener el número de serie. Saltando configuración.")
            conexion_activa.close()
            return False

        if nombre_host[1:] != serial_obtenido:
            print(f"⚠ La serie del dispositivo ({serial_obtenido}) no coincide con la del CSV ({nombre_host[1:]}). Saltando configuración.")
            conexion_activa.close()
            return False

        enviar_comando_al_equipo(conexion_activa, "enable")
        enviar_comando_al_equipo(conexion_activa, "configure terminal")
        enviar_comando_al_equipo(conexion_activa, f"hostname {nombre_host}")
        enviar_comando_al_equipo(conexion_activa, f"username {nombre_usuario} privilege 15 secret {clave_secreta}")
        enviar_comando_al_equipo(conexion_activa, f"ip domain-name {nombre_dominio}")
        enviar_comando_al_equipo(conexion_activa, "crypto key generate rsa modulus 1024", retraso=3)
        enviar_comando_al_equipo(conexion_activa, "line vty 0 4")
        enviar_comando_al_equipo(conexion_activa, "login local")
        enviar_comando_al_equipo(conexion_activa, "transport input ssh")
        enviar_comando_al_equipo(conexion_activa, "transport output ssh")
        enviar_comando_al_equipo(conexion_activa, "exit")
        enviar_comando_al_equipo(conexion_activa, "ip ssh version 2")
        enviar_comando_al_equipo(conexion_activa, "end")
        enviar_comando_al_equipo(conexion_activa, "write memory", retraso=2)

        print(f"✅ Configuración aplicada correctamente en {nombre_host}.")
        conexion_activa.close()
        return True

    except Exception as excepcion_ocurrida:
        print(f"❌ Error al configurar el dispositivo {nombre_host}: {excepcion_ocurrida}")
        return False

# 🔹 Menú principal
def presentar_menu_principal():
    limpiar_pantalla_consola()
    print("=== MENÚ PRINCIPAL ===")
    print("1. Mandar comandos manualmente")
    print("2. Hacer configuraciones iniciales desde CSV")
    print("0. Salir")

# 🔹 Menú de comandos manuales
def menu_de_comandos_manuales():
    puerto_de_conexion = input("🔌 Ingresa el puerto serial (ej. COM3): ")
    try:
        sesion_serial = serial.Serial(puerto_de_conexion, baudrate=9600, timeout=1)
        time.sleep(2)
        print(f"\n✅ Conectado al dispositivo en {puerto_de_conexion}")
        while True:
            comando_ingresado = input("📥 Ingresa el comando (o 'exit' para salir): ")
            if comando_ingresado.lower() == "exit":
                break
            salida_del_comando = enviar_comando_al_equipo(sesion_serial, comando_ingresado, retraso=2)
            print(f"\n📤 Respuesta:\n{salida_del_comando}")
        sesion_serial.close()
    except Exception as error_general:
        print(f"❌ Error al conectar: {error_general}")
    input("Presione ENTER para volver al menú...")

# 🔹 Flujo de configuración inicial
def flujo_de_configuracion_con_csv():
    limpiar_pantalla_consola()
    dataframe_dispositivos = pd.read_csv("C:\\Users\\Dani\\OneDrive\\Escritorio\\Clases Unipoli\\Cuatri 4\\Programacion de Redes\\Apuntes\\VENV\\Data.csv")
    print("\n📂 Dispositivos encontrados en el archivo:")
    print(dataframe_dispositivos)

    NombresDeHostGenerados = [str(d).strip()[0] + str(s).strip() for d, s in zip(dataframe_dispositivos['Device'], dataframe_dispositivos['Serie'])]
    lista_completa_dispositivos = [(p, h, u, pas, dom) for p, u, pas, dom, h in zip(dataframe_dispositivos['Port'], dataframe_dispositivos['User'], dataframe_dispositivos['Password'], dataframe_dispositivos['Ip-domain'], NombresDeHostGenerados)]

    print("\n📋 Lista de dispositivos y sus configuraciones:")
    for elemento in lista_completa_dispositivos:
        print(elemento)
    input("Presione ENTER para continuar...")

    dispositivos_configurados_ok = []
    dispositivos_omitidos = []

    for indice, (puerto, host, usr, pwd, dominio_ip) in enumerate(lista_completa_dispositivos, start=1):
        limpiar_pantalla_consola()
        print(f"\n➡ Conecte ahora el dispositivo {indice}: {host} en el puerto {puerto}")
        input("Presione ENTER cuando el dispositivo esté conectado...")
        fue_exitoso = configurar_dispositivo_individual(puerto, host, usr, pwd, dominio_ip)
        if fue_exitoso:
            dispositivos_configurados_ok.append(host)
        else:
            dispositivos_omitidos.append(host)
        print("=================================================")
        input("Presione ENTER para continuar...")

    limpiar_pantalla_consola()
    print("📊 Resumen de la configuración:")
    print(f"✅ Dispositivos configurados ({len(dispositivos_configurados_ok)}): {dispositivos_configurados_ok}")
    print(f"⚠ Dispositivos saltados ({len(dispositivos_omitidos)}): {dispositivos_omitidos}")
    input("Presione ENTER para volver al menú...")

# 🔹 Ejecutar menú
if __name__ == "__main__":
    while True:
        presentar_menu_principal()
        opcion_elegida = input("Selecciona una opción: ")
        if opcion_elegida == "1":
            menu_de_comandos_manuales()
        elif opcion_elegida == "2":
            flujo_de_configuracion_con_csv()
        elif opcion_elegida == "0":
            print("👋 Saliendo del programa...")
            break
        else:
            print("❌ Opción inválida.")
            input("Presione ENTER para continuar...")