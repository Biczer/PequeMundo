from flask import render_template


def register_routes(app):

    @app.route("/producto/<int:id>")
    def detalle_producto(id):
        return render_template("detalle.html")
