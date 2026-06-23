from flask import Blueprint, request, jsonify
from extensions import db
from models import Producto
from services.sabor_latino_service import obtener_productos, normalizar_producto

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


@api_bp.route('/api/socios/sabor-latino')
def api_sabor_latino():
    categoria = request.args.get('categoria', '').strip()
    try:
        productos = obtener_productos(categoria or None)
        return jsonify([normalizar_producto(p) for p in productos])
    except Exception as e:
        return jsonify({"error": "No se pudo conectar con el socio", "detalle": str(e)}), 503


@api_bp.route('/api/socios/sabor-latino/<string:sku>')
def api_sabor_latino_producto(sku):
    try:
        productos = obtener_productos()
        producto = next((p for p in productos if p["sku"] == sku), None)
        if not producto:
            return jsonify({"error": f"Producto {sku} no encontrado"}), 404
        return jsonify(normalizar_producto(producto))
    except Exception as e:
        return jsonify({"error": "No se pudo conectar con el socio", "detalle": str(e)}), 503
