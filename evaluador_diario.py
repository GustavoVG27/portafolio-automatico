import yfinance as yf
import csv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
# SECTORES
# =========================
SECTORES = {
    "🧠 TECNOLOGÍA": ["NVDA", "PANW", "UBER", "TSLA"],
    "🏥 SALUD": ["VHT"],
    "💰 DIVIDENDOS": ["JEPI"],
    "📈 S&P 500 / ÍNDICES": ["CSPX.L"],
    "⚡ ENERGÍA": ["URA"]
}

# =========================
# CONFIG ALERTAS
# =========================
UMBRAL_ALERTA = 3  # %

# =========================
# ARCHIVO CSV
# =========================
ARCHIVO_CSV = "historial_detallado.csv"
csv_existe = os.path.isfile(ARCHIVO_CSV)

# =========================
# VARIABLES
# =========================
mensaje = []
mensaje.append("<h1>📊 Evaluación diaria del portafolio</h1>")

total_actual_hoy = 0.0
ranking = []
alertas = []

# =========================
# ABRIR CSV
# =========================
with open(ARCHIVO_CSV, "a", newline="") as f:
    writer = csv.writer(f)

    if not csv_existe:
        writer.writerow([
            "fecha", "ticker", "sector", "nombre",
            "cantidad", "inversion_inicial",
            "precio_cierre", "valor_actual",
            "ganancia_usd", "ganancia_pct"
        ])

    # =========================
    # PROCESO POR SECTOR
    # =========================
    for sector, tickers in SECTORES.items():
        mensaje.append(f"<h2>{sector}</h2>")

        for ticker in tickers:
            datos = PORTAFOLIO[ticker]
            accion = yf.Ticker(ticker)
            hist = accion.history(period="1d")

            if hist.empty:
                continue

            precio = float(hist["Close"].iloc[-1])
            valor_actual = precio * datos["cantidad"]
            ganancia = valor_actual - datos["invertido"]
            roi = (ganancia / datos["invertido"]) * 100

            total_actual_hoy += valor_actual
            ranking.append((ticker, roi))

            # ALERTAS
            if roi >= UMBRAL_ALERTA:
                alertas.append(f"🟢 {ticker} sube fuerte (+{roi:.2f}%)")
            elif roi <= -UMBRAL_ALERTA:
                alertas.append(f"🔴 {ticker} cae fuerte ({roi:.2f}%)")

            # GUARDAR CSV (acción x acción)
            writer.writerow([
                fecha_hoy,
                ticker,
                sector,
                datos["nombre"],
                datos["cantidad"],
                round(datos["invertido"], 2),
                round(precio, 2),
                round(valor_actual, 2),
                round(ganancia, 2),
                round(roi, 2)
            ])

            color = "green" if roi >= 0 else "red"

            mensaje.append(f"""
            <p>
            <b>{ticker} ({datos['nombre']})</b><br>
            📦 Cantidad: {datos['cantidad']}<br>
            💰 Inversión inicial: ${datos['invertido']:.2f}<br>
            📈 Valor actual: ${valor_actual:.2f}<br>
            💵 Ganancia:
            <b style="color:{color};">
            ${ganancia:+.2f} ({roi:+.2f}%)
            </b>
            </p>
            """)

# =========================
# 📊 COMPARACIÓN VS AYER
# =========================
ayer_total = 0.0

if csv_existe:
    with open(ARCHIVO_CSV, "r") as f:
        rows = list(csv.DictReader(f))
        fechas = sorted(set(r["fecha"] for r in rows))
        if len(fechas) >= 2:
            ultimo_dia = fechas[-2]
            ayer_total = sum(
                float(r["valor_actual"])
                for r in rows
                if r["fecha"] == ultimo_dia
            )

mensaje.append("<hr><h2>📊 Comparación vs ayer</h2>")

if ayer_total > 0:
    variacion = total_actual_hoy - ayer_total
    pct = (variacion / ayer_total) * 100
    mensaje.append(f"""
    Ayer: ${ayer_total:.2f}<br>
    Hoy: ${total_actual_hoy:.2f}<br>
    Variación: ${variacion:+.2f} ({pct:+.2f}%)
    """)
else:
    mensaje.append("No hay datos suficientes para comparar.")

# =========================
# 🏆 RANKING
# =========================
ranking.sort(key=lambda x: x[1], reverse=True)

mensaje.append("<hr><h2>🏆 Ranking del día</h2>")
for i, (ticker, roi) in enumerate(ranking, 1):
    mensaje.append(f"{i}️⃣ {ticker} ({roi:+.2f}%)<br>")

# =========================
# 🧠 COMENTARIO ANALISTA
# =========================
mejor = ranking[0]

mensaje.append(f"""
<hr>
<h2>🧠 Comentario del analista</h2>
La jornada muestra un comportamiento estable del portafolio.
El activo más destacado fue <b>{mejor[0]}</b>
con una variación de <b>{mejor[1]:+.2f}%</b>.
""")

# =========================
# 🚨 ALERTAS
# =========================
if alertas:
    mensaje.append("<hr><h2 style='color:red;'>🚨 Alertas del día</h2><ul>")
    for a in alertas:
        mensaje.append(f"<li>{a}</li>")
    mensaje.append("</ul>")

# =========================
# ENVIAR CORREO
# =========================
msg = MIMEMultipart()
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📊 Evaluación diaria del portafolio - {fecha_hoy}"
msg.attach(MIMEText("".join(mensaje), "html"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Correo enviado correctamente")








