from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import Producto

carrito_bp = Blueprint('carrito', __name__)

COSTO_RM = 9990
COSTO_REGION = 14990


def _costos(entrega):
    mapa = {'domicilio_rm': COSTO_RM, 'domicilio_region': COSTO_REGION, 'retiro': 0}
    return mapa.get(entrega, COSTO_RM)


@carrito_bp.route('/carrito')
def carrito():
    items = session.get('carrito', [])
    entrega = session.get('entrega', 'domicilio_rm')
    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    total = subtotal + _costos(entrega)
    return render_template('carrito.html', items=items, subtotal=subtotal, total=total,
                           entrega=entrega, costo_rm=COSTO_RM, costo_region=COSTO_REGION)


@carrito_bp.route('/carrito/agregar/<int:id>')
def agregar_al_carrito(id):
    p = Producto.query.filter_by(id=id, estado='Activo').first()
    if not p:
        return redirect(url_for('publico.catalogo'))
    items = session.get('carrito', [])
    for item in items:
        if item['id'] == id:
            if item['cantidad'] < p.stock:
                item['cantidad'] += 1
            break
    else:
        items.append({'id': p.id, 'nombre': p.nombre, 'precio': int(p.precio),
                      'cantidad': 1, 'imagen': p.imagen})
    session['carrito'] = items
    session.modified = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True})
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/aumentar/<int:id>')
def aumentar_cantidad(id):
    items = session.get('carrito', [])
    for item in items:
        if item['id'] == id:
            item['cantidad'] += 1
            break
    session['carrito'] = items
    session.modified = True
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/disminuir/<int:id>')
def disminuir_cantidad(id):
    items = session.get('carrito', [])
    for item in items:
        if item['id'] == id:
            if item['cantidad'] > 1:
                item['cantidad'] -= 1
            else:
                items.remove(item)
            break
    session['carrito'] = items
    session.modified = True
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/eliminar/<int:id>')
def eliminar_del_carrito(id):
    session['carrito'] = [i for i in session.get('carrito', []) if i['id'] != id]
    session.modified = True
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/vaciar')
def vaciar_carrito():
    session['carrito'] = []
    session.modified = True
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/entrega/<tipo>')
def cambiar_entrega(tipo):
    if tipo in ('domicilio_rm', 'domicilio_region', 'retiro'):
        session['entrega'] = tipo
        session.modified = True
    return redirect(url_for('carrito.carrito'))
