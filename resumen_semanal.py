import csv
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from analitica import comentario_analista

ARCHIVO = "historial_portafolio.csv"

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_APP_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO")

# =========================
# LEER CSV
# =========================
with open(ARCHIVO, newline="") as f:
    reader = csv.DictReader(f)
    datos = list(reader)

if len(datos) < 5:
    print("No hay suficientes datos para resumen semanal")
    exit()

# =========================
# FILTRAR ÚLTIMA SEMANA
# =========================
ultimos_7 = datos[-7:]

inicio = float(ultimos_7[0]["total_actual"])
fin = float(ultimos_7[-1]["total_actual"])

ganancia = fin - inicio
porcentaje = (ganancia / inicio) * 100 if inicio != 0 else 0

# =========================
# COMENTARIO ANALISTA SEMANAL
# =========================
comparacion_fake = {
    "diff": ganancia
}

ranking_fake = [
    {"ticker": "Portafolio", "roi": porcentaje}
]

comentario = comentario_analista(comparacion_fake, ranking_fake)

# =========================
# MENSAJE HTML
# =========================
mensaje = f"""
<h1>📅 Resumen Semanal del Portafolio</h1>

<p>
<b>Inicio de la semana:</b> ${inicio:.2f}<br>
<b>Fin de la semana:</b> ${fin:.2f}<br>
<b>Resultado semanal:</b>
<b style="color:{'green' if ganancia > 0 else 'red'}">
${ganancia:+.2f} ({porcentaje:+.2f}%)
</b>
</p>

<hr>
<h2>🧠 Comentario del analista</h2>
<p>{comentario}</p>
"""

# =========================
# ENVIAR CORREO
# =========================
msg = MIMEMultipart()
msg["From"] = EMAIL_USER
msg["To"] = EMAIL_TO
msg["Subject"] = f"📅 Resumen Semanal Portafolio - Semana {datetime.now().isocalendar()[1]}"

msg.attach(MIMEText(mensaje, "html"))

with smtplib.SMTP("smtp.gmail.com", 587) as s:
    s.starttls()
    s.login(EMAIL_USER, EMAIL_PASS)
    s.send_message(msg)

print("📧 Resumen semanal enviado")
