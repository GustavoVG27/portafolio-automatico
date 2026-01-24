import csv
from datetime import datetime

ARCHIVO = "historial_portafolio.csv"

def leer_historial():
    with open(ARCHIVO, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def comparacion_vs_ayer(total_actual_hoy):
    historial = leer_historial()

    if len(historial) < 2:
        return None

    ayer = float(historial[-2]["total_actual"])
    diferencia = total_actual_hoy - ayer
    porcentaje = (diferencia / ayer) * 100 if ayer != 0 else 0

    return {
        "ayer": ayer,
        "hoy": total_actual_hoy,
        "diff": diferencia,
        "pct": porcentaje
    }

def ranking_portafolio(resultados):
    ranking = sorted(
        resultados,
        key=lambda x: x["roi"],
        reverse=True
    )
    return ranking

def alertas_diarias(comparacion, ranking):
    alertas = []

    if comparacion:
        if comparacion["pct"] <= -2:
            alertas.append("🚨 Caída fuerte del portafolio hoy")
        elif comparacion["pct"] >= 2:
            alertas.append("🚀 Subida fuerte del portafolio hoy")

    for r in ranking:
        if r["roi"] >= 5:
            alertas.append(f"🚀 {r['ticker']} sube fuerte (+{r['roi']:.2f}%)")
        elif r["roi"] <= -5:
            alertas.append(f"🔴 {r['ticker']} cae fuerte ({r['roi']:.2f}%)")

    return alertas

def comentario_analista(comparacion, ranking):
    if not comparacion:
        return "Aún no hay suficiente historial para análisis."

    mejor = ranking[0]
    peor = ranking[-1]

    if comparacion["diff"] > 0:
        return (
            "El portafolio registra una sesión positiva frente al día anterior, "
            f"impulsado principalmente por {mejor['ticker']}. "
            "El desempeño general se mantiene estable."
        )
    else:
        return (
            "El portafolio muestra una jornada negativa respecto a ayer, "
            f"con presión principalmente en {peor['ticker']}. "
            "Se recomienda seguimiento a corto plazo."
        )
