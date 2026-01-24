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
    raise ValueError("❌ Faltan variables de entorno del correo")

# =========================
# VARIABLES
# =========================
total_invertido = 0.0
total_actual = 0.0
fecha_hoy = datetime.utcnow().strftime("%Y-%m-%d")

archivo_csv = "historial_portafolio.csv"

mensaje = []
mensaje.append(f"📊 EVALUACIÓN DIARIA DEL PORTAFOLIO ({fecha_hoy})\n")

# =========================
# EVALUAR ACTIVOS
# =========================
for ticker, datos in PORTAFOLIO.items():
    accion = yf.Ticker(ticker)
    hist = accion.history(period="1d")

    if hist.empty:
        mensaje.append(f"⚠️ {ticker}: sin datos disponibles\n")
        continue

    precio_actual = float(hist["Close"].iloc[-1])
    valor_actual = precio_actual * datos["cantidad"]
    ganancia = valor_actual - datos["invertido"]
    roi = (ganancia / datos["invertido"]) * 100

    total_invertido += datos["invertido"]
    total_actual += valor_actual

    emoji = "🟢" if roi > 0 else "🔴" if roi < 0 else "⚪"

    mensaje.append(
        f"{emoji} {ticker} ({datos['nombre']})\n"
        f"   📦 Cantidad: {datos['cantidad']}\n"
        f"   💰 Compra: ${datos['precio_compra']:.2f} | Actual: ${precio_actual:.2f}\n"
        f"   💵 Ganancia: ${ganancia:+.2f} ({roi:+.2f}%)\n"
    )

# =========================
# TOTALES
# =========================
resultado = total_actual - total_invertido

mensaje.append(
    "---------------------------\n"
    f"📥 TOTAL INVERTIDO: ${total_invertido:.2f}\n"
    f"📤 TOTAL ACTUAL:   ${total_actual:.2f}\n"
    f"🏁 RESULTADO:      ${resultado:+.2f}\n"
)

mensaje_final = "\n".join(mensaje)

# =========================
# GUARDAR CSV (LOCAL DEL RUN)
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
        round(resultado, 2)
    ])

# =========================
# ENVIAR CORREO
# =========================
msg = MIMEMultipart()
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📊 Portafolio {fecha_hoy}"

msg.attach(MIMEText(mensaje_final, "plain"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Correo enviado correctamente")
