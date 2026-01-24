import yfinance as yf
import csv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from portfolio import PORTAFOLIO
import os

# =========================
# CONFIGURACIÓN CORREO
# =========================
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_APP_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO")

if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
    raise ValueError("❌ Faltan variables de entorno del correo")

# =========================
# ARCHIVO CSV
# =========================
CSV_FILE = "historial_portafolio.csv"

# =========================
# FECHA
# =========================
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# =========================
# MENSAJE EMAIL
# =========================
mensaje = []
mensaje.append("<h1>📊 Evaluación diaria del portafolio</h1>")

total_invertido = 0.0
total_actual = 0.0
ranking = []

# =========================
# PROCESO POR ACTIVO
# =========================
for ticker, datos in PORTAFOLIO.items():

    accion = yf.Ticker(ticker)
    hist = accion.history(period="1d")

    if hist.empty:
        continue

    precio_cierre = float(hist["Close"].iloc[-1])
    cantidad = datos["cantidad"]
    invertido = datos["invertido"]

    valor_actual = precio_cierre * cantidad
    ganancia = valor_actual - invertido
    ganancia_pct = (ganancia / invertido) * 100 if invertido > 0 else 0

    total_invertido += invertido
    total_actual += valor_actual
    ranking.append((ticker, ganancia_pct))

    color = "green" if ganancia >= 0 else "red"

    # ----- BLOQUE EMAIL -----
    mensaje.append(f"""
    <p>
    <b>{ticker} ({datos['nombre']})</b><br>
    📦 Cantidad de acciones: {cantidad}<br>
    💰 Inversión inicial: ${invertido:.2f}<br>
    📈 Valor actual: ${valor_actual:.2f}<br>
    💵 Ganancia:
    <b style="color:{color};">
    ${ganancia:+.2f} ({ganancia_pct:+.2f}%)
    </b>
    </p>
    """)

    # ----- GUARDAR CSV (ACCION x ACCION) -----
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            fecha_hoy,
            ticker,
            datos["nombre"],
            cantidad,
            round(invertido, 2),
            round(precio_cierre, 2),
            round(valor_actual, 2),
            round(ganancia, 2),
            round(ganancia_pct, 2)
        ])

# =========================
# RESUMEN GENERAL
# =========================
resultado = total_actual - total_invertido
resultado_pct = (resultado / total_invertido) * 100 if total_invertido > 0 else 0

mensaje.append(f"""
<hr>
<h2>📌 Resumen general</h2>
💰 Total invertido: ${total_invertido:.2f}<br>
📈 Valor actual: ${total_actual:.2f}<br>
💵 Resultado:
<b style="color:{'green' if resultado >= 0 else 'red'};">
${resultado:+.2f} ({resultado_pct:+.2f}%)
</b>
""")

# =========================
# RANKING
# =========================
ranking.sort(key=lambda x: x[1], reverse=True)

mensaj








