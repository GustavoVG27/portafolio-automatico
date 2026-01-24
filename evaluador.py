import yfinance as yf
import csv
from datetime import datetime, timedelta, timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from portfolio import PORTAFOLIO
import os

# =========================
# ZONA HORARIA PERÚ (UTC-5)
# =========================
PERU_TZ = timezone(timedelta(hours=-5))
fecha_hoy = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

# =========================
# CONFIGURACIÓN DE CORREO
# =========================
CORREO_EMISOR = os.environ.get("EMAIL_USER")
CONTRASENA_APP = os.environ.get("EMAIL_APP_PASSWORD")
CORREO_DESTINO = os.environ.get("EMAIL_TO")

if not CORREO_EMISOR or not CONTRASENA_APP or not CORREO_DESTINO:
    raise ValueError("❌ Faltan variables de entorno del correo")

# =========================
# VARIABLES GENERALES
# =========================
total_invertido = 0.0
total_actual = 0.0

archivo_csv = "historial_portafolio.csv"

# =========================
# MENSAJE DEL CORREO
# =========================
mensaje = []
mensaje.append("📊EVALUACIÓN DIARIA DEL PORTAFOLIO\n\n")

# =========================
# EVALUAR CADA ACTIVO
# =========================
for ticker, datos in PORTAFOLIO.items():
    accion = yf.Ticker(ticker)
    hist = accion.history(period="1d")

    if hist.empty:
        mensaje.append(f"⚠️{ticker}: sin datos disponibles\n\n")
        continue

    precio_actual = float(hist["Close"].iloc[-1])
    valor_actual = precio_actual * datos["cantidad"]
    ganancia = valor_actual - datos["invertido"]
    roi = (ganancia / datos["invertido"]) * 100

    total_invertido += datos["invertido"]
    total_actual += valor_actual

    emoji = "🟢" if ganancia > 0 else "🔴" if ganancia < 0 else "⚪"

    mensaje.append(
        f"{emoji}{ticker} ({datos['nombre']})\n"
        f"   📦Cantidad de acciones: {datos['cantidad']}\n"
        f"   💰Inversión inicial: ${datos['invertido']:.2f}\n"
        f"   📈Valor actual de la inversión: ${valor_actual:.2f}\n"
        f"   💵Ganancia: ${ganancia:+.2f} ({roi:+.2f}%)\n\n"
    )

# =========================
# TOTALES
# =========================
resultado = total_actual - total_invertido

mensaje.append(
    "---------------------------\n"
    f"📥TOTAL INVERTIDO: ${total_invertido:.2f}\n"
    f"📤TOTAL ACTUAL: ${total_actual:.2f}\n"
    f"🏁RESULTADO: ${resultado:+.2f}\n"
)

mensaje_final = "".join(mensaje)

# =========================
# GUARDAR CSV (CON FECHA CORRECTA)
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
# ENVIAR CORREO
# =========================
msg = MIMEMultipart()
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📊 Evaluación diaria del portafolio ({fecha_hoy})"

msg.attach(MIMEText(mensaje_final, "plain"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Correo enviado correctamente")

