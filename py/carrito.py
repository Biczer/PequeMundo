from flask import Blueprint, render_template, redirect, url_for, session

carrito_bp = Blueprint('carrito', __name__)

# Costos de despacho (en pesos chilenos)
COSTO_RM     = 3990
COSTO_REGION = 6990

# Simulación de productos (reemplazar con consulta a BD)
PRODUCTOS_DB = {
    1: {"id": 1, "nombre": "Cama Infantil Estrella",  "precio": 129990, "imagen": "cama_estrella.png"},
    2: {"id": 2, "nombre": "Escritorio Arcoíris",     "precio": 89990,  "imagen": "escritorio.png"},
    3: {"id": 3, "nombre": "Repisa Nube",              "precio": 34990,  "imagen": "repisa.png"},
    4: {"id": 4, "nombre": "Organizador Cohete",       "precio": 49990,  "imagen": "organizador.png"},
}


def obtener_carrito():
    """Retorna el carrito actual desde la sesión."""
    return session.get('carrito', {})   # { str(producto_id): cantidad }


def calcular_totales(carrito, entrega):
    """Calcula subtotal, costo de despacho y total."""
    items = []
    subtotal = 0

    for prod_id_str, cantidad in carrito.items():
        prod = PRODUCTOS_DB.get(int(prod_id_str))
        if prod:
            items.append({**prod, "cantidad": cantidad})
            subtotal += prod["precio"] * cantidad

    if entrega == 'domicilio_rm':
        despacho = COSTO_RM
    elif entrega == 'domicilio_region':
        despacho = COSTO_REGION
    else:   # retiro en tienda
        despacho = 0

    total = subtotal + despacho
    return items, subtotal, total


# ─────────────────────────────────────────
#  RUTAS
# ─────────────────────────────────────────

@carrito_bp.route('/carrito')
def carrito():
    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    carrito  = obtener_carrito()
    entrega  = session.get('entrega', 'retiro')
    items, subtotal, total = calcular_totales(carrito, entrega)

    return render_template(
        'carrito.html',
        items       = items,
        subtotal    = subtotal,
        total       = total,
        entrega     = entrega,
        costo_rm    = COSTO_RM,
        costo_region= COSTO_REGION,
    )


@carrito_bp.route('/carrito/agregar/<int:producto_id>')
def agregar(producto_id):
    """Agrega 1 unidad del producto al carrito."""
    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    carrito = obtener_carrito()
    key     = str(producto_id)
    carrito[key] = carrito.get(key, 0) + 1
    session['carrito'] = carrito
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/aumentar/<int:producto_id>')
def aumentar(producto_id):
    """Aumenta en 1 la cantidad del producto."""
    carrito = obtener_carrito()
    key     = str(producto_id)
    if key in carrito:
        carrito[key] += 1
        session['carrito'] = carrito
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/disminuir/<int:producto_id>')
def disminuir(producto_id):
    """Disminuye en 1 la cantidad; si llega a 0 lo elimina."""
    carrito = obtener_carrito()
    key     = str(producto_id)
    if key in carrito:
        carrito[key] -= 1
        if carrito[key] <= 0:
            del carrito[key]
        session['carrito'] = carrito
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/eliminar/<int:producto_id>')
def eliminar(producto_id):
    """Elimina el producto del carrito."""
    carrito = obtener_carrito()
    carrito.pop(str(producto_id), None)
    session['carrito'] = carrito
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/vaciar')
def vaciar():
    """Vacía el carrito completamente."""
    session['carrito'] = {}
    return redirect(url_for('carrito.carrito'))


@carrito_bp.route('/carrito/entrega/<tipo>')
def cambiar_entrega(tipo):
    """Cambia el tipo de entrega seleccionado."""
    if tipo in ('domicilio_rm', 'domicilio_region', 'retiro'):
        session['entrega'] = tipo
    return redirect(url_for('carrito.carrito'))
