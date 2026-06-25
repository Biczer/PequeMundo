import os
import json
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from database.conexion import get_connection

load_dotenv()


API_KEY = os.environ.get("PEDIDOS_API_KEY", "dev-api-key-pequemundo")

# Estados válidos para la API de despacho (empresa logística externa)
# Flujo: Pagado → Enviado → Entregado
ESTADOS_VALIDOS = ["Pendiente", "Pagado", "Enviado", "Entregado", "Rechazado"]
TRANSICIONES = {
    "Pendiente":  None,        # Esperando pago (no gestionable por despacho)
    "Pagado":     "Enviado",   # Pago confirmado → listo para despachar
    "Enviado":    "Entregado", # En camino → entregado
    "Entregado":  None,        # Estado final
    "Rechazado":  None,        # Estado final
}


def requiere_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-Key") != API_KEY:
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)
    return wrapper


def _serializar(pedido):
    """Convierte un dict de pedido BD a formato JSON limpio."""
    items = []
    if pedido.get("items_json"):
        try:
            items = json.loads(pedido["items_json"])
        except Exception:
            pass
    return {
        "id":          pedido["id"],
        "cliente":     pedido["cliente"],
        "email":       pedido["cliente_email"],
        "total":       pedido["total"],
        "estado":      pedido["estado"],
        "mp_status":   pedido["mp_status"],
        "mp_pago_id":  pedido["mp_payment_id"],
        "siguiente_estado": TRANSICIONES.get(pedido["estado"]) or "ninguno (estado final)",
        "items":       items,
    }


# ── GET /api/pedidos ─────────────────────────────────────────────────────────
@app.get("/api/pedidos")
@requiere_api_key
def listar_pedidos():
    """
    Lista todos los pedidos.
    Filtros opcionales por query string:
      ?estado=Pagado
      ?email=cliente@ejemplo.com
    """
    estado_filtro = request.args.get("estado", "").strip()
    email_filtro  = request.args.get("email", "").strip()

    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        query  = "SELECT * FROM pedido WHERE 1=1"
        params = []

        if estado_filtro:
            query  += " AND estado = %s"
            params.append(estado_filtro)
        if email_filtro:
            query  += " AND cliente_email = %s"
            params.append(email_filtro)

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        pedidos = cursor.fetchall()
        cursor.close(); conn.close()

        return jsonify([_serializar(p) for p in pedidos])

    except Exception as e:
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500


# ── GET /api/pedidos/<id> ────────────────────────────────────────────────────
@app.get("/api/pedidos/<int:id>")
@requiere_api_key
def obtener_pedido(id):
    """Retorna el detalle de un pedido por ID."""
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pedido WHERE id = %s", (id,))
        pedido = cursor.fetchone()
        cursor.close(); conn.close()

        if pedido is None:
            return jsonify({"error": f"Pedido #{id} no encontrado"}), 404

        return jsonify(_serializar(pedido))

    except Exception as e:
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500


# ── PATCH /api/pedidos/<id>/estado ──────────────────────────────────────────
@app.patch("/api/pedidos/<int:id>/estado")
@requiere_api_key
def cambiar_estado(id):
    """
    Cambia el estado de despacho de un pedido.
    Body JSON: { "estado": "Enviado" }
    Transiciones permitidas:
      Pagado → Enviado → Entregado
    """
    body = request.get_json(silent=True)
    if not body or "estado" not in body:
        return jsonify({"error": "Body JSON requerido con campo 'estado'"}), 400

    nuevo_estado = body["estado"].strip().capitalize()
    if nuevo_estado not in ESTADOS_VALIDOS:
        return jsonify({
            "error": f"Estado '{nuevo_estado}' no válido",
            "estados_validos": ESTADOS_VALIDOS,
        }), 400

    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pedido WHERE id = %s", (id,))
        pedido = cursor.fetchone()

        if pedido is None:
            cursor.close(); conn.close()
            return jsonify({"error": f"Pedido #{id} no encontrado"}), 404

        estado_actual = pedido["estado"]

        if nuevo_estado == estado_actual:
            cursor.close(); conn.close()
            return jsonify({"mensaje": "El pedido ya tiene ese estado",
                            "pedido": _serializar(pedido)}), 200

        siguiente_permitido = TRANSICIONES.get(estado_actual)
        if siguiente_permitido != nuevo_estado:
            cursor.close(); conn.close()
            return jsonify({
                "error": f"Transición no permitida: '{estado_actual}' → '{nuevo_estado}'",
                "siguiente_permitido": siguiente_permitido or "ninguno (estado final)",
            }), 422

        cursor.execute(
            "UPDATE pedido SET estado = %s WHERE id = %s",
            (nuevo_estado, id)
        )
        conn.commit()

        # Releer para devolver el pedido actualizado
        cursor.execute("SELECT * FROM pedido WHERE id = %s", (id,))
        pedido_actualizado = cursor.fetchone()
        cursor.close(); conn.close()

        return jsonify({
            "mensaje": f"Estado actualizado: '{estado_actual}' → '{nuevo_estado}'",
            "pedido": _serializar(pedido_actualizado),
        }), 200

    except Exception as e:
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5001))
    print(f"[pedidos_api] Corriendo en http://localhost:{port}")
    print(f"[pedidos_api] API Key: {API_KEY}")
    app.run(debug=True, port=port)
