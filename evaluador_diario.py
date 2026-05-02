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
# CONFIG
# =========================
CORREO_EMISOR = os.environ.get("EMAIL_USER")
CONTRASENA_APP = os.environ.get("EMAIL_APP_PASSWORD")
CORREO_DESTINO = os.environ.get("EMAIL_TO")

if not CORREO_EMISOR or not CONTRASENA_APP or not CORREO_DESTINO:
    raise ValueError("Faltan variables")

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

# =========================
# ESTILO GENERAL
# =========================
mensaje = ["""
<div style="
font-family:Arial, sans-serif;
background:#f7f9fb;
padding:20px;
">

<h1 style="margin-bottom:10px;">📊 Portafolio</h1>
"""]

acciones_para_csv = []

# =========================
# PROCESO
# =========================
for sector, tickers in SECTORES.items():
    mensaje.append(f"<h2 style='margin-top:25px;'>{sector}</h2>")

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
            alertas.append(f"🟢 {ticker} +{roi:.2f}%")
        elif roi <= -UMBRAL_ALERTA:
            alertas.append(f"🔴 {ticker} {roi:.2f}%")

        # colores
        color = "#16a34a" if roi >= 0 else "#dc2626"
        fondo = "#ffffff"

        # 🔥 BLOQUE HORIZONTAL
        mensaje.append(f"""
        <div style="
        display:flex;
        justify-content:space-between;
        align-items:center;
        background:{fondo};
        padding:12px;
        margin-bottom:8px;
        border-radius:8px;
        border:1px solid #e5e7eb;
        ">

        <div>
            <div style="font-weight:600;">{ticker}</div>
            <div style="font-size:12px; color:#666;">
                {datos['nombre']}
            </div>
            <div style="font-size:12px;">
                {datos['cantidad']} acciones · ${valor_actual:.2f}
            </div>
        </div>

        <div style="text-align:right;">
            <div style="color:{color}; font-weight:600;">
                {roi:+.2f}%
            </div>
            <div style="font-size:13px; color:{color};">
                ${ganancia:+.2f}
            </div>
        </div>

        </div>
        """)

        acciones_para_csv.append({
            "fecha": fecha_hoy,
            "ticker": ticker,
            "valor_actual": round(valor_actual, 2),
            "roi": round(roi, 2)
        })

# =========================
# RESUMEN ARRIBA
# =========================
ganancia_total = total_actual - total_invertido
porcentaje_total = (ganancia_total / total_invertido) * 100 if total_invertido != 0 else 0
color_total = "#16a34a" if ganancia_total >= 0 else "#dc2626"

mensaje.insert(1, f"""
<div style="
background:white;
padding:15px;
border-radius:10px;
margin-bottom:15px;
border:1px solid #e5e7eb;
">

💰 ${total_invertido:.2f} → 📈 ${total_actual:.2f}

<div style="margin-top:5px; font-size:18px; font-weight:700; color:{color_total};">
{ganancia_total:+.2f} ({porcentaje_total:+.2f}%)
</div>

</div>
""")

# =========================
# ALERTAS
# =========================
if alertas:
    mensaje.append("<hr><h3>🚨 Alertas</h3>")
    for a in alertas:
        mensaje.append(f"{a}<br>")

# =========================
# RANKING
# =========================
ranking.sort(key=lambda x: x[1], reverse=True)
mensaje.append("<hr><h3>🏆 Ranking</h3>")
for i, (t, r) in enumerate(ranking, 1):
    mensaje.append(f"{i}. {t} ({r:+.2f}%)<br>")

mensaje.append("</div>")

# =========================
# EMAIL
# =========================
msg = MIMEMultipart()
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📊 Portafolio - {fecha_hoy}"

msg.attach(MIMEText("".join(mensaje), "html"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Enviado")
