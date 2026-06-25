from flask import Blueprint, jsonify, request
from models.producto import Producto


producto_api_bp = Blueprint(
    "producto_api",
    __name__
)


@producto_api_bp.route("/api/producto")
def listar_producto():

    categoria = request.args.get("categoria", "").strip()

    query = Producto.query.filter(
        Producto.estado == "Activo"
    )

    if categoria:
        query = query.filter(
            Producto.categoria == categoria
        )

    producto = query.order_by(
        Producto.id_producto
    ).all()

    return jsonify([
        {
            "id_producto": p.id_producto,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "imagen": p.imagen,
            "categoria": p.categoria,
            "precio": p.precio,
            "stock": p.stock,
            "estado": p.estado
        }
        for p in producto
    ])



@producto_api_bp.route("/api/producto/<int:id_producto>")
def obtener_producto(id_producto):

    producto = Producto.query.get(id_producto)

    if producto is None:
        return jsonify({
            "error": f"Producto #{id_producto} no encontrado"
        }), 404


    return jsonify({
        "id_producto": producto.id_producto,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,
        "imagen": producto.imagen,
        "categoria": producto.categoria,
        "precio": producto.precio,
        "stock": producto.stock,
        "estado": producto.estado
    })



@producto_api_bp.route("/api/categorias")
def listar_categorias():

    categorias = (
        Producto.query
        .with_entities(Producto.categoria)
        .filter(Producto.estado == "Activo")
        .distinct()
        .order_by(Producto.categoria)
        .all()
    )

    return jsonify([
        categoria[0]
        for categoria in categorias
    ])
