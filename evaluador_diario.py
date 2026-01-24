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
# ALERTAS
# =========================
UMBRAL_ALERTA = 3  # %
alertas = []

# =========================
# VARIABLES
# =========================
total_invertido = 0.0
total_actual = 0.0
ranking = []
archivo_csv = "historial_portafolio.csv"

# =========================
# MENSAJE HTML
# =========================
mensaje = []
mensaje.append("<h1>📊 Evaluación diaria del portafolio</h1>")

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

        precio_actual = float(hist["Close"].iloc[-1])
        valor_actual = precio_actual * datos["cantidad"]
        ganancia = valor_actual - datos["invertido"]
        roi = (ganancia / datos["invertido"]) * 100

        total_invertido += datos["invertido"]
        total_actual += valor_actual

        ranking.append((ticker, roi))

        # =========================
        # ALERTAS
        # =========================
        if roi >= UMBRAL_ALERTA:
            alertas.append(f"🟢 <b>{ticker}</b> sube fuerte <b>+{roi:.2f}%</b>")
        elif roi <= -UMBRAL_ALERTA:
            alertas.append(f"🔴 <b>{ticker}</b> cae fuerte <b>{roi:.2f}%</b>")

        color = "green" if roi >= 0 else "red"

        # =========================
        # BLOQUE DEL ACTIVO EN EL CORREO
        # =========================
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

        # =========================
        # GUARDAR CSV POR ACTIVO
        # =========================
        archivo_existe = os.path.isfile(archivo_csv)

        with open(archivo_csv, "a", newline="", encoding="utf-8") as f:
            fieldnames = [
                "fecha",
                "ticker",
                "sector",
                "cantidad",
                "inversion_inicial",
                "precio_actual",
                "valor_actual",
                "ganancia_usd",
                "ganancia_pct"
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not archivo_existe:
                writer.writeheader()

            writer.writerow({
                "fecha": fecha_hoy,
                "ticker": ticker,
                "sector": sector,
                "cantidad": round(datos["cantidad"], 6),
                "inversion_inicial": round(datos["invertido"], 2),
                "precio_actual": round(precio_actual, 2),
                "valor_actual": round(valor_actual, 2),
                "ganancia_usd": round(ganancia, 2),
                "ganancia_pct": round(roi, 2)
            })

# =========================
# ALERTAS DEL DÍA
# =========================
if alertas:
    mensaje.append("""
    <hr>
    <h2 style="color:red;">🚨 ALERTAS DEL DÍA</h2>
    <ul>
    """)
    for alerta in alertas:
        mensaje.append(f"<li>{alerta}</li>")
    mensaje.append("</ul>")

# =========================
# RANKING
# =========================
ranking.sort(key=lambda x: x[1], reverse=True)

mensaje.append("<hr><h2>🏆 Ranking del día</h2>")
for i, (ticker, roi) in enumerate(ranking, 1):
    mensaje.append(f"{i}️⃣ {ticker} ({roi:+.2f}%)<br>")

# =========================
# COMENTARIO ANALISTA
# =========================
mejor = ranking[0]

mensaje.append(f"""
<hr>
<h2>🧠 Comentario del analista</h2>
El portafolio muestra un comportamiento general estable.
El activo más destacado de la jornada fue
<b>{mejor[0]}</b>, con una variación de
<b>{mejor[1]:+.2f}%</b>.
""")

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






