import os
import json
from functools import wraps
from flask import Flask, jsonify, request

app = Flask(__name__)

PEDIDOS_JSON  = os.path.join(os.path.dirname(__file__), "data", "pedidos.json")
API_KEY       = os.environ.get("PEDIDOS_API_KEY", "dev-api-key-pequemundo")
ESTADOS_VALIDOS = ["Pendiente", "Enviado", "Entregado"]
TRANSICIONES    = {"Pendiente": "Enviado", "Enviado": "Entregado", "Entregado": None}


def leer_pedidos():
    with open(PEDIDOS_JSON, encoding="utf-8") as f:
        return json.load(f)

def guardar_pedidos(pedidos):
    with open(PEDIDOS_JSON, "w", encoding="utf-8") as f:
        json.dump(pedidos, f, ensure_ascii=False, indent=2)

def requiere_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-Key") != API_KEY:
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.get("/api/pedidos")
@requiere_api_key
def listar_pedidos():
    estado_filtro = request.args.get("estado")
    pedidos = leer_pedidos()
    if estado_filtro:
        pedidos = [p for p in pedidos if p["estado"] == estado_filtro]
    return jsonify(pedidos)


@app.get("/api/pedidos/<int:id>")
@requiere_api_key
def obtener_pedido(id):
    pedido = next((p for p in leer_pedidos() if p["id"] == id), None)
    if pedido is None:
        return jsonify({"error": f"Pedido #{id} no encontrado"}), 404
    return jsonify(pedido)


@app.patch("/api/pedidos/<int:id>/estado")
@requiere_api_key
def cambiar_estado(id):
    body = request.get_json(silent=True)
    if not body or "estado" not in body:
        return jsonify({"error": "Body JSON requerido con campo 'estado'"}), 400

    nuevo_estado = body["estado"].strip().capitalize()
    if nuevo_estado not in ESTADOS_VALIDOS:
        return jsonify({"error": f"Estado '{nuevo_estado}' no válido", "estados_validos": ESTADOS_VALIDOS}), 400

    pedidos = leer_pedidos()
    pedido  = next((p for p in pedidos if p["id"] == id), None)
    if pedido is None:
        return jsonify({"error": f"Pedido #{id} no encontrado"}), 404

    estado_actual = pedido["estado"]

    if nuevo_estado == estado_actual:
        return jsonify({"mensaje": "El pedido ya tiene ese estado", "pedido": pedido}), 200

    if TRANSICIONES[estado_actual] != nuevo_estado:
        return jsonify({
            "error": f"Transición no permitida: '{estado_actual}' → '{nuevo_estado}'",
            "siguiente_permitido": TRANSICIONES[estado_actual] or "ninguno (estado final)"
        }), 422

    pedido["estado"] = nuevo_estado
    guardar_pedidos(pedidos)

    return jsonify({
        "mensaje": f"Estado actualizado: '{estado_actual}' → '{nuevo_estado}'",
        "pedido": pedido
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5001))
    print(f"[pedidos_api] Corriendo en http://localhost:{port}")
    app.run(debug=True, port=port)