from flask import Blueprint, render_template, request
from sqlalchemy import text
from extensions import db
from models import Producto
from services.sabor_latino_service import obtener_producto, normalizar_producto

publico_bp = Blueprint('publico', __name__)


@publico_bp.route('/')
def inicio():
    return render_template('index.html')


@publico_bp.route('/catalogo')
def catalogo():
    categoria = request.args.get('categoria', None)
    if categoria:
        producto = Producto.query.filter_by(categoria=categoria, estado='Activo').all()
    else:
        producto = Producto.query.filter_by(estado='Activo').all()
    return render_template('catalogo.html', producto=producto)


@publico_bp.route('/socios/sabor-latino')
def sabor_latino():
    try:
        producto = [normalizar_producto(p) for p in obtener_producto()]
        categorias = sorted(set(p['categoria'] for p in producto))
        error = None
    except Exception as e:
        producto = []
        categorias = []
        error = str(e)
    return render_template('sabor_latino.html',
                           producto=producto,
                           categorias=categorias,
                           error=error)


@publico_bp.route('/test-db')
def test_db():
    try:
        db.session.execute(text("SELECT 1"))
        return "MySQL OK ✅"
    except Exception as e:
        return f"Error: {e}"
