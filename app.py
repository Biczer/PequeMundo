import os
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from sqlalchemy import text
import mercadopago

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-pequemundo-2024')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mysql+pymysql://{user}:{password}@{host}:{port}/{db}".format(
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        port=os.environ.get('MYSQL_PORT', '3306'),
        db=os.environ.get('MYSQL_DATABASE', 'railway'),
    )
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'TEST-7405494608123272-053123-046e81571c23bf9c73efb64662b94c28-585535158')
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)


@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value)
    except Exception:
        return []


# =========================
# MODELOS
# =========================
class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(300), nullable=False)
    imagen = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), nullable=False)


class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    rol = db.Column(db.String(20), nullable=False, default='Cliente')


class Pedido(db.Model):
    __tablename__ = 'pedido'
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(100), nullable=False)
    cliente_email = db.Column(db.String(100), nullable=True)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(30), nullable=False, default='Pendiente')
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    mp_preference_id = db.Column(db.String(200), nullable=True)
    mp_payment_id = db.Column(db.String(200), nullable=True)
    mp_status = db.Column(db.String(50), nullable=True)
    items_json = db.Column(db.Text, nullable=True)
    vendedor = db.relationship('Usuario', backref='pedidos_vendedor', foreign_keys=[vendedor_id])


# =========================
# DECORADORES
# =========================
def requiere_admin(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if session.get('rol') != 'Admin':
            flash('Debes iniciar sesión como administrador.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorado

def requiere_vendedor(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if session.get('rol') not in ('Vendedor', 'Admin'):
            flash('Debes iniciar sesión como vendedor.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorado

def requiere_cliente(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if not session.get('usuario_id'):
            flash('Debes iniciar sesión para comprar.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorado


# =========================
# UTILIDAD MP
# =========================
def crear_preferencia_mp(items_list, cliente_nombre, cliente_email, pedido_id):
    base = request.host_url.rstrip('/')

    mp_items = [{
        "id": str(i['id']),
        "title": i['nombre'],
        "quantity": int(i['cantidad']),
        "unit_price": int(i['precio']),
        "currency_id": "CLP"
    } for i in items_list]

    preference_data = {
        "items": mp_items,
        "payer": {
            "name": cliente_nombre,
            "email": cliente_email or "test_user@test.com"
        },
        "back_urls": {
            "success": f"{base}/mp/success",
            "failure": f"{base}/mp/failure",
            "pending": f"{base}/mp/pending",
        },
        "notification_url": f"{base}/mp/webhook",
        "external_reference": str(pedido_id),
        "auto_return": "all",
    }

    response = sdk.preference().create(preference_data)
    return response.get("response", {})


# =========================
# API PRODUCTOS (para el catálogo)
# =========================
@app.route('/api/productos')
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


@app.route('/api/productos/<int:id>')
def api_producto(id):
    p = Producto.query.get_or_404(id)
    return jsonify({
        'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion,
        'imagen': p.imagen, 'categoria': p.categoria,
        'precio': p.precio, 'stock': p.stock
    })


@app.route('/api/categorias')
def api_categorias():
    rows = (
        db.session.query(Producto.categoria)
        .filter_by(estado='Activo')
        .distinct()
        .order_by(Producto.categoria)
        .all()
    )
    return jsonify([r[0] for r in rows])


# =========================
# DIAGNÓSTICO
# =========================
@app.route('/test-db')
def test_db():
    try:
        db.session.execute(text("SELECT 1"))
        return "MySQL OK ✅"
    except Exception as e:
        return f"Error: {e}"


# =========================
# PÁGINAS PÚBLICAS
# =========================
@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/catalogo')
def catalogo():
    categoria = request.args.get('categoria', None)
    if categoria:
        productos = Producto.query.filter_by(categoria=categoria, estado='Activo').all()
    else:
        productos = Producto.query.filter_by(estado='Activo').all()
    return render_template('catalogo.html', productos=productos)


# =========================
# AUTENTICACIÓN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.password == password:
            session['usuario_id'] = usuario.id
            session['usuario'] = usuario.nombre
            session['rol'] = usuario.rol
            flash(f'¡Bienvenido, {usuario.nombre}!', 'success')
            if usuario.rol == 'Admin':
                return redirect(url_for('admin_dashboard'))
            elif usuario.rol == 'Vendedor':
                return redirect(url_for('vendedor_dashboard'))
            else:
                return redirect(url_for('inicio'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form.get('telefono', '')
        password = request.form['password']
        confirmar = request.form['confirmar_password']
        if password != confirmar:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('registro.html')
        if Usuario.query.filter_by(email=email).first():
            flash('Ya existe una cuenta con ese correo.', 'danger')
            return render_template('registro.html')
        nuevo = Usuario(nombre=nombre, email=email, telefono=telefono,
                        password=password, rol='Cliente')
        db.session.add(nuevo)
        db.session.commit()
        flash('Cuenta creada exitosamente. Inicia sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html')


@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('inicio'))


# =========================
# CARRITO CLIENTE
# =========================
@app.route('/carrito/checkout', methods=['POST'])
@requiere_cliente
def carrito_checkout():
    data = request.get_json(silent=True) or {}
    items = data.get('items', [])
    if not items:
        return jsonify({'error': 'Carrito vacío'}), 400
    usuario = Usuario.query.get(session['usuario_id'])
    total = sum(i['precio'] * i['cantidad'] for i in items)
    for item in items:
        producto = Producto.query.get(item['id'])
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
        preference = crear_preferencia_mp(items, usuario.nombre, usuario.email, nuevo_pedido.id)
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


@app.route('/mis-pedidos')
@requiere_cliente
def mis_pedidos():
    usuario = Usuario.query.get(session['usuario_id'])
    pedidos = Pedido.query.filter_by(cliente_email=usuario.email).order_by(Pedido.id.desc()).all()
    return render_template('mis_pedidos.html', pedidos=pedidos)

#prueba de commit
# =========================
# CARRITO POR SESIÓN (flujo tradicional)
# =========================
COSTO_RM     = 9990
COSTO_REGION = 14990

def _costos(entrega):
    mapa = {'domicilio_rm': COSTO_RM, 'domicilio_region': COSTO_REGION, 'retiro': 0}
    return mapa.get(entrega, COSTO_RM)

@app.route('/carrito')
def carrito():
    items   = session.get('carrito', [])
    entrega = session.get('entrega', 'domicilio_rm')
    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    total    = subtotal + _costos(entrega)
    return render_template('carrito.html', items=items, subtotal=subtotal, total=total,
                           entrega=entrega, costo_rm=COSTO_RM, costo_region=COSTO_REGION)

@app.route('/carrito/agregar/<int:id>')
def agregar_al_carrito(id):
    p = Producto.query.filter_by(id=id, estado='Activo').first()
    if not p:
        return redirect(url_for('catalogo'))
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
    return redirect(url_for('carrito'))

@app.route('/carrito/aumentar/<int:id>')
def aumentar_cantidad(id):
    items = session.get('carrito', [])
    for item in items:
        if item['id'] == id:
            item['cantidad'] += 1
            break
    session['carrito'] = items
    session.modified = True
    return redirect(url_for('carrito'))

@app.route('/carrito/disminuir/<int:id>')
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
    return redirect(url_for('carrito'))

@app.route('/carrito/eliminar/<int:id>')
def eliminar_del_carrito(id):
    session['carrito'] = [i for i in session.get('carrito', []) if i['id'] != id]
    session.modified = True
    return redirect(url_for('carrito'))

@app.route('/carrito/vaciar')
def vaciar_carrito():
    session['carrito'] = []
    session.modified = True
    return redirect(url_for('carrito'))

@app.route('/carrito/entrega/<tipo>')
def cambiar_entrega(tipo):
    if tipo in ('domicilio_rm', 'domicilio_region', 'retiro'):
        session['entrega'] = tipo
        session.modified = True
    return redirect(url_for('carrito'))


# =========================
# CHECKOUT
# =========================
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    items = session.get('carrito', [])
    if not items:
        return redirect(url_for('carrito'))
    entrega  = session.get('entrega', 'domicilio_rm')
    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    envio    = _costos(entrega)
    total    = subtotal + envio
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
        return redirect(url_for('pago'))
    return render_template('checkout.html', items=items, subtotal=subtotal,
                           envio=envio, total=total, entrega=entrega,
                           usuario=session.get('usuario', ''))


# =========================
# PAGO (flujo de sesión)
# =========================
@app.route('/pago')
def pago():
    items = session.get('carrito', [])
    if not items:
        return redirect(url_for('carrito'))
    entrega  = session.get('entrega', 'domicilio_rm')
    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    envio    = _costos(entrega)
    total    = subtotal + envio
    return render_template('pago_form.html', items=items, subtotal=subtotal,
                           envio=envio, total=total, entrega=entrega)


@app.route('/pago/procesar', methods=['POST'])
def pago_procesar():
    items = session.get('carrito', [])
    if not items:
        return redirect(url_for('carrito'))
    entrega  = session.get('entrega', 'domicilio_rm')
    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    envio    = _costos(entrega)
    total    = subtotal + envio

    nombre  = request.form.get('nombre_tarjeta', '').strip()
    numero  = request.form.get('numero_tarjeta', '').replace(' ', '')
    expira  = request.form.get('expiracion', '').strip()
    cvv     = request.form.get('cvv', '').strip()

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
        cliente_email  = session.get('datos_envio', {}).get('email', '')
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
            p = Producto.query.get(item['id'])
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


# =========================
# HISTORIAL Y DETALLE PEDIDO
# =========================
@app.route('/historial')
def historial():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    usuario_id = session.get('usuario_id')
    if session.get('rol') == 'Admin':
        pedidos = Pedido.query.order_by(Pedido.id.desc()).all()
    else:
        usuario = Usuario.query.get(usuario_id)
        pedidos = Pedido.query.filter_by(
            cliente_email=usuario.email if usuario else ''
        ).order_by(Pedido.id.desc()).all()
    filas = [{'id_orden': p.id, 'fecha_orden': '—', 'total': p.total,
               'estado': p.estado, 'codigo_transaccion': p.mp_payment_id or '—'}
             for p in pedidos]
    return render_template('historial.html', pedidos=filas)


@app.route('/pedido/<int:id>')
def detalle_pedido(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    pedido = Pedido.query.get_or_404(id)
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


# =========================
# PANEL ADMIN
# =========================
@app.route('/admin')
@requiere_admin
def dashboard():
    productos = Producto.query.all()
    pedidos = Pedido.query.all()
    usuarios = Usuario.query.all()
    return render_template('dashboard.html', productos=productos, pedidos=pedidos, usuarios=usuarios)

@app.route('/admin/panel')
@requiere_admin
def admin_dashboard():
    return redirect(url_for('dashboard'))


@app.route('/admin/productos')
@requiere_admin
def productos():
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)


@app.route('/admin/agregar', methods=['GET', 'POST'])
@requiere_admin
def agregar_producto():
    if request.method == 'POST':
        nuevo = Producto(
            nombre=request.form['nombre'],
            descripcion=request.form['descripcion'],
            imagen=request.form['imagen'],
            categoria=request.form['categoria'],
            precio=float(request.form['precio']),
            stock=int(request.form['stock']),
            estado=request.form['estado']
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Producto agregado correctamente.', 'success')
        return redirect(url_for('productos'))
    return render_template('agregar_producto.html')


@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
@requiere_admin
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.imagen = request.form['imagen']
        producto.categoria = request.form['categoria']
        producto.precio = float(request.form['precio'])
        producto.stock = int(request.form['stock'])
        producto.estado = request.form['estado']
        db.session.commit()
        flash('Producto actualizado.', 'success')
        return redirect(url_for('productos'))
    return render_template('editar_producto.html', producto=producto)


@app.route('/admin/eliminar/<int:id>', methods=['POST'])
@requiere_admin
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado.', 'success')
    return redirect(url_for('productos'))


@app.route('/admin/pedidos')
@requiere_admin
def pedidos():
    pedidos = Pedido.query.all()
    return render_template('pedidos.html', pedidos=pedidos)


@app.route('/admin/usuarios')
@requiere_admin
def usuarios():
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/admin/actualizar_rol/<int:id>', methods=['POST'])
@requiere_admin
def actualizar_rol(id):
    usuario = Usuario.query.get_or_404(id)
    usuario.rol = request.form['rol']
    db.session.commit()
    flash('Rol actualizado.', 'success')
    return redirect(url_for('usuarios'))


# =========================
# PANEL VENDEDOR
# =========================
@app.route('/vendedor')
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


@app.route('/vendedor/pedidos')
@requiere_vendedor
def vendedor_pedidos():
    vendedor_id = session.get('usuario_id')
    pedidos = Pedido.query.filter_by(vendedor_id=vendedor_id).all()
    return render_template('vendedor_pedidos.html', pedidos=pedidos)


@app.route('/vendedor/catalogo')
@requiere_vendedor
def vendedor_catalogo():
    productos = Producto.query.filter_by(estado='Activo').all()
    return render_template('vendedor_catalogo.html', productos=productos)


@app.route('/vendedor/estadisticas')
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


@app.route('/vendedor/crear_pedido', methods=['GET', 'POST'])
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
            preference = crear_preferencia_mp(items, cliente, cliente_email, nuevo_pedido.id)
            if preference.get("id"):
                nuevo_pedido.mp_preference_id = preference["id"]
                db.session.commit()
                checkout_url = preference.get("sandbox_init_point") or preference.get("init_point")
                return redirect(checkout_url)
            flash('Pedido creado pero MP no respondió correctamente.', 'warning')
            return redirect(url_for('vendedor_pedidos'))
        except Exception as e:
            flash(f'Error Mercado Pago: {e}', 'danger')
            return redirect(url_for('vendedor_pedidos'))
    return render_template('vendedor_crear_pedido.html', productos=productos)


# =========================
# MERCADO PAGO - CALLBACKS
# =========================
def _actualizar_pedido_desde_pago(payment_id, external_ref, status_fallback=None):
    """Verifica el pago via API de MP y actualiza el pedido en BD."""
    if not external_ref:
        return
    try:
        pedido = Pedido.query.get(int(external_ref))
    except (ValueError, TypeError):
        return
    if not pedido:
        return

    status = status_fallback
    if payment_id:
        try:
            payment_info = sdk.payment().get(payment_id)
            payment = payment_info.get("response", {})
            status = payment.get("status", status_fallback)
            payment_id = str(payment.get("id", payment_id))
        except Exception:
            pass

    if payment_id:
        pedido.mp_payment_id = str(payment_id)
    if status:
        pedido.mp_status = status

    if status == 'approved' and pedido.estado != 'Pagado':
        pedido.estado = 'Pagado'
        if pedido.items_json:
            try:
                for item in json.loads(pedido.items_json):
                    prod = Producto.query.get(item['id'])
                    if prod:
                        prod.stock = max(0, prod.stock - item['cantidad'])
                        if prod.stock == 0:
                            prod.estado = 'Agotado'
            except Exception:
                pass
    elif status == 'rejected':
        pedido.estado = 'Rechazado'
    elif status == 'pending':
        pedido.estado = 'Pendiente'

    db.session.commit()


@app.route('/mp/success')
def mp_success():
    payment_id = request.args.get('payment_id')
    external_ref = request.args.get('external_reference')
    status = request.args.get('status')
    _actualizar_pedido_desde_pago(payment_id, external_ref, status_fallback=status or 'approved')
    flash('¡Pago realizado con éxito!', 'success')
    rol = session.get('rol')
    if rol in ('Vendedor', 'Admin'):
        return redirect(url_for('vendedor_pedidos'))
    return redirect(url_for('mis_pedidos'))


@app.route('/mp/failure')
def mp_failure():
    payment_id = request.args.get('payment_id')
    external_ref = request.args.get('external_reference')
    status = request.args.get('status')
    _actualizar_pedido_desde_pago(payment_id, external_ref, status_fallback=status or 'rejected')
    flash('El pago fue rechazado. Intenta nuevamente.', 'danger')
    rol = session.get('rol')
    if rol in ('Vendedor', 'Admin'):
        return redirect(url_for('vendedor_pedidos'))
    return redirect(url_for('catalogo'))


@app.route('/mp/pending')
def mp_pending():
    payment_id = request.args.get('payment_id')
    external_ref = request.args.get('external_reference')
    status = request.args.get('status')
    _actualizar_pedido_desde_pago(payment_id, external_ref, status_fallback=status or 'pending')
    flash('Pago pendiente de confirmación.', 'warning')
    rol = session.get('rol')
    if rol in ('Vendedor', 'Admin'):
        return redirect(url_for('vendedor_pedidos'))
    return redirect(url_for('mis_pedidos'))


@app.route('/mp/webhook', methods=['POST'])
def mp_webhook():
    data = request.get_json(silent=True) or {}
    topic = data.get('type') or request.args.get('topic')
    if topic == 'payment':
        payment_id = data.get('data', {}).get('id') or request.args.get('id')
        if payment_id:
            try:
                payment_info = sdk.payment().get(payment_id)
                payment = payment_info.get("response", {})
                external_ref = payment.get("external_reference")
                status = payment.get("status")
                _actualizar_pedido_desde_pago(str(payment_id), external_ref, status_fallback=status)
            except Exception:
                pass
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)