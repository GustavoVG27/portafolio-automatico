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
# CONFIG CORREO
# =========================
CORREO_EMISOR = os.environ.get("EMAIL_USER")
CONTRASENA_APP = os.environ.get("EMAIL_APP_PASSWORD")
CORREO_DESTINO = os.environ.get("EMAIL_TO")

if not CORREO_EMISOR or not CONTRASENA_APP or not CORREO_DESTINO:
    raise ValueError("Faltan variables de entorno")

# =========================
# FECHAS
# =========================
hoy = datetime.now()
mes_actual = hoy.strftime("%Y-%m")
nombre_mes = hoy.strftime("%B %Y")

archivo_csv = "historial_portafolio.csv"

# =========================
# LEER HISTORIAL DEL MES
# =========================
fechas = []
valores = []

with open(archivo_csv, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["fecha"].startswith(mes_actual):
            fechas.append(row["fecha"])
            valores.append(float(row["total_actual"]))

if not fechas:
    print("No hay datos del mes")
    exit()

# =========================
# CALCULOS
# =========================
inicio = valores[0]
fin = valores[-1]
ganancia = fin - inicio
porcentaje = (ganancia / inicio) * 100

# =========================
# GRAFICO
# =========================
plt.figure()
plt.plot(fechas, valores)
plt.title("Evolución del Portafolio - " + nombre_mes)
plt.xlabel("Fecha")
plt.ylabel("Valor ($)")
plt.xticks(rotation=45)
plt.tight_layout()

grafico = "grafico_mensual.png"
plt.savefig(grafico)
plt.close()

# =========================
# CSV DEL MES
# =========================
csv_mes = "historial_mensual.csv"
with open(csv_mes, "w", newline="") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["fecha", "valor"])
    for f, v in zip(fechas, valores):
        writer.writerow([f, v])

# =========================
# MENSAJE HTML
# =========================
mensaje_html = f"""
<h1>📆 Resumen Mensual del Portafolio</h1>
<h2>{nombre_mes}</h2>

<p>
<b>Valor inicial:</b> ${inicio:.2f}<br>
<b>Valor final:</b> ${fin:.2f}<br>
<b>Resultado del mes:</b>
<b style="color:{'green' if ganancia >= 0 else 'red'};">
${ganancia:+.2f} ({porcentaje:+.2f}%)
</b>
</p>

<h2>📊 Evolución del portafolio</h2>
<img src="cid:grafico">

<h2>🧠 Comentario del analista</h2>
<p>
El portafolio cerró el mes con un rendimiento
<b style="color:{'green' if ganancia >= 0 else 'red'};">
{porcentaje:+.2f}%
</b>.
La evolución refleja una gestión estable y disciplinada,
con un enfoque en diversificación y control del riesgo.
</p>
"""

# =========================
# CORREO
# =========================
msg = MIMEMultipart("related")
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📆 Resumen Mensual del Portafolio – {nombre_mes}"

msg_alt = MIMEMultipart("alternative")
msg.attach(msg_alt)
msg_alt.attach(MIMEText(mensaje_html, "html"))

# Imagen
with open(grafico, "rb") as f:
    img = MIMEBase("image", "png")
    img.set_payload(f.read())
    encoders.encode_base64(img)
    img.add_header("Content-ID", "<grafico>")
    img.add_header("Content-Disposition", "inline", filename=grafico)
    msg.attach(img)

# CSV adjunto
with open(csv_mes, "rb") as f:
    adj = MIMEBase("application", "octet-stream")
    adj.set_payload(f.read())
    encoders.encode_base64(adj)
    adj.add_header("Content-Disposition", f'attachment; filename="{csv_mes}"')
    msg.attach(adj)

# Enviar
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Resumen mensual enviado")

