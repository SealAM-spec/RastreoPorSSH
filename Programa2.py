import serial
import time
import pandas as pd
from textfsm import clitable
from datetime import datetime
from openpyxl import load_workbook
import os

# === CONFIGURACIÓN SERIAL ===
PORT = 'COM9'           # Ajusta según tu sistema
BAUDRATE = 9600         # Velocidad típica para Cisco
TIMEOUT = 2             # Tiempo de espera

# === CONEXIÓN SERIAL ===
ser = serial.Serial(PORT, baudrate=BAUDRATE, timeout=TIMEOUT)
time.sleep(1)  # Espera para estabilizar

# === ENVÍO DE COMANDOS ===
ser.write(b'\r')              # Despierta el prompt
ser.write(b'enable\r')        # Comando correcto para modo privilegiado
time.sleep(1)

# Obtener hostname
ser.write(b'show running-config | include hostname\r')
time.sleep(1)
hostname_output = ser.read(1000).decode('utf-8', errors='ignore')
if "hostname" in hostname_output:
    hostname = hostname_output.split()[-1]
else:
    hostname = "Desconocido"

# Obtener interfaces
ser.write(b'show ip interface brief\r')
time.sleep(2)
output = ser.read(5000).decode('utf-8', errors='ignore')
ser.close()

print("Salida recibida del router:\n")
print(output)

# === PARSEO CON TEXTFSM ===
# Usa ruta absoluta si ntc_templates no está junto al script
ruta_templates = os.path.join(os.path.dirname(__file__), 'ntc_templates')
print("Ruta templates:", ruta_templates)
print("Contenido:", os.listdir(ruta_templates))  # Verifica que index esté aquí

cli_table = clitable.CliTable("index", ruta_templates)
attributes = {"Command": "show ip interface brief", "Platform": "cisco_ios"}
cli_table.ParseCmd(output, attributes)

data = [list(row) for row in cli_table]
headers = list(cli_table.header)
df = pd.DataFrame(data, columns=headers)

# === TIMESTAMP ===
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
df["Hostname"] = hostname
df["Timestamp"] = timestamp

# === SALIDA CRUDA ===
df_raw = pd.DataFrame({"Salida cruda": output.splitlines()})
df_raw["Hostname"] = hostname
df_raw["Timestamp"] = timestamp

# === GUARDAR EN EXCEL EXISTENTE ===
archivo_excel = "interfaces_completo.xlsx"
try:
    libro = load_workbook(archivo_excel)
except FileNotFoundError:
    print(f"⚠️ El archivo '{archivo_excel}' no existe. Se creará uno nuevo.")
    libro = None

with pd.ExcelWriter(archivo_excel, engine="openpyxl", mode="a" if libro else "w") as writer:
    if libro:
        writer.book = libro
        writer.sheets = {ws.title: ws for ws in libro.worksheets}  # sincroniza hojas

    # Nombres de hoja seguros (máx 31 caracteres)
    hoja_parseada = f"Parseadas_{hostname}_{timestamp[:10]}"[:31]
    hoja_cruda = f"Cruda_{hostname}_{timestamp[:10]}"[:31]

    df.to_excel(writer, sheet_name=hoja_parseada, index=False)
    df_raw.to_excel(writer, sheet_name=hoja_cruda, index=False)

print(f"\n✅ Datos agregados a '{archivo_excel}' en hojas '{hoja_parseada}' y '{hoja_cruda}'")
