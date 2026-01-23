import yfinance as yf
import csv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from portfolio import PORTAFOLIO

# =========================
# CONFIGURACIÓN DE CORREO
# =========================
CORREO_EMISOR = os.environ.get("EMAIL_USER")         # Tu correo emisor
CONTRASENA_APP = os.environ.get("EMAIL_APP_PASSWORD") # Contraseña específica de la app
CORREO_DESTINO = os.environ.get("EMAIL_TO")         # Correo destino

# =========================
# VARIABLES GENERALES
# =========================
total_invertido = 0
total_actual = 0
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# CSV (solo técnico, se queda en la PC)
archivo_csv = "historial_portafolio.csv"

# Mensaje completo (para correo y consola)
mensaje_completo = []
mensaje_completo.append("📊 EVALUACIÓN DIARIA DEL PORTAFOLIO\n")
print("📊 EVALUACIÓN DIARIA\n")

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

    # Precio actual de la acción
    precio_actual = float(hist["Close"].iloc[-1])
    # Valor de mi inversión actual
    valor_inversion = precio_actual * datos["cantidad"]
    # Ganancia de mi inversión
    ganancia = valor_inversion - datos["invertido"]
    roi = (ganancia / datos["invertido"]) * 100

    total_invertido += datos["invertido"]
    total_actual += valor_inversion

    # Emoji según rendimiento
    if roi > 0:
        emoji = "🟢"
    elif roi < 0:
        emoji = "🔴"
    else:
        emoji = "⚪"

    bloque = (
        f"{emoji} {ticker} ({datos['nombre']})\n"
        f"   📦 Cantidad de acciones: {datos['cantidad']}\n"
        f"   💰 Inversión inicial: ${datos['invertido']:.2f}\n"
        f"   📈 Valor actual de la inversión: ${valor_inversion:.2f}\n"
        f"   💵 Ganancia: ${ganancia:+.2f} ({roi:+.2f}%)\n"
    )

    print(bloque)
    mensaje_completo.append(bloque)

# =========================
# TOTALES DEL PORTAFOLIO
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
# GUARDAR CSV (FORMATO LIMPIO)
# =========================
try:
    existe = True
    with open(archivo_csv, "r"):
        pass
except FileNotFoundError:
    existe = False

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

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(CORREO_EMISOR, CONTRASENA_APP)
        server.send_message(msg)
    print("📧 Correo enviado correctamente")
except Exception as e:
    print("❌ Error al enviar correo:", e)

