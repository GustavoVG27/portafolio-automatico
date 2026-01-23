import yfinance as yf
import csv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from portfolio import PORTAFOLIO
import os  # ✅ IMPORT CORREGIDO

# =========================
# CONFIGURACIÓN DE CORREO (VARIABLES DE ENTORNO)
# =========================
CORREO_EMISOR = os.environ.get("EMAIL_USER")
CONTRASENA_APP = os.environ.get("EMAIL_APP_PASSWORD")
CORREO_DESTINO = os.environ.get("EMAIL_TO")

# Validación básica
if not CORREO_EMISOR or not CONTRASENA_APP or not CORREO_DESTINO:
    raise ValueError("❌ Faltan variables de entorno para el correo")

# =========================
# VARIABLES GENERALES
# =========================
total_invertido = 0.0
total_actual = 0.0
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

archivo_csv = "historial_portafolio.csv"

mensaje_completo = []
mensaje_completo.append(f"📊 EVALUACIÓN DIARIA DEL PORTAFOLIO ({fecha_hoy})\n")
print(f"📊 EVALUACIÓN DIARIA ({fecha_hoy})\n")

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
        f"   📦 Cantidad: {datos['cantidad']}\n"
        f"   💰 Compra: ${datos['precio_compra']:.2f} | Actual: ${precio_actual:.2f}\n"
        f"   💵 Ganancia: ${ganancia:+.2f} ({roi:+.2f}%)\n"
    )

    print(bloque)
    mensaje_completo.append(bloque)

# =========================
# TOTALES
# =========================
resultado = total_actual - total_invertido

mensaje_totales = (
    "---------------------------\n"
    f"📥 TOTAL INVERTIDO: ${total_invertido:.2f}\n"
    f"📤 TOTAL ACTUAL:   ${total_actual:.2f}\n"
    f"🏁 RESULTADO:      ${resultado:+.2f}\n"
)

print(mensaje_totales)
mensaje_completo.append(mensaje_totales)

mensaje_final = "\n".join(mensaje_completo)

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
# ENVIAR CORREO
# =========================
msg = MIMEMultipart()
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📊 Portafolio {fecha_hoy}"

msg.attach(MIMEText(mensaje_final, "plain"))

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(CORREO_EMISOR, CONTRASENA_APP)
        server.send_message(msg)
    print("📧 Correo enviado correctamente")
except Exception as e:
    print("❌ Error al enviar correo:", e)

