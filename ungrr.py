import serial
import time
import pandas as pd
from datetime import datetime

# === CONFIGURAR PUERTO COM ===
ser = serial.Serial(
    port="COM9",        # ⚠️ Cambia a tu COM real
    baudrate=9600,
    timeout=1
)

time.sleep(1)

# === FUNCIONES ===
def send(cmd, wait=1):
    ser.write(cmd.encode('utf-8') + b'\r')
    time.sleep(wait)
    return ser.read(8000).decode('utf-8', errors='ignore')

# === DESPERTAR CONSOLA ===
send("\r")

# === HOSTNAME ===
hostname_output = send("show running-config | include hostname")
if "hostname" in hostname_output:
    hostname = hostname_output.split()[-1]
else:
    hostname = "Desconocido"

# === OBTENER show ip interface brief ===
raw_output = send("show ip interface brief", wait=2)
print("\nSalida recibida:\n", raw_output)

ser.close()

# === PARSEAR SIN TEXTFSM ===
lineas = raw_output.splitlines()
datos = []

for linea in lineas:
    if (
        linea.startswith("Interface")
        or linea.startswith("show ip")
        or linea.strip() == ""
        or hostname in linea
    ):
        continue

    partes = linea.split()
    if len(partes) >= 6:
        interf = partes[0]
        ip = partes[1]
        status = partes[-2]
        proto = partes[-1]
        datos.append([interf, ip, status, proto])

df = pd.DataFrame(datos, columns=["Interface", "IP", "Status", "Protocol"])

# === TIMESTAMP ===
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
df["Hostname"] = hostname
df["Timestamp"] = timestamp

# === GUARDAR A EXCEL ===
nombre_archivo = "interfaces_completo.xlsx"
df.to_excel(nombre_archivo, index=False)

print(f"\n✅ Archivo creado correctamente: {nombre_archivo}")
