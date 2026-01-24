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
# FECHA (SOLO FECHA)
# =========================
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# =========================
# DEFINICIÓN DE SECTORES
# =========================
SECTORES = {
    "🧠 TECNOLOGÍA": ["NVDA", "PANW", "UBER", "TSLA"],
    "🏥 SALUD": ["VHT"],
    "💰 DIVIDENDOS": ["JEPI"],
    "📈 S&P 500 / ÍNDICES": ["CSPX.L"],
    "⚡ ENERGÍA / MATERIAS PRIMAS": ["URA"]
}

# =========================
# VARIABLES GENERALES
# =========================
total_invertido = 0.0
total_actual = 0.0
archivo_csv = "historial_portafolio.csv"

# =========================
# INICIO MENSAJE HTML
# =========================
mensaje = []
mensaje.append("<h1>📊 EVALUACIÓN DIARIA DEL PORTAFOLIO</h1>")

# =========================
# PROCESAR POR SECTORES
# =========================
for sector, tickers in SECTORES.items():
    mensaje.append(f"<h2>📌 {sector}</h2>")

    for ticker in tickers:
        datos = PORTAFOLIO[ticker]
        accion = yf.Ticker(ticker)
        hist = accion.history(period="1d")

        if hist.empty:
            mensaje.append(f"<p>⚠️ {ticker}: sin datos disponibles</p>")
            continue

        precio_actual = float(hist["Close"].iloc[-1])
        valor_actual = precio_actual * datos["cantidad"]
        ganancia = valor_actual - datos["invertido"]
        roi = (ganancia / datos["invertido"]) * 100

        total_invertido += datos["invertido"]
        total_actual += valor_actual

        if roi > 0:
            emoji = "🟢"
            color = "green"
        elif roi < 0:
            emoji = "🔴"
            color = "red"
        else:
            emoji = "⚪"
            color = "black"

        bloque = f"""
        <p>
        <b>{emoji} {ticker} ({datos['nombre']})</b><br>
        📦 Cantidad de acciones: {datos['cantidad']}<br>
        💰 Inversión inicial: ${datos['invertido']:.2f}<br>
        📈 Valor actual: ${valor_actual:.2f}<br>
        💵 Ganancia: <b style="color:{color};">
            ${ganancia:+.2f} ({roi:+.2f}%)
        </b>
        </p>
        """

        mensaje.append(bloque)

# =========================
# TOTALES
# =========================
resultado = total_actual - total_invertido

mensaje.append(f"""
<hr>
<h2>📊 RESUMEN GENERAL</h2>
<p>
<b>📥 Total invertido:</b> ${total_invertido:.2f}<br>
<b>📤 Total actual:</b> ${total_actual:.2f}<br>
<b>🏁 Resultado:</b> ${resultado:+.2f}
</p>
""")

mensaje_final = "".join(mensaje)

# =========================
# GUARDAR CSV
# =========================
archivo_existe = os.path.isfile(archivo_csv)

with open(archivo_csv, "a", newline="") as f:
    writer = csv.writer(f)
    if not archivo_existe:
        writer.writerow(["fecha", "total_invertido", "total_actual", "resultado"])
    writer.writerow([
        fecha_hoy,
        round(total_invertido, 2),
        round(total_actual, 2),
        round(resultado, 2)
    ])

# =========================
# ENVIAR CORREO (HTML)
# =========================
msg = MIMEMultipart()
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📊 Portafolio Diario - {fecha_hoy}"

msg.attach(MIMEText(mensaje_final, "html"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Correo enviado correctamente")

