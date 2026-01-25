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

        # ALERTAS
        if roi >= UMBRAL_ALERTA:
            alertas.append(f"🟢 <b>{ticker}</b> sube fuerte <b>+{roi:.2f}%</b>")
        elif roi <= -UMBRAL_ALERTA:
            alertas.append(f"🔴 <b>{ticker}</b> cae fuerte <b>{roi:.2f}%</b>")

        color = "green" if roi >= 0 else "red"

        # BLOQUE COMPLETO DEL ACTIVO
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
# 🚨 ALERTAS DEL DÍA
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
# COMPARACIÓN VS AYER
# =========================
ayer = None
if os.path.isfile(archivo_csv):
    with open(archivo_csv, "r") as f:
        rows = list(csv.DictReader(f))
        if rows:
            # Sumar valor_actual del último día registrado
            ultimo_dia = rows[-1]["fecha"]
            ayer_total = sum(float(r["valor_actual"]) for r in rows if r["fecha"] == ultimo_dia)
            ayer = ayer_total

mensaje.append("<hr><h2>📊 Comparación vs ayer</h2>")
if ayer:
    variacion = total_actual - ayer
    porcentaje = (variacion / ayer) * 100
    mensaje.append(f"""
    Ayer: ${ayer:.2f}<br>
    Hoy: ${total_actual:.2f}<br>
    Variación: ${variacion:+.2f} ({porcentaje:+.2f}%)
    """)
else:
    mensaje.append("No hay datos de ayer.")

# =========================
# RANKING
# =========================
ranking.sort(key=lambda x: x[1], reverse=True)

mensaje.append("<hr><h2>🏆 Ranking</h2>")
for i, (ticker, roi) in enumerate(ranking, 1):
    mensaje.append(f"{i}️⃣ {ticker} ({roi:+.2f}%)<br>")

# =========================
# COMENTARIO ANALISTA
# =========================
mejor = ranking[0]
mensaje.append(f"""
<hr>
<h2>🧠 Comentario del analista</h2>
El portafolio muestra un desempeño estable.
El activo más destacado de la jornada fue
<b>{mejor[0]}</b>, con una variación de
<b>{mejor[1]:+.2f}%</b>.
""")

# =========================
# GUARDAR CSV DETALLADO
# =========================
archivo_existe = os.path.isfile(archivo_csv)

with open(archivo_csv, "a", newline="") as f:
    writer = csv.writer(f)
    if not archivo_existe:
        writer.writerow([
            "fecha", "ticker", "nombre", "cantidad",
            "invertido", "valor_actual", "ganancia", "roi"
        ])

    for sector, tickers in SECTORES.items():
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

            writer.writerow([
                fecha_hoy,
                ticker,
                datos["nombre"],
                datos["cantidad"],
                round(datos["invertido"], 2),
                round(valor_actual, 2),
                round(ganancia, 2),
                round(roi, 2)
            ])

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





