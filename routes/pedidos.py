import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from extensions import db
from models import Producto, Usuario, Pedido
from decorators import requiere_cliente
from services.mercadopago_service import crear_preferencia

pedidos_bp = Blueprint('pedidos', __name__)

COSTO_RM = 9990
COSTO_REGION = 14990


def _costos(entrega):
    mapa = {'domicilio_rm': COSTO_RM, 'domicilio_region': COSTO_REGION, 'retiro': 0}
    return mapa.get(entrega, COSTO_RM)


@pedidos_bp.route('/carrito/checkout', methods=['POST'])
def checkout_json():
    if not session.get('usuario_id'):
        return jsonify({'error': 'Debes iniciar sesión para comprar.'}), 401
    if session.get('rol') == 'Vendedor':
        return jsonify({'error': 'Los vendedores no pueden comprar.'}), 403
    data = request.get_json(silent=True) or {}
    items = data.get('items', [])
    if not items:
        return jsonify({'error': 'Carrito vacío'}), 400
    usuario = db.session.get(Usuario, session['usuario_id'])
    total = sum(i['precio'] * i['cantidad'] for i in items)
    for item in items:
        producto = db.session.get(Producto, item['id'])
        if not producto or producto.stock < item['cantidad']:
            return jsonify({'error': f"Stock insuficiente para {item['nombre']}"}), 400
    nuevo_pedido = Pedido(
        cliente=usuario.nombre,
        cliente_email=usuario.email,
        total=total,
        estado='Pendiente',
        vendedor_id=None,
        items_json=json.dumps(items)
    )
    db.session.add(nuevo_pedido)
    db.session.commit()
    try:
        base = request.host_url.rstrip('/').replace('http://', 'https://', 1)
        preference = crear_preferencia(items, usuario.nombre, usuario.email, nuevo_pedido.id, base)
        if preference.get("id"):
            nuevo_pedido.mp_preference_id = preference["id"]
            db.session.commit()
            checkout_url = preference.get("sandbox_init_point") or preference.get("init_point")
            return jsonify({'checkout_url': checkout_url})
        db.session.delete(nuevo_pedido)
        db.session.commit()
        return jsonify({'error': 'Mercado Pago no respondió correctamente', 'detalle': preference}), 500
    except Exception as e:
        db.session.delete(nuevo_pedido)
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@pedidos_bp.route('/mis-pedidos')
@requiere_cliente
def mis_pedidos():
    usuario = db.session.get(Usuario, session['usuario_id'])
    pedidos = Pedido.query.filter_by(cliente_email=usuario.email).order_by(Pedido.id.desc()).all()
    return render_template('mis_pedidos.html', pedidos=pedidos)


@pedidos_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    items = session.get('carrito', [])
    if not items:
        return redirect(url_for('carrito.carrito'))
    entrega = session.get('entrega', 'domicilio_rm')
    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    envio = _costos(entrega)
    total = subtotal + envio
    if request.method == 'POST':
        session['datos_envio'] = {
            'nombre':   request.form.get('nombre', ''),
            'email':    request.form.get('email', ''),
            'telefono': request.form.get('telefono', ''),
            'calle':    request.form.get('calle', ''),
            'depto':    request.form.get('depto', ''),
            'comuna':   request.form.get('comuna', ''),
            'region':   request.form.get('region', ''),
        }
        session.modified = True
        return redirect(url_for('pedidos.pago'))
    return render_template('checkout.html', items=items, subtotal=subtotal,
                           envio=envio, total=total, entrega=entrega,
                           usuario=session.get('usuario', ''))


@pedidos_bp.route('/pago')
def pago():
    items = session.get('carrito', [])
    if not items:
        return redirect(url_for('carrito.carrito'))
    entrega = session.get('entrega', 'domicilio_rm')
    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    envio = _costos(entrega)
    total = subtotal + envio
    return render_template('pago_form.html', items=items, subtotal=subtotal,
                           envio=envio, total=total, entrega=entrega)


@pedidos_bp.route('/pago/procesar', methods=['POST'])
def pago_procesar():
    items = session.get('carrito', [])
    if not items:
        return redirect(url_for('carrito.carrito'))
    entrega = session.get('entrega', 'domicilio_rm')
    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    envio = _costos(entrega)
    total = subtotal + envio

    nombre = request.form.get('nombre_tarjeta', '').strip()
    numero = request.form.get('numero_tarjeta', '').replace(' ', '')
    expira = request.form.get('expiracion', '').strip()
    cvv = request.form.get('cvv', '').strip()

    errores = {}
    if not nombre:
        errores['nombre_tarjeta'] = 'Ingresa el nombre.'
    if len(numero) != 16 or not numero.isdigit():
        errores['numero_tarjeta'] = 'Ingresa los 16 dígitos.'
    if not expira:
        errores['expiracion'] = 'Ingresa la fecha.'
    if len(cvv) < 3:
        errores['cvv'] = 'CVV inválido.'

    if errores:
        return render_template('pago_form.html', items=items, subtotal=subtotal,
                               envio=envio, total=total, entrega=entrega,
                               errores=errores, form=request.form)
    try:
        cliente_nombre = session.get('usuario', nombre)
        cliente_email = session.get('datos_envio', {}).get('email', '')
        nuevo_pedido = Pedido(
            cliente=cliente_nombre,
            cliente_email=cliente_email,
            total=total,
            estado='Pagado',
            vendedor_id=None,
            mp_status='approved',
            items_json=json.dumps(items)
        )
        db.session.add(nuevo_pedido)
        for item in items:
            p = db.session.get(Producto, item['id'])
            if p:
                p.stock = max(0, p.stock - item['cantidad'])
                if p.stock == 0:
                    p.estado = 'Agotado'
        db.session.commit()
        session['mp_id_orden'] = nuevo_pedido.id
        session['carrito'] = []
        session.modified = True
        pedido_data = {
            'id_orden': nuevo_pedido.id,
            'fecha_orden': 'Ahora',
            'total': total,
            'estado': 'Pagado',
            'codigo_transaccion': f'SIM-{nuevo_pedido.id:06d}',
            'lineas': [{'nombre': i['nombre'], 'cantidad': i['cantidad'],
                        'precio_unitario': i['precio'], 'subtotal': i['precio'] * i['cantidad']}
                       for i in items]
        }
        return render_template('confirmacion.html', pedido=pedido_data, payment_status='approved')
    except Exception as e:
        return render_template('pago_error.html', error=str(e)), 500


@pedidos_bp.route('/historial')
def historial():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    usuario_id = session.get('usuario_id')
    if session.get('rol') == 'Admin':
        pedidos = Pedido.query.order_by(Pedido.id.desc()).all()
    else:
        usuario = db.session.get(Usuario, usuario_id)
        pedidos = Pedido.query.filter_by(
            cliente_email=usuario.email if usuario else ''
        ).order_by(Pedido.id.desc()).all()
    filas = [{'id_orden': p.id, 'fecha_orden': '—', 'total': p.total,
               'estado': p.estado, 'codigo_transaccion': p.mp_payment_id or '—'}
             for p in pedidos]
    return render_template('historial.html', pedidos=filas)


@pedidos_bp.route('/pedido/<int:id>')
def detalle_pedido(id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    pedido = db.session.get(Pedido, id) or (None,)
    if not pedido or pedido == (None,):
        from flask import abort
        abort(404)
    items_raw = []
    if pedido.items_json:
        try:
            raw = json.loads(pedido.items_json)
            items_raw = [{'nombre': i.get('nombre', ''), 'cantidad': i.get('cantidad', 1),
                          'precio_unitario': i.get('precio', 0),
                          'subtotal': i.get('precio', 0) * i.get('cantidad', 1)} for i in raw]
        except Exception:
            pass
    pedido_data = {
        'id_orden': pedido.id,
        'fecha_orden': '—',
        'total': pedido.total,
        'precio_envio': 0,
        'estado': pedido.estado,
        'estado_pago': pedido.mp_status or '—',
        'codigo_transaccion': pedido.mp_payment_id or '—',
        'tipo_entrega': 'domicilio_rm',
        'cliente': pedido.cliente,
        'lineas': items_raw,
    }
    return render_template('detalle_pedido.html', pedido=pedido_data)
