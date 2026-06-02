import os
import json
from flask import render_template, request, jsonify


def leer_productos():
    ruta = os.path.join(os.path.dirname(__file__), "data", "productos.json")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def register_routes(app):

    @app.route("/catalogo")
    def catalogo():
        return render_template("catalogo.html")

    @app.route("/api/productos")
    def api_productos():
        productos = leer_productos()
        categoria = request.args.get("categoria", "").strip()
        if categoria:
            productos = [p for p in productos if p["categoria"] == categoria]
        return jsonify(productos)

    @app.route("/api/productos/<int:id>")
    def api_producto(id):
        productos = leer_productos()
        producto = next((p for p in productos if p["id"] == id), None)
        if producto is None:
            return jsonify({"error": "Producto no encontrado"}), 404
        return jsonify(producto)

    @app.route("/api/categorias")
    def api_categorias():
        productos = leer_productos()
        categorias = sorted(set(p["categoria"] for p in productos))
        return jsonify(categorias)
