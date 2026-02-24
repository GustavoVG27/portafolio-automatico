from datetime import date

PORTAFOLIO = {

    "NVDA": {
        "nombre": "NVIDIA Corp.",
        "tipo": "Acción",
        "sector": "Tecnología",
        "fecha_compra": date(2025, 12, 29),
        "cantidad": 0.53573,
        "precio_compra": 186.66,
        "invertido": 100.00
    },

    "PANW": {
        "nombre": "Palo Alto Networks",
        "tipo": "Acción",
        "sector": "Tecnología",
        "fecha_compra": date(2025, 12, 29),
        "cantidad": 0.10628,
        "precio_compra": 186.76,
        "invertido": 19.85
    },

    "UBER": {
        "nombre": "Uber Technologies",
        "tipo": "Acción",
        "sector": "Tecnología",
        "fecha_compra": date(2025, 12, 29),
        "cantidad": 0.18434,
        "precio_compra": 81.37,
        "invertido": 15.00
    },

    # S&P 500 UCITS (Londres)
    "CSPX.L": {
        "nombre": "iShares Core S&P 500 UCITS ETF",
        "tipo": "ETF",
        "sector": "S&P 500",
        "fecha_compra": date(2025, 12, 29),
        "cantidad": 0.29640,
        "precio_compra": 736.27,   # usa tu precio real promedio
        "invertido": 219.74
    },

    "VHT": {
        "nombre": "Vanguard Health Care ETF",
        "tipo": "ETF",
        "sector": "Salud",
        "fecha_compra": date(2026, 1, 21),
        "cantidad": 0.11705,
        "precio_compra": 289.18,
        "invertido": 33.94
    },

    "VXUS": {
        "nombre": "Vanguard Total International Stock ETF",
        "tipo": "ETF",
        "sector": "Mercados Emergentes",
        "fecha_compra": date(2026, 1, 25),
        "cantidad": 0.36211,
        "precio_compra": 82.96,
        "invertido": 30.14
    },

    "URA": {
        "nombre": "Global X Uranium ETF",
        "tipo": "ETF",
        "sector": "Energía",
        "fecha_compra": date(2026, 1, 20),
        "cantidad": 0.52935,
        "precio_compra": 54.50,
        "invertido": 28.84
    },

    # Bitcoin
    "BTC-USD": {
        "nombre": "Bitcoin",
        "tipo": "Criptomoneda",
        "sector": "Cripto",
        "fecha_compra": date(2026, 1, 30),
        "cantidad": 0.00033006,
        "precio_compra": 68105.97,
        "invertido": 22.00
    }
}
