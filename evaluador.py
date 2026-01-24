import yfinance as yf
import csv
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from portfolio import PORTAFOLIO

# =========================
# FECHA Y HORA
# =========================
fecha_hoy = datetime.now().strftime("%d/%m/%Y")
hora_hoy = datetime.now().strftime("%H:%M")

# =========================
# CONFIGURACIÓN DE CORREO
# =========================
CORREO_EMISOR = os.environ.get("EMAIL_USER")
CONTRASENA_APP = os.environ.get("EMAIL_APP_PASSWORD")
CORREO_DESTINO = os.environ.get("EMAIL_TO")

# =========================
# VARIABLES GENERALES
# =========================
total_invertido = 0
total_actual = 0

archivo_csv = "historial_portafolio.csv"

mensaje_completo = []
mensaje_completo.append(
    f"📊 EVALUACIÓN DIARIA DEL PORTAFOLIO\n"
    f"📅 Fecha: {fecha_hoy}\n"
    f"⏰ Hora: {hora_hoy}\n\n"
)

print("📊 EVALUACIÓN DIARIA DEL PORTAFOLIO")
print(f"📅 Fecha: {fecha_hoy} | ⏰ Hora: {hora_hoy}\n")

# =========================
# EVALUAR CADA ACTIVO
# =========================
for ticker, datos in PORTAFOLIO.items():
    accion = yf.Ticker(ticker)
    hist = accion.history(period="1d")

    if hist.empty:
        linea = f"⚠️ {ticker}: sin datos disponibles\n"
        print(linea)
        mensaje_completo.append(linea)
        continue

    precio_actual = float(hist["Close"].iloc[-1])
    valor_inversion = precio_actual * datos["cantidad"]
    ganancia = valor_inversion - datos["invertido"]
    roi = (ganancia / datos["invertido"]) * 100

    total_invertido += datos["invertido"]
    total_actual += valor_inversion

    if roi > 0:
        emoji = "🟢"
    elif roi < 0:
        emoji = "🔴"
    else:
        emoji = "⚪"

    bloque = (
        f"{emoji} {ticker} ({datos['nombre']})\n"
        f"   📦 Acciones: {datos['cantidad']}\n"
        f"   💰 Inversión inicial: ${datos['invertido']:.2f}\n"
        f"   📈 Valor actual: ${valor_inversion:.2f}\n"
        f"   💵 Ganancia: ${ganancia:+.2f} ({roi:+.2f}%)\n\n"
    )

    print(bloque)
    mensaje_completo.append(bloque)

# =========================
# TOTALES
# =========================
resultado = total_actual - total_invertido

mensaje_totales = (
    "-----------------------------\n"
    f"📥 TOTAL INVERTIDO: ${total_invertido:.2f}\n"
    f"📤 TOTAL ACTUAL:   ${total_actual:.2f}\n"
    f"🏁 RESULTADO:      ${resultado:+.2f}\n"
)

print(mensaje_totales)
mensaje_completo.append(mensaje_totales)

mensaje_final = "".join(mensaje_completo)

# =========================
# GUARDAR CSV
# =========================
existe = os.path.isfile(archivo_csv)

with open(archivo_csv, "a", newline="") as f:
    writer = csv.writer(f)
    if not existe:
        writer.writerow(["fecha", "hora", "total_invertido", "total_actual", "resultado"])
    writer.writerow([
        fecha_hoy,
        hora_hoy,
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
msg["Subject"] = f"📊 Portafolio – {fecha_hoy} {hora_hoy}"

msg.attach(MIMEText(mensaje_final, "plain"))

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(CORREO_EMISOR, CONTRASENA_APP)
        server.send_message(msg)
    print("📧 Correo enviado correctamente")
except Exception as e:
    print("❌ Error al enviar correo:", e)



