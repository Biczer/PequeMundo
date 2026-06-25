from flask import Blueprint, render_template, request
from models.producto import Producto

catalogo_bp = Blueprint('catalogo', __name__)

@catalogo_bp.route('/catalogo')
def catalogo():
    categoria = request.args.get('categoria')

    query = Producto.query.filter(
        Producto.estado.ilike('activo')
    )

    if categoria:
        query = query.filter(
            Producto.categoria == categoria
        )

    productos = query.all()

    return render_template("catalogo.html", productos=productos)
