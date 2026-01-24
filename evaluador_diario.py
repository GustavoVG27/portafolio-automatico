import yfinance as yf
import csv
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from portfolio import PORTAFOLIO
from analitica import (
    comparacion_vs_ayer,
    ranking_portafolio,
    alertas_diarias,
    comentario_analista
)

# =========================
# CONFIGURACIÓN CORREO
# =========================
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_APP_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO")

fecha_hoy = datetime.now().strftime("%Y-%m-%d")
archivo_csv = "historial_portafolio.csv"

SECTORES = {
    "🧠 TECNOLOGÍA": ["NVDA", "PANW", "UBER", "TSLA"],
    "🏥 SALUD": ["VHT"],
    "💰 DIVIDENDOS": ["JEPI"],
    "📈 S&P 500 / ÍNDICES": ["CSPX.L"],
    "⚡ ENERGÍA": ["URA"]
}

total_invertido = 0
total_actual = 0
resultados = []

mensaje = ["<h1>📊 Evaluación diaria del portafolio</h1>"]

# =========================
# EVALUAR ACTIVOS
# =========================
for sector, tickers in SECTORES.items():
    mensaje.append(f"<h2>{sector}</h2>")

    for ticker in tickers:
        datos = PORTAFOLIO[ticker]
        hist = yf.Ticker(ticker).history(period="1d")

        if hist.empty:
            continue

        precio = float(hist["Close"].iloc[-1])
        valor = precio * datos["cantidad"]
        ganancia = valor - datos["invertido"]
        roi = (ganancia / datos["invertido"]) * 100

        total_invertido += datos["invertido"]
        total_actual += valor

        resultados.append({
            "ticker": ticker,
            "roi": roi
        })

        color = "green" if roi > 0 else "red" if roi < 0 else "black"

        mensaje.append(f"""
        <p>
        <b>{ticker} ({datos['nombre']})</b><br>
        Valor actual: ${valor:.2f}<br>
        Ganancia: <b style="color:{color}">
        ${ganancia:+.2f} ({roi:+.2f}%)
        </b>
        </p>
        """)

# =========================
# GUARDAR CSV
# =========================
existe = os.path.isfile(archivo_csv)
with open(archivo_csv, "a", newline="") as f:
    writer = csv.writer(f)
    if not existe:
        writer.writerow(["fecha", "total_invertido", "total_actual", "resultado"])
    writer.writerow([
        fecha_hoy,
        round(total_invertido, 2),
        round(total_actual, 2),
        round(total_actual - total_invertido, 2)
    ])

# =========================
# ANALÍTICA
# =========================
comparacion = comparacion_vs_ayer(total_actual)
ranking = ranking_portafolio(resultados)
alertas = alertas_diarias(comparacion, ranking)
comentario = comentario_analista(comparacion, ranking)

mensaje.append("<hr><h2>📊 Comparación vs ayer</h2>")
if comparacion:
    mensaje.append(
        f"Ayer: ${comparacion['ayer']:.2f}<br>"
        f"Hoy: ${comparacion['hoy']:.2f}<br>"
        f"Variación: ${comparacion['diff']:+.2f} "
        f"({comparacion['pct']:+.2f}%)"
    )

mensaje.append("<hr><h2>🏆 Ranking</h2>")
for i, r in enumerate(ranking, start=1):
    mensaje.append(f"{i}️⃣ {r['ticker']} ({r['roi']:+.2f}%)<br>")

if alertas:
    mensaje.append("<hr><h2>🔔 Alertas</h2>")
    for a in alertas:
        mensaje.append(f"{a}<br>")

mensaje.append("<hr><h2>🧠 Comentario del analista</h2>")
mensaje.append(f"<p>{comentario}</p>")

mensaje_final = "".join(mensaje)

# =========================
# ENVIAR CORREO
# =========================
msg = MIMEMultipart()
msg["From"] = EMAIL_USER
msg["To"] = EMAIL_TO
msg["Subject"] = f"📊 Portafolio Diario - {fecha_hoy}"
msg.attach(MIMEText(mensaje_final, "html"))

with smtplib.SMTP("smtp.gmail.com", 587) as s:
    s.starttls()
    s.login(EMAIL_USER, EMAIL_PASS)
    s.send_message(msg)

print("📧 Correo diario enviado")

