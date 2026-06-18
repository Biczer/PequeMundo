from flask import Blueprint, request, jsonify
from extensions import db
from models import Producto

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/productos')
def api_productos():
    categoria = request.args.get('categoria', '').strip()
    if categoria:
        lista = Producto.query.filter_by(categoria=categoria, estado='Activo').order_by(Producto.id).all()
    else:
        lista = Producto.query.filter_by(estado='Activo').order_by(Producto.id).all()
    return jsonify([{
        'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion,
        'imagen': p.imagen, 'categoria': p.categoria,
        'precio': p.precio, 'stock': p.stock
    } for p in lista])


@api_bp.route('/api/productos/<int:id>')
def api_producto(id):
    p = db.session.get(Producto, id)
    if not p:
        from flask import abort
        abort(404)
    return jsonify({
        'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion,
        'imagen': p.imagen, 'categoria': p.categoria,
        'precio': p.precio, 'stock': p.stock
    })


@api_bp.route('/api/categorias')
def api_categorias():
    rows = (
        db.session.query(Producto.categoria)
        .filter_by(estado='Activo')
        .distinct()
        .order_by(Producto.categoria)
        .all()
    )
    return jsonify([r[0] for r in rows])
