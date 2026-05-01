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

# 🔍 DEBUG (puedes borrarlo luego)
print("Columnas detectadas:", datos[0].keys())

# =========================
# DETECTAR COLUMNA CORRECTA
# =========================
posibles_claves = ["total_actual", "total", "balance", "valor"]

clave_total = None
for clave in posibles_claves:
    if clave in datos[0]:
        clave_total = clave
        break

if clave_total is None:
    print("❌ Error: No se encontró columna válida en el CSV")
    print("Columnas disponibles:", datos[0].keys())
    exit()

print(f"✅ Usando columna: {clave_total}")

# =========================
# FILTRAR ÚLTIMA SEMANA
# =========================
ultimos_7 = datos[-7:]

try:
    inicio = float(ultimos_7[0][clave_total])
    fin = float(ultimos_7[-1][clave_total])
except Exception as e:
    print("❌ Error al convertir datos:", e)
    exit()

ganancia = fin - inicio
porcentaje = (ganancia / inicio) * 100 if inicio != 0 else 0

# =========================
# COMENTARIO ANALISTA
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
if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
    print("❌ Faltan variables de entorno (EMAIL_USER, EMAIL_PASS, EMAIL_TO)")
    exit()

msg = MIMEMultipart()
msg["From"] = EMAIL_USER
msg["To"] = EMAIL_TO
msg["Subject"] = f"📅 Resumen Semanal Portafolio - Semana {datetime.now().isocalendar()[1]}"

msg.attach(MIMEText(mensaje, "html"))

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(EMAIL_USER, EMAIL_PASS)
        s.send_message(msg)

    print("📧 Resumen semanal enviado correctamente")

except Exception as e:
    print("❌ Error enviando correo:", e)
