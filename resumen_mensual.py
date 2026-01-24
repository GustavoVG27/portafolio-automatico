import csv
import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import matplotlib.pyplot as plt

# =========================
# CONFIG EMAIL
# =========================
CORREO_EMISOR = os.environ.get("EMAIL_USER")
CONTRASENA_APP = os.environ.get("EMAIL_APP_PASSWORD")
CORREO_DESTINO = os.environ.get("EMAIL_TO")

# =========================
# FECHAS
# =========================
hoy = datetime.now()
mes_actual = hoy.strftime("%Y-%m")
nombre_mes = hoy.strftime("%B %Y")

archivo_csv = "historial_portafolio.csv"

fechas = []
valores = []

# =========================
# LEER CSV (SOLO MES ACTUAL)
# =========================
with open(archivo_csv, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["fecha"].startswith(mes_actual):
            fechas.append(row["fecha"])
            valores.append(float(row["total_actual"]))

if not fechas:
    print("No hay datos mensuales")
    exit()

inicio = valores[0]
fin = valores[-1]
ganancia = fin - inicio
porcentaje = (ganancia / inicio) * 100

# =========================
# 📊 GRAFICO EVOLUCIÓN
# =========================
plt.figure()
plt.plot(fechas, valores)
plt.title("Evolución mensual del portafolio")
plt.xticks(rotation=45)
plt.tight_layout()

grafico_path = "grafico_mensual.png"
plt.savefig(grafico_path)
plt.close()

# =========================
# CSV MENSUAL
# =========================
csv_mensual = f"historial_{mes_actual}.csv"

with open(csv_mensual, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["fecha", "valor"])
    for fch, val in zip(fechas, valores):
        writer.writerow([fch, val])

# =========================
# MENSAJE
# =========================
mensaje_html = f"""
<h1>📆 Resumen Mensual del Portafolio</h1>
<h2>{nombre_mes}</h2>

<p>
💰 Valor inicial: ${inicio:.2f}<br>
📈 Valor final: ${fin:.2f}<br>
💵 Resultado: <b>${ganancia:+.2f} ({porcentaje:+.2f}%)</b>
</p>

<h2>🧠 Comentario del analista</h2>
<p>
El portafolio mostró un comportamiento {"positivo" if ganancia > 0 else "negativo"}
durante el mes, con una variación total de {porcentaje:+.2f}%.
</p>

<p>📊 Ver gráfico y CSV adjuntos.</p>
"""

# =========================
# ENVIAR CORREO
# =========================
msg = MIMEMultipart()
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📆 Resumen Mensual del Portafolio - {nombre_mes}"
msg.attach(MIMEText(mensaje_html, "html"))

for archivo in [grafico_path, csv_mensual]:
    with open(archivo, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{archivo}"')
    msg.attach(part)

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Resumen mensual enviado")
