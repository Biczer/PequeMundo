import requests

PARTNER_API_URL = "https://saborlatinochile.cl/api/productos_pequemundos_api.php"


def obtener_productos(categoria=None):
    response = requests.get(PARTNER_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json().get("data", [])
    if categoria:
        data = [p for p in data if p["categoria"].lower() == categoria.lower()]
    return data


def normalizar_producto(p):
    return {
        "id": f"SL-{p['id']}",
        "sku": p["sku"],
        "nombre": p["nombre"],
        "descripcion": p["descripcion"],
        "categoria": p["categoria"],
        "precio": p["precio"],
        "precio_formateado": p["precio_formateado"],
        "stock": p["stock"],
        "imagen": p["imagen"],
        "material": p.get("material"),
        "color": p.get("color"),
        "edad_recomendada": p.get("edad_recomendada"),
        "medidas": p.get("medidas"),
        "destacado": p.get("destacado", False),
        "empresa": p.get("empresa"),
        "socio": "sabor_latino",
    }
