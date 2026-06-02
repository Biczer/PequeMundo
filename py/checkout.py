from flask import render_template, redirect, session


COSTO_RM     = 9990
COSTO_REGION = 14990


def get_carrito():
    return session.get("carrito", [])


def register_routes(app):

    @app.route("/checkout")
    def checkout():
        items = get_carrito()
        if not items:
            return redirect("/carrito")

        entrega  = session.get("entrega", "domicilio_rm")
        subtotal = sum(i["precio"] * i["cantidad"] for i in items)
        costos   = {"domicilio_rm": COSTO_RM, "domicilio_region": COSTO_REGION, "retiro": 0}
        envio    = costos.get(entrega, COSTO_RM)
        total    = subtotal + envio

        usuario = session.get("usuario", "")

        return render_template(
            "checkout.html",
            items=items,
            subtotal=subtotal,
            envio=envio,
            total=total,
            entrega=entrega,
            usuario=usuario,
        )
