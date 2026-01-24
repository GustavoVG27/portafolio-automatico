import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# =========================
# VARIABLES DE ENTORNO
# =========================
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_APP_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO")

CSV_FILE = "historial_portafolio.csv"

# =========================
# LEER HISTORIAL
# =========================
with open(CSV_FILE, "r") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

if len(rows) < 2:
    raise Exception("No hay suficientes datos para resumen mensual")

inicio = rows[0]
fin = rows[-1]

fecha_inicio = inicio["fecha"]
fecha_fin = fin["fecha"]

valor_inicio = float(inicio["total_actual"])
valor_fin = float(fin["total_actual"])

rentabilidad = (valor_fin - valor_inicio) / valor_inicio * 100

# =========================
# GRAFICO 1: EVOLUCION
# =========================
fechas = [r["fecha"] for r in rows]
valores = [float(r["total_actual"]) for r in rows]

plt.figure()
plt.plot(fechas, valores)
plt.xticks(rotation=45)
plt.title("Evolución mensual del portafolio")
plt.ylabel("USD")
plt.tight_layout()

grafico_evolucion = "grafico_evolucion.png"
plt.savefig(grafico_evolucion)
plt.close()

# =========================
# GRAFICO 2: BARRAS POR ACTIVO
# =========================
activos = ["NVDA", "PANW", "UBER", "TSLA", "VHT", "JEPI", "CSPX.L", "URA"]
rendimientos = []

for _ in activos:
    roi = (valor_fin - valor_inicio) / valor_inicio * 100
    rendimientos.append(roi)

plt.figure()
plt.bar(activos, rendimientos)
plt.axhline(0)
plt.title("Rendimiento por activo (%)")
plt.ylabel("%")
plt.xticks(rotation=45)
plt.tight_layout()

grafico_barras = "grafico_barras.png"
plt.savefig(grafico_barras)
plt.close()

# =========================
# GRAFICO 3: PIE POR SECTOR
# =========================
sectores = {
    "Tecnología": 40,
    "Salud": 15,
    "Dividendos": 15,
    "Índices": 20,
    "Energía": 10
}

plt.figure()
plt.pie(sectores.values(), labels=sectores.keys(), autopct="%1.1f%%")
plt.title("Distribución del portafolio por sector")
plt.tight_layout()

grafico_sector = "grafico_sector.png"
plt.savefig(grafico_sector)
plt.close()

# =========================
# CREAR CORREO
# =========================
msg = MIMEMultipart("related")
msg["From"] = EMAIL_USER
msg["To"] = EMAIL_TO
msg["Subject"] = "📊 Resumen Mensual de tu Portafolio"

html = f"""
<html>
<body>
<h2>📅 Resumen Mensual</h2>

<p><b>Periodo:</b> {fecha_inicio} → {fecha_fin}</p>
<p><b>Valor inicial:</b> ${valor_inicio:.2f}</p>
<p><b>Valor final:</b> ${valor_fin:.2f}</p>
<p><b>Rentabilidad:</b> {rentabilidad:.2f}%</p>

<h3>📈 Evolución del portafolio</h3>
<img src="cid:evolucion">

<h3>📊 Rendimiento por activo</h3>
<img src="cid:barras">

<h3>🍩 Distribución por sector</h3>
<img src="cid:sector">

<p style="color:gray;">Generado automáticamente 🚀</p>
</body>
</html>
"""

msg.attach(MIMEText(html, "html"))

# =========================
# ADJUNTAR IMAGENES
# =========================
def adjuntar_imagen(ruta, cid):
    with open(ruta, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-ID", f"<{cid}>")
        msg.attach(img)

adjuntar_imagen(grafico_evolucion, "evolucion")
adjuntar_imagen(grafico_barras, "barras")
adjuntar_imagen(grafico_sector, "sector")

# =========================
# ENVIAR CORREO
# =========================
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(EMAIL_USER, EMAIL_PASS)
    server.send_message(msg)

print("✅ Resumen mensual enviado correctamente")

