from netmiko import ConnectHandler

# DEFINICIÓN DE SWITCHES

switches = {
    "192.168.1.1": {
        "name": "CORE-SW1",
        "device_type": "cisco_ios",
        "host": "192.168.1.1",
        "username": "cisco",
        "password": "cisco99",
    },
    "192.168.1.11": {
        "name": "SW2",
        "device_type": "cisco_ios",
        "host": "192.168.1.11",
        "username": "cisco",
        "password": "cisco99",
    },
    "192.168.1.12": {
        "name": "SW3",
        "device_type": "cisco_ios",
        "host": "192.168.1.12",
        "username": "cisco",
        "password": "cisco99",
    }
}

# FUNCIONES DE CONEXIÓN Y PARSEO

def connect_to(ip):
    """Crea una conexión Netmiko al switch indicado."""
    data = switches[ip].copy()
    data.pop("name")
    return ConnectHandler(**data)


def get_mac_from_arp(conn, ip):
    """Busca la MAC correspondiente a una IP en la tabla ARP."""
    salida = conn.send_command("show arp")
    for linea in salida.splitlines():
        partes = linea.split()
        if len(partes) >= 4 and partes[0] == "Internet" and partes[1] == ip:
            return partes[3]
    return None


def get_mac_entry(conn, mac):
    """Obtiene la interfaz y VLAN donde aparece una MAC."""
    salida = conn.send_command(f"show mac address-table | include {mac}")
    if salida:
        partes = salida.split()
        return {"vlan": partes[0], "interface": partes[-1]}
    return None


def get_cdp_neighbors(conn):
    """Obtiene vecinos CDP detallados."""
    salida = conn.send_command("show cdp neighbors detail")
    vecinos = {}

    bloques = salida.split("Device ID:")
    for bloque in bloques[1:]:
        lineas = bloque.splitlines()
        vecino_name = lineas[0].strip()
        vecino_ip = None
        interfaz = None

        for linea in lineas:
            if "IP address:" in linea:
                vecino_ip = linea.split("IP address:")[1].strip()
            if "Interface:" in linea:
                interfaz = linea.split("Interface:")[1].split(",")[0].strip()

        if interfaz and vecino_ip:
            vecinos[interfaz] = {"ip": vecino_ip, "name": vecino_name}

    return vecinos

# ALGORITMO PRINCIPAL

def locate_ip_anywhere(start_sw_ip, ip_host):
    """Busca la IP en todos los switches y luego rastrea la MAC encontrada."""
    print("\n=== BUSQUEDA DE ARP ===")

    orden_busqueda = [start_sw_ip] + [ip for ip in switches if ip != start_sw_ip]
    mac_encontrada = None
    sw_donde_aparecio = None

    for sw_ip in orden_busqueda:
        print(f"\nBuscando IP {ip_host} en ARP de {switches[sw_ip]['name']}...")

        conn = connect_to(sw_ip)
        mac = get_mac_from_arp(conn, ip_host)
        conn.disconnect()

        if mac:
            print(f"IP encontrada en: {switches[sw_ip]['name']}")
            print(f"MAC: {mac}")
            mac_encontrada = mac
            sw_donde_aparecio = sw_ip
            break
        else:
            print("No encontrada en este switch.")

    if not mac_encontrada:
        print("\nLa IP NO fue encontrada en ningún switch.")
        return

    print("\n=== INICIANDO RASTREO MAC/CDP ===")
    trace_from_switch(sw_donde_aparecio, ip_host, mac_encontrada)


def trace_from_switch(start_sw_ip, ip_host, mac):
    """Rastrea la MAC saltando entre switches usando CDP."""
    current_sw_ip = start_sw_ip

    while True:
        sw_data = switches[current_sw_ip]
        print(f"\nRevisando MAC en {sw_data['name']} ({current_sw_ip})...")

        conn = connect_to(current_sw_ip)
        mac_entry = get_mac_entry(conn, mac)
        neighbors = get_cdp_neighbors(conn)

        if not mac_entry:
            print("ERROR: La MAC no aparece en este switch. Rastreo detenido.")
            conn.disconnect()
            return

        interfaz = mac_entry["interface"]
        vlan = mac_entry["vlan"]

        print(f"MAC encontrada en {interfaz}  VLAN {vlan}")

        # Si el puerto NO está en CDP → es un host final
        if interfaz not in neighbors:
            print("\nDISPOSITIVO FINAL: HOST\n")
            print(f"IP del host: {ip_host}")
            print(f"MAC: {mac}")
            print(f"Switch final: {sw_data['name']} ({current_sw_ip})")
            print(f"Puerto: {interfaz}")
            print(f"VLAN: {vlan}")
            conn.disconnect()
            return

        # Si está en CDP → continuar al siguiente switch
        vecino = neighbors[interfaz]
        vecino_ip = vecino["ip"]
        vecino_name = vecino["name"]

        print("\nDISPOSITIVO: SWITCH")
        print(f"Vecino: {vecino_name}  ({vecino_ip})")
        print("Saltando al switch vecino...\n")

        conn.disconnect()

        if vecino_ip not in switches:
            print("El vecino no está en la lista de switches conocidos.")
            return

        current_sw_ip = vecino_ip

# EJECUCIÓN

print("\n=== SWITCHES DISPONIBLES ===")
for ip, data in switches.items():
    print(f"{ip}  →  {data['name']}")

start_sw = input("\nIngresa la IP del switch donde iniciarás la búsqueda: ")
ip_buscar = input("Ingresa la IP del host a rastrear: ")

if start_sw not in switches:
    print("Switch inválido.")
else:
    locate_ip_anywhere(start_sw, ip_buscar)