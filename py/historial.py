import os
import json
from flask import render_template, session, redirect


PEDIDOS_JSON = os.path.join(os.path.dirname(__file__), "data", "pedidos.json")


def leer_pedidos():
    if not os.path.exists(PEDIDOS_JSON):
        return []
    with open(PEDIDOS_JSON, encoding="utf-8") as f:
        return json.load(f)


def register_routes(app):

    @app.route("/historial")
    def historial():
        pedidos = leer_pedidos()

        # Si hay usuario en sesión, filtrar solo sus pedidos
        usuario = session.get("usuario")
        if usuario and session.get("rol") != "Admin":
            pedidos = [p for p in pedidos if p.get("cliente") == usuario]

        return render_template("historial.html", pedidos=pedidos)

    @app.route("/pedido/<int:id>")
    def detalle_pedido(id):
        pedidos = leer_pedidos()
        pedido  = next((p for p in pedidos if p["id"] == id), None)
        if pedido is None:
            return redirect("/historial")
        return render_template("detalle_pedido.html", pedido=pedido)
