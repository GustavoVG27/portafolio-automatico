import yfinance as yf
import csv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from portfolio import PORTAFOLIO
import os

# =========================
# CONFIGURACIÓN DE CORREO
# =========================
CORREO_EMISOR = os.environ.get("EMAIL_USER")
CONTRASENA_APP = os.environ.get("EMAIL_APP_PASSWORD")
CORREO_DESTINO = os.environ.get("EMAIL_TO")

if not CORREO_EMISOR or not CONTRASENA_APP or not CORREO_DESTINO:
    raise ValueError("❌ Faltan variables de entorno para el correo")

# =========================
# FECHA
# =========================
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# =========================
# ARCHIVOS CSV
# =========================
CSV_DETALLADO = "historial_portafolio_detallado.csv"
CSV_TOTALES = "historial_portafolio_totales.csv"

# =========================
# SECTORES
# =========================
SECTORES = {
    "🧠 TECNOLOGÍA": ["NVDA", "PANW", "UBER"],
    "📈 S&P 500 / ÍNDICES": ["CSPX.L"],
    "🏥 SALUD": ["VHT"],
    "🌎 MERCADOS INTERNACIONALES": ["VXUS"],
    "⚡ ENERGÍA": ["URA"],
    "₿ CRIPTO": ["BTC-USD"]
}

UMBRAL_ALERTA = 3
alertas = []
ranking = []

total_invertido = 0.0
total_actual = 0.0

mensaje = ["<h1>📊 Evaluación diaria del portafolio</h1>"]
acciones_para_csv = []

# =========================
# PROCESO PRINCIPAL
# =========================
for sector, tickers in SECTORES.items():
    mensaje.append(f"<h2>{sector}</h2>")

    for ticker in tickers:
        datos = PORTAFOLIO[ticker]
        hist = yf.Ticker(ticker).history(period="1d")

        if hist.empty:
            continue

        precio = float(hist["Close"].iloc[-1])
        valor_actual = precio * datos["cantidad"]
        ganancia = valor_actual - datos["invertido"]
        roi = (ganancia / datos["invertido"]) * 100

        total_invertido += datos["invertido"]
        total_actual += valor_actual

        ranking.append((ticker, roi))

        if roi >= UMBRAL_ALERTA:
            alertas.append(f"🟢 <b>{ticker}</b> sube fuerte <b>+{roi:.2f}%</b>")
        elif roi <= -UMBRAL_ALERTA:
            alertas.append(f"🔴 <b>{ticker}</b> cae fuerte <b>{roi:.2f}%</b>")

        color = "green" if roi >= 0 else "red"

        mensaje.append(f"""
        <p>
        <b>{ticker} ({datos['nombre']})</b><br>
        📦 Cantidad de acciones: {datos['cantidad']}<br>
        💰 Inversión inicial: ${datos['invertido']:.2f}<br>
        📈 Valor actual: ${valor_actual:.2f}<br>
        💵 Ganancia:
        <b style="color:{color};">
        ${ganancia:+.2f} ({roi:+.2f}%)
        </b>
        </p>
        """)

        acciones_para_csv.append({
            "fecha": fecha_hoy,
            "ticker": ticker,
            "nombre": datos["nombre"],
            "cantidad": datos["cantidad"],
            "invertido": round(datos["invertido"], 2),
            "valor_actual": round(valor_actual, 2),
            "ganancia": round(ganancia, 2),
            "roi": round(roi, 2)
        })

# =========================
# ALERTAS
# =========================
if alertas:
    mensaje.append("<hr><h2 style='color:red;'>🚨 ALERTAS DEL DÍA</h2><ul>")
    for a in alertas:
        mensaje.append(f"<li>{a}</li>")
    mensaje.append("</ul>")

# =========================
# COMPARACIÓN VS AYER
# =========================
ayer_total = None

if os.path.isfile(CSV_TOTALES):
    with open(CSV_TOTALES, "r") as f:
        rows = list(csv.DictReader(f))
        if rows:
            ayer_total = float(rows[-1]["total_actual"])

mensaje.append("<hr><h2>📊 Comparación vs ayer</h2>")

if ayer_total:
    variacion = total_actual - ayer_total
    porcentaje = (variacion / ayer_total) * 100
    mensaje.append(
        f"Ayer: ${ayer_total:.2f}<br>"
        f"Hoy: ${total_actual:.2f}<br>"
        f"Variación: ${variacion:+.2f} ({porcentaje:+.2f}%)"
    )
else:
    mensaje.append("No hay datos del día anterior.")

# =========================
# RANKING
# =========================
ranking.sort(key=lambda x: x[1], reverse=True)
mensaje.append("<hr><h2>🏆 Ranking</h2>")
for i, (t, r) in enumerate(ranking, 1):
    mensaje.append(f"{i}️⃣ {t} ({r:+.2f}%)<br>")

# =========================
# COMENTARIO
# =========================
mejor = ranking[0]
mensaje.append(f"""
<hr>
<h2>🧠 Comentario del analista</h2>
El activo más destacado fue <b>{mejor[0]}</b>
con una variación de <b>{mejor[1]:+.2f}%</b>.
""")

# =========================
# ✅ NUEVO: RESUMEN TOTAL
# =========================
ganancia_total = total_actual - total_invertido
porcentaje_total = (ganancia_total / total_invertido) * 100 if total_invertido != 0 else 0

color_total = "green" if ganancia_total >= 0 else "red"

mensaje.append(f"""
<hr>
<h2>💼 Resumen total del portafolio</h2>

<p>
💰 <b>Total invertido:</b> ${total_invertido:.2f}<br>
📈 <b>Valor actual:</b> ${total_actual:.2f}<br>
💵 <b>Ganancia total:</b>
<b style="color:{color_total};">
${ganancia_total:+.2f} ({porcentaje_total:+.2f}%)
</b>
</p>
""")

# =========================
# GUARDAR CSV DETALLADO
# =========================
existe = os.path.isfile(CSV_DETALLADO)
with open(CSV_DETALLADO, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=acciones_para_csv[0].keys())
    if not existe:
        writer.writeheader()
    writer.writerows(acciones_para_csv)

# =========================
# GUARDAR CSV TOTALES
# =========================
existe_totales = os.path.isfile(CSV_TOTALES)
with open(CSV_TOTALES, "a", newline="") as f:
    writer = csv.writer(f)
    if not existe_totales:
        writer.writerow(["fecha", "total_invertido", "total_actual"])
    writer.writerow([fecha_hoy, round(total_invertido, 2), round(total_actual, 2)])

# =========================
# ENVIAR CORREO
# =========================
msg = MIMEMultipart()
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📊 Evaluación diaria del portafolio - {fecha_hoy}"
msg.attach(MIMEText("".join(mensaje), "html"))

with open(CSV_DETALLADO, "rb") as f:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{CSV_DETALLADO}"')
    msg.attach(part)

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Correo enviado correctamente")

