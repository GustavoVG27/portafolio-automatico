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
# CONFIGURACIÓN
# =========================
CORREO_EMISOR = os.environ.get("EMAIL_USER")
CONTRASENA_APP = os.environ.get("EMAIL_APP_PASSWORD")
CORREO_DESTINO = os.environ.get("EMAIL_TO")

if not CORREO_EMISOR or not CONTRASENA_APP or not CORREO_DESTINO:
    raise ValueError("❌ Faltan variables de entorno")

fecha_hoy = datetime.now().strftime("%Y-%m-%d")

CSV_DETALLADO = "historial_portafolio_detallado.csv"
CSV_TOTALES = "historial_portafolio_totales.csv"

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
# PROCESO
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

        ranking.append((ticker, roi, valor_actual))

        if roi >= UMBRAL_ALERTA:
            alertas.append(f"🟢 <b>{ticker}</b> sube fuerte +{roi:.2f}%")
        elif roi <= -UMBRAL_ALERTA:
            alertas.append(f"🔴 <b>{ticker}</b> cae fuerte {roi:.2f}%")

        color = "green" if roi >= 0 else "red"

        mensaje.append(f"""
        <p>
        <b>{ticker} ({datos['nombre']})</b><br>
        💰 ${valor_actual:.2f} |
        <b style="color:{color};">
        {roi:+.2f}%
        </b>
        </p>
        """)

        acciones_para_csv.append({
            "fecha": fecha_hoy,
            "ticker": ticker,
            "valor_actual": round(valor_actual, 2),
            "roi": round(roi, 2)
        })

# =========================
# RESUMEN TOTAL (CARD)
# =========================
ganancia_total = total_actual - total_invertido
porcentaje_total = (ganancia_total / total_invertido) * 100 if total_invertido != 0 else 0
color_total = "green" if ganancia_total >= 0 else "red"

if porcentaje_total > 5:
    estado = "🚀 Excelente rendimiento"
elif porcentaje_total > 0:
    estado = "📈 Crecimiento moderado"
else:
    estado = "⚠️ Semana negativa"

mensaje.insert(1, f"""
<div style="background:#f5f7fa;padding:15px;border-radius:10px;">
<h2>💼 Resumen general</h2>

💰 ${total_invertido:.2f} → 📈 ${total_actual:.2f}<br>

<b style="color:{color_total};font-size:18px;">
{ganancia_total:+.2f} ({porcentaje_total:+.2f}%)
</b>

<p>{estado}</p>
</div>
""")

# =========================
# ALERTAS
# =========================
if alertas:
    mensaje.append("<hr><h2>🚨 Alertas</h2>")
    for a in alertas:
        mensaje.append(f"<p>{a}</p>")

# =========================
# RANKING + MEJOR/PEOR
# =========================
ranking.sort(key=lambda x: x[1], reverse=True)

mejor = ranking[0]
peor = ranking[-1]

mensaje.append("<hr><h2>🏆 Ranking</h2>")
for i, (t, r, _) in enumerate(ranking, 1):
    mensaje.append(f"{i}. {t} ({r:+.2f}%)<br>")

mensaje.append(f"""
<hr>
<h2>🧠 Análisis rápido</h2>

Mejor activo: <b>{mejor[0]}</b> ({mejor[1]:+.2f}%)<br>
Peor activo: <b>{peor[0]}</b> ({peor[1]:+.2f}%)
""")

# =========================
# ALERTA DE CONCENTRACIÓN
# =========================
for t, _, val in ranking:
    peso = val / total_actual * 100
    if peso > 40:
        mensaje.append(f"<p>⚠️ {t} representa {peso:.1f}% del portafolio</p>")

# =========================
# GUARDAR CSV
# =========================
existe = os.path.isfile(CSV_DETALLADO)
with open(CSV_DETALLADO, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=acciones_para_csv[0].keys())
    if not existe:
        writer.writeheader()
    writer.writerows(acciones_para_csv)

# =========================
# EMAIL
# =========================
msg = MIMEMultipart()
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📊 Evaluación del portafolio - {fecha_hoy}"

msg.attach(MIMEText("".join(mensaje), "html"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Correo enviado")

