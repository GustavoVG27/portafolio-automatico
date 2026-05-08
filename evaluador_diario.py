import yfinance as yf
import csv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
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
fecha_legible = datetime.now().strftime("%d de %B de %Y")

# =========================
# ARCHIVOS CSV
# =========================
CSV_DETALLADO = "historial_portafolio_detallado.csv"
CSV_TOTALES = "historial_portafolio_totales.csv"

# =========================
# SECTORES
# =========================
SECTORES = {
    "🧠 TECNOLOGÍA": ["NVDA", "PANW", "UBER"],
    "📈 S&P 500 / ÍNDICES": ["CSPX.L"],
    "🏥 SALUD": ["VHT"],
    "🌎 MERCADOS INTERNACIONALES": ["VXUS"],
    "⚡ ENERGÍA": ["URA"],
    "₿ CRIPTO": ["BTC-USD"]
}

UMBRAL_ALERTA = 3
alertas = []
ranking = []

total_invertido = 0.0
total_actual = 0.0
acciones_para_csv = []
tarjetas_sectores = {}

# =========================
# PROCESO PRINCIPAL
# =========================
for sector, tickers in SECTORES.items():
    tarjetas_sector = []
    for ticker in tickers:
        datos = PORTAFOLIO[ticker]
        hist = yf.Ticker(ticker).history(period="1d")
        if hist.empty:
            continue

        precio = float(hist["Close"].iloc[-1])
        valor_actual = precio * datos["cantidad"]
        ganancia = valor_actual - datos["invertido"]
        roi = (ganancia / datos["invertido"]) * 100

        total_invertido += datos["invertido"]
        total_actual += valor_actual
        ranking.append((ticker, roi))

        if roi >= UMBRAL_ALERTA:
            alertas.append({"ticker": ticker, "roi": roi, "tipo": "up"})
        elif roi <= -UMBRAL_ALERTA:
            alertas.append({"ticker": ticker, "roi": roi, "tipo": "down"})

        tarjetas_sector.append({
            "ticker": ticker,
            "nombre": datos["nombre"],
            "cantidad": datos["cantidad"],
            "invertido": datos["invertido"],
            "valor_actual": valor_actual,
            "ganancia": ganancia,
            "roi": roi,
            "precio": precio,
        })

        acciones_para_csv.append({
            "fecha": fecha_hoy,
            "ticker": ticker,
            "nombre": datos["nombre"],
            "cantidad": datos["cantidad"],
            "invertido": round(datos["invertido"], 2),
            "valor_actual": round(valor_actual, 2),
            "ganancia": round(ganancia, 2),
            "roi": round(roi, 2)
        })

    if tarjetas_sector:
        tarjetas_sectores[sector] = tarjetas_sector

# =========================
# DATOS HISTÓRICOS (últimos 5 días)
# =========================
historial_5_dias = []
if os.path.isfile(CSV_TOTALES):
    with open(CSV_TOTALES, "r") as f:
        rows = list(csv.DictReader(f))
        historial_5_dias = rows[-5:] if len(rows) >= 5 else rows

ayer_total = None
if historial_5_dias:
    ayer_total = float(historial_5_dias[-1]["total_actual"])

# =========================
# RANKING
# =========================
ranking.sort(key=lambda x: x[1], reverse=True)
mejor = ranking[0]
peor = ranking[-1]

ganancia_total = total_actual - total_invertido
porcentaje_total = (ganancia_total / total_invertido) * 100 if total_invertido != 0 else 0

variacion_dia = None
porcentaje_dia = None
if ayer_total:
    variacion_dia = total_actual - ayer_total
    porcentaje_dia = (variacion_dia / ayer_total) * 100

# =========================
# HELPER: BARRA DE ROI
# =========================
def barra_roi(roi, max_val=30):
    filled = min(int(abs(roi) / max_val * 10), 10)
    empty = 10 - filled
    color = "#22c55e" if roi >= 0 else "#ef4444"
    bar = "█" * filled + "░" * empty
    return f'<span style="font-family:monospace;color:{color};letter-spacing:1px;">{bar}</span>'

# =========================
# COMENTARIO DEL ANALISTA
# =========================
def generar_comentario():
    estado = "positivo" if porcentaje_total >= 0 else "negativo"
    estado_dia = ""
    if variacion_dia is not None:
        if variacion_dia >= 0:
            estado_dia = f"En la sesión de hoy, el portafolio <b>ganó ${variacion_dia:+.2f}</b> respecto a ayer (+{porcentaje_dia:.2f}%), mostrando momentum alcista."
        else:
            estado_dia = f"En la sesión de hoy, el portafolio <b>perdió ${abs(variacion_dia):.2f}</b> respecto a ayer ({porcentaje_dia:.2f}%), con presión bajista."

    accion_mejor = "Considera revisar niveles de toma de ganancias." if mejor[1] > 10 else "El activo mantiene buen desempeño relativo."
    accion_peor = "Monitorear de cerca ante posible continuación de caída." if peor[1] < -5 else "La corrección parece moderada por ahora."

    return f"""
    El portafolio se encuentra en territorio <b>{estado}</b> con un ROI acumulado de <b>{porcentaje_total:+.2f}%</b>.
    {estado_dia}<br><br>
    El activo estrella del día fue <b>{mejor[0]}</b> con <b>{mejor[1]:+.2f}%</b>. {accion_mejor}
    El activo con mayor presión fue <b>{peor[0]}</b> con <b>{peor[1]:+.2f}%</b>. {accion_peor}
    """

# =========================
# CONSTRUCCIÓN DEL HTML
# =========================
def build_email_html():
    # ---- Alertas HTML ----
    alertas_html = ""
    if alertas:
        banners = ""
        for a in alertas:
            if a["tipo"] == "up":
                banners += f"""
                <div style="background:#dcfce7;border-left:6px solid #16a34a;padding:14px 18px;border-radius:8px;margin-bottom:8px;font-family:'Segoe UI',sans-serif;">
                  <span style="font-size:20px;">🚀</span>
                  <b style="color:#15803d;font-size:15px;margin-left:8px;">{a['ticker']}</b>
                  <span style="color:#166534;"> sube fuerte </span>
                  <b style="color:#15803d;font-size:16px;">+{a['roi']:.2f}%</b>
                </div>"""
            else:
                banners += f"""
                <div style="background:#fee2e2;border-left:6px solid #dc2626;padding:14px 18px;border-radius:8px;margin-bottom:8px;font-family:'Segoe UI',sans-serif;">
                  <span style="font-size:20px;">⚠️</span>
                  <b style="color:#b91c1c;font-size:15px;margin-left:8px;">{a['ticker']}</b>
                  <span style="color:#991b1b;"> cae fuerte </span>
                  <b style="color:#b91c1c;font-size:16px;">{a['roi']:.2f}%</b>
                </div>"""

        alertas_html = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
          <tr><td style="padding:0 0 10px 0;">
            <div style="background:#1e1e2e;border-radius:12px;padding:20px 24px;">
              <h2 style="color:#f8fafc;font-family:'Segoe UI',sans-serif;margin:0 0 14px 0;font-size:16px;letter-spacing:1px;text-transform:uppercase;">
                🚨 Alertas del día
              </h2>
              {banners}
            </div>
          </td></tr>
        </table>"""

    # ---- Tarjetas por sector ----
    sectores_html = ""
    for sector, tarjetas in tarjetas_sectores.items():
        filas = ""
        for t in tarjetas:
            color_roi = "#16a34a" if t["roi"] >= 0 else "#dc2626"
            bg_roi = "#dcfce7" if t["roi"] >= 0 else "#fee2e2"
            flecha = "▲" if t["roi"] >= 0 else "▼"
            filas += f"""
            <tr style="border-bottom:1px solid #f1f5f9;">
              <td style="padding:12px 10px;font-family:'Segoe UI',sans-serif;">
                <b style="font-size:14px;color:#0f172a;">{t['ticker']}</b><br>
                <span style="font-size:11px;color:#64748b;">{t['nombre']}</span>
              </td>
              <td style="padding:12px 10px;text-align:center;font-family:'Segoe UI',sans-serif;color:#334155;font-size:13px;">
                {t['cantidad']}
              </td>
              <td style="padding:12px 10px;text-align:right;font-family:'Segoe UI',sans-serif;color:#334155;font-size:13px;">
                ${t['invertido']:.2f}
              </td>
              <td style="padding:12px 10px;text-align:right;font-family:'Segoe UI',sans-serif;color:#0f172a;font-weight:600;font-size:13px;">
                ${t['valor_actual']:.2f}
              </td>
              <td style="padding:12px 10px;text-align:right;">
                <span style="background:{bg_roi};color:{color_roi};padding:4px 10px;border-radius:20px;font-size:12px;font-weight:700;font-family:'Segoe UI',sans-serif;white-space:nowrap;">
                  {flecha} {abs(t['roi']):.2f}%
                </span>
              </td>
              <td style="padding:12px 10px;font-family:monospace;font-size:12px;color:{color_roi};">
                {barra_roi(t['roi'])}
              </td>
            </tr>"""

        sectores_html += f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">
          <tr><td>
            <div style="background:#1e293b;padding:12px 16px;">
              <span style="color:#f8fafc;font-family:'Segoe UI',sans-serif;font-size:14px;font-weight:700;letter-spacing:0.5px;">{sector}</span>
            </div>
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;">
              <thead>
                <tr style="background:#f8fafc;">
                  <th style="padding:10px;text-align:left;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Activo</th>
                  <th style="padding:10px;text-align:center;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Cantidad</th>
                  <th style="padding:10px;text-align:right;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Invertido</th>
                  <th style="padding:10px;text-align:right;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Valor actual</th>
                  <th style="padding:10px;text-align:right;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">ROI</th>
                  <th style="padding:10px;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Tendencia</th>
                </tr>
              </thead>
              <tbody>{filas}</tbody>
            </table>
          </td></tr>
        </table>"""

    # ---- Historial 5 días ----
    historial_html = ""
    if historial_5_dias:
        filas_hist = ""
        for row in historial_5_dias:
            inv = float(row["total_invertido"])
            act = float(row["total_actual"])
            gan = act - inv
            pct = (gan / inv * 100) if inv else 0
            color = "#16a34a" if gan >= 0 else "#dc2626"
            filas_hist += f"""
            <tr style="border-bottom:1px solid #f1f5f9;">
              <td style="padding:10px 12px;font-family:'Segoe UI',sans-serif;font-size:13px;color:#64748b;">{row['fecha']}</td>
              <td style="padding:10px 12px;text-align:right;font-family:'Segoe UI',sans-serif;font-size:13px;color:#334155;">${inv:.2f}</td>
              <td style="padding:10px 12px;text-align:right;font-family:'Segoe UI',sans-serif;font-size:13px;font-weight:600;color:#0f172a;">${act:.2f}</td>
              <td style="padding:10px 12px;text-align:right;font-family:'Segoe UI',sans-serif;font-size:13px;font-weight:700;color:{color};">{pct:+.2f}%</td>
            </tr>"""

        historial_html = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">
          <tr><td>
            <div style="background:#1e293b;padding:12px 16px;">
              <span style="color:#f8fafc;font-family:'Segoe UI',sans-serif;font-size:14px;font-weight:700;letter-spacing:0.5px;">📅 Evolución — últimos 5 días</span>
            </div>
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;">
              <thead>
                <tr style="background:#f8fafc;">
                  <th style="padding:10px 12px;text-align:left;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;">Fecha</th>
                  <th style="padding:10px 12px;text-align:right;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;">Invertido</th>
                  <th style="padding:10px 12px;text-align:right;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;">Valor</th>
                  <th style="padding:10px 12px;text-align:right;font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;">ROI</th>
                </tr>
              </thead>
              <tbody>{filas_hist}</tbody>
            </table>
          </td></tr>
        </table>"""

    # ---- Ranking ----
    medallas = ["🥇", "🥈", "🥉"]
    filas_ranking = ""
    for i, (t, r) in enumerate(ranking, 1):
        color = "#16a34a" if r >= 0 else "#dc2626"
        bg = "#dcfce7" if r >= 0 else "#fee2e2"
        medalla = medallas[i-1] if i <= 3 else f"{i}."
        filas_ranking += f"""
        <tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:10px 14px;font-family:'Segoe UI',sans-serif;font-size:15px;">{medalla}</td>
          <td style="padding:10px 14px;font-family:'Segoe UI',sans-serif;font-size:14px;font-weight:600;color:#0f172a;">{t}</td>
          <td style="padding:10px 14px;text-align:right;">
            <span style="background:{bg};color:{color};padding:4px 12px;border-radius:20px;font-size:13px;font-weight:700;font-family:'Segoe UI',sans-serif;">{r:+.2f}%</span>
          </td>
        </tr>"""

    # ---- Color resumen total ----
    color_total = "#16a34a" if ganancia_total >= 0 else "#dc2626"
    bg_total = "#dcfce7" if ganancia_total >= 0 else "#fee2e2"
    flecha_total = "▲" if ganancia_total >= 0 else "▼"

    variacion_dia_html = ""
    if variacion_dia is not None:
        color_dia = "#16a34a" if variacion_dia >= 0 else "#dc2626"
        bg_dia = "#dcfce7" if variacion_dia >= 0 else "#fee2e2"
        flecha_dia = "▲" if variacion_dia >= 0 else "▼"
        variacion_dia_html = f"""
        <td style="padding:20px;text-align:center;border-right:1px solid #e2e8f0;">
          <div style="font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Variación del día</div>
          <div style="font-size:22px;font-weight:800;font-family:'Segoe UI',sans-serif;color:{color_dia};">{flecha_dia} {abs(variacion_dia):.2f}</div>
          <div style="margin-top:4px;"><span style="background:{bg_dia};color:{color_dia};padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;font-family:'Segoe UI',sans-serif;">{porcentaje_dia:+.2f}%</span></div>
        </td>"""

    # ---- HTML FINAL ----
    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f1f5f9;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:20px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

  <!-- HEADER -->
  <tr><td style="padding-bottom:20px;">
    <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#0f4c81 100%);border-radius:16px;padding:32px 28px;text-align:center;">
      <div style="font-family:'Segoe UI',sans-serif;font-size:11px;color:#94a3b8;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Reporte diario</div>
      <div style="font-family:Georgia,serif;font-size:28px;font-weight:700;color:#f8fafc;margin-bottom:4px;">📊 Mi Portafolio</div>
      <div style="font-family:'Segoe UI',sans-serif;font-size:14px;color:#94a3b8;">{fecha_legible}</div>
    </div>
  </td></tr>

  <!-- RESUMEN TOTAL -->
  <tr><td style="padding-bottom:20px;">
    <div style="background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.08);overflow:hidden;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:20px;text-align:center;border-right:1px solid #e2e8f0;">
            <div style="font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Total invertido</div>
            <div style="font-size:22px;font-weight:800;font-family:'Segoe UI',sans-serif;color:#0f172a;">${total_invertido:,.2f}</div>
          </td>
          <td style="padding:20px;text-align:center;border-right:1px solid #e2e8f0;">
            <div style="font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Valor actual</div>
            <div style="font-size:22px;font-weight:800;font-family:'Segoe UI',sans-serif;color:#0f172a;">${total_actual:,.2f}</div>
          </td>
          {variacion_dia_html}
          <td style="padding:20px;text-align:center;">
            <div style="font-family:'Segoe UI',sans-serif;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">ROI total</div>
            <div style="font-size:22px;font-weight:800;font-family:'Segoe UI',sans-serif;color:{color_total};">{flecha_total} {abs(porcentaje_total):.2f}%</div>
            <div style="margin-top:4px;"><span style="background:{bg_total};color:{color_total};padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;font-family:'Segoe UI',sans-serif;">${ganancia_total:+,.2f}</span></div>
          </td>
        </tr>
      </table>
    </div>
  </td></tr>

  <!-- ALERTAS -->
  {alertas_html}

  <!-- SECTORES -->
  {sectores_html}

  <!-- RANKING -->
  <tr><td style="padding-bottom:24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">
      <tr><td>
        <div style="background:#1e293b;padding:12px 16px;">
          <span style="color:#f8fafc;font-family:'Segoe UI',sans-serif;font-size:14px;font-weight:700;letter-spacing:0.5px;">🏆 Ranking del día</span>
        </div>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;">
          <tbody>{filas_ranking}</tbody>
        </table>
      </td></tr>
    </table>
  </td></tr>

  <!-- HISTORIAL 5 DÍAS -->
  {historial_html}

  <!-- COMENTARIO DEL ANALISTA -->
  <tr><td style="padding-bottom:24px;">
    <div style="background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.08);padding:22px 24px;">
      <div style="font-family:'Segoe UI',sans-serif;font-size:14px;font-weight:700;color:#0f172a;margin-bottom:10px;">🧠 Comentario del analista</div>
      <div style="font-family:'Segoe UI',sans-serif;font-size:14px;color:#334155;line-height:1.7;">
        {generar_comentario()}
      </div>
    </div>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="padding-bottom:20px;">
    <div style="text-align:center;font-family:'Segoe UI',sans-serif;font-size:11px;color:#94a3b8;padding:16px;">
      Generado automáticamente · {fecha_legible}<br>
      Los datos son orientativos y no constituyen asesoramiento financiero.
    </div>
  </td></tr>

</table>
</td></tr>
</table>

</body>
</html>"""
    return html

# =========================
# GUARDAR CSV DETALLADO
# =========================
existe = os.path.isfile(CSV_DETALLADO)
with open(CSV_DETALLADO, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=acciones_para_csv[0].keys())
    if not existe:
        writer.writeheader()
    writer.writerows(acciones_para_csv)

# =========================
# GUARDAR CSV TOTALES
# =========================
existe_totales = os.path.isfile(CSV_TOTALES)
with open(CSV_TOTALES, "a", newline="") as f:
    writer = csv.writer(f)
    if not existe_totales:
        writer.writerow(["fecha", "total_invertido", "total_actual"])
    writer.writerow([fecha_hoy, round(total_invertido, 2), round(total_actual, 2)])

# =========================
# ENVIAR CORREO
# =========================
html_body = build_email_html()

msg = MIMEMultipart("alternative")
msg["From"] = CORREO_EMISOR
msg["To"] = CORREO_DESTINO
msg["Subject"] = f"📊 Portafolio {fecha_hoy} — ROI total {porcentaje_total:+.2f}%"

msg.attach(MIMEText(html_body, "html"))

with open(CSV_DETALLADO, "rb") as f:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{CSV_DETALLADO}"')
    msg.attach(part)

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(CORREO_EMISOR, CONTRASENA_APP)
    server.send_message(msg)

print("📧 Correo enviado correctamente")
