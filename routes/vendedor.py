import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import Producto, Pedido
from decorators import requiere_vendedor
from services.mercadopago_service import crear_preferencia

vendedor_bp = Blueprint('vendedor', __name__)


@vendedor_bp.route('/vendedor')
@requiere_vendedor
def vendedor_dashboard():
    vendedor_id = session.get('usuario_id')
    mis_pedidos = Pedido.query.filter_by(vendedor_id=vendedor_id).all()
    productos = Producto.query.filter_by(estado='Activo').all()
    total_ventas = sum(p.total for p in mis_pedidos if p.mp_status == 'approved')
    pedidos_pendientes = sum(1 for p in mis_pedidos if p.estado == 'Pendiente')
    pedidos_pagados = sum(1 for p in mis_pedidos if p.mp_status == 'approved')
    return render_template('vendedor_dashboard.html',
                           mis_pedidos=mis_pedidos,
                           todos_pedidos=Pedido.query.all(),
                           productos=productos,
                           total_ventas=total_ventas,
                           pedidos_pendientes=pedidos_pendientes,
                           pedidos_pagados=pedidos_pagados)


@vendedor_bp.route('/vendedor/pedidos')
@requiere_vendedor
def vendedor_pedidos():
    vendedor_id = session.get('usuario_id')
    pedidos = Pedido.query.filter_by(vendedor_id=vendedor_id).all()
    return render_template('vendedor_pedidos.html', pedidos=pedidos)


@vendedor_bp.route('/vendedor/catalogo')
@requiere_vendedor
def vendedor_catalogo():
    productos = Producto.query.filter_by(estado='Activo').all()
    return render_template('vendedor_catalogo.html', productos=productos)


@vendedor_bp.route('/vendedor/estadisticas')
@requiere_vendedor
def vendedor_estadisticas():
    vendedor_id = session.get('usuario_id')
    pedidos = Pedido.query.filter_by(vendedor_id=vendedor_id).all()
    aprobados = [p for p in pedidos if p.mp_status == 'approved']
    pendientes = [p for p in pedidos if p.estado == 'Pendiente' and p.mp_status != 'approved']
    rechazados = [p for p in pedidos if p.mp_status == 'rejected']
    total_ventas = sum(p.total for p in aprobados)
    return render_template('vendedor_estadisticas.html',
                           pedidos=pedidos, aprobados=aprobados,
                           pendientes=pendientes, rechazados=rechazados,
                           total_ventas=total_ventas)


@vendedor_bp.route('/vendedor/crear_pedido', methods=['GET', 'POST'])
@requiere_vendedor
def vendedor_crear_pedido():
    productos = Producto.query.filter(Producto.estado == 'Activo', Producto.stock > 0).all()
    if request.method == 'POST':
        cliente = request.form['cliente']
        cliente_email = request.form['cliente_email']
        items_raw = request.form.get('items', '[]')
        try:
            items = json.loads(items_raw)
        except Exception:
            flash('Error en los productos seleccionados.', 'danger')
            return render_template('vendedor_crear_pedido.html', productos=productos)
        if not items:
            flash('Debes agregar al menos un producto.', 'danger')
            return render_template('vendedor_crear_pedido.html', productos=productos)
        total = sum(i['precio'] * i['cantidad'] for i in items)
        nuevo_pedido = Pedido(
            cliente=cliente, cliente_email=cliente_email,
            total=total, estado='Pendiente',
            vendedor_id=session.get('usuario_id'),
            items_json=items_raw
        )
        db.session.add(nuevo_pedido)
        db.session.commit()
        try:
            base = request.host_url.rstrip('/').replace('http://', 'https://', 1)
            preference = crear_preferencia(items, cliente, cliente_email, nuevo_pedido.id, base)
            if preference.get("id"):
                nuevo_pedido.mp_preference_id = preference["id"]
                db.session.commit()
                checkout_url = preference.get("sandbox_init_point") or preference.get("init_point")
                return redirect(checkout_url)
            flash('Pedido creado pero MP no respondió correctamente.', 'warning')
            return redirect(url_for('vendedor.vendedor_pedidos'))
        except Exception as e:
            flash(f'Error Mercado Pago: {e}', 'danger')
            return redirect(url_for('vendedor.vendedor_pedidos'))
    return render_template('vendedor_crear_pedido.html', productos=productos)
