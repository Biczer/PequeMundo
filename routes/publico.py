from flask import Blueprint, render_template, request
from sqlalchemy import text
from extensions import db
from models import Producto
from services.sabor_latino_service import obtener_productos, normalizar_producto

publico_bp = Blueprint('publico', __name__)


@publico_bp.route('/')
def inicio():
    return render_template('index.html')


@publico_bp.route('/catalogo')
def catalogo():
    categoria = request.args.get('categoria', None)
    if categoria:
        productos = Producto.query.filter_by(categoria=categoria, estado='Activo').all()
    else:
        productos = Producto.query.filter_by(estado='Activo').all()
    return render_template('catalogo.html', productos=productos)


@publico_bp.route('/socios/sabor-latino')
def sabor_latino():
    try:
        productos = [normalizar_producto(p) for p in obtener_productos()]
        categorias = sorted(set(p['categoria'] for p in productos))
        error = None
    except Exception as e:
        productos = []
        categorias = []
        error = str(e)
    return render_template('sabor_latino.html',
                           productos=productos,
                           categorias=categorias,
                           error=error)


@publico_bp.route('/test-db')
def test_db():
    try:
        db.session.execute(text("SELECT 1"))
        return "MySQL OK ✅"
    except Exception as e:
        return f"Error: {e}"
