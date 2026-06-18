from flask import Blueprint, render_template, request
from sqlalchemy import text
from extensions import db
from models import Producto

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


@publico_bp.route('/test-db')
def test_db():
    try:
        db.session.execute(text("SELECT 1"))
        return "MySQL OK ✅"
    except Exception as e:
        return f"Error: {e}"
