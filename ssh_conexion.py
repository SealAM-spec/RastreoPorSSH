from netmiko import ConnectHandler

# === Mapeo de puertos del Core hacia switches de acceso ===
puertos_switches = {
    "Gi0/1": "Switch1",
    "Gi0/2": "Switch2",
    "Gi0/0": "Troncal",
    # Agrega más si tienes otros enlaces
}

# === Datos de conexión al Core ===
core = {
    "device_type": "cisco_ios",
    "ip": "192.168.1.1",
    "username": "cisco",
    "password": "cisco99",
    "name": "Core"
}

# === Conexión SSH ===
print(f"\n🔌 Conectando al {core['name']} ({core['ip']})...")
conexion = ConnectHandler(
    device_type=core["device_type"],
    ip=core["ip"],
    username=core["username"],
    password=core["password"]
)

# === Obtener datos de red ===
arp_output = conexion.send_command("show ip arp")
mac_output = conexion.send_command("show mac address-table")
conexion.disconnect()

# === Procesar ARP: IP ↔ MAC ===
hosts = []
for linea in arp_output.splitlines():
    if "Internet" in linea:
        partes = linea.split()
        ip = partes[1]
        mac = partes[3]
        hosts.append({"ip": ip, "mac": mac})

# === Asociar MAC ↔ Puerto del Core ===
for host in hosts:
    puerto = "Desconocido"
    for linea in mac_output.splitlines():
        if host["mac"] in linea:
            campos = linea.split()
            if len(campos) >= 4:
                puerto = campos[-1]
                break
    switch = puertos_switches.get(puerto, "Desconocido")
    print(f"🔍 Host → IP: {host['ip']} | MAC: {host['mac']} | Puerto en Core: {puerto} → {switch}")
