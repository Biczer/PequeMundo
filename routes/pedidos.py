import json

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from extensions import db
from models import Producto, Usuario, Pedido
from decorators import requiere_cliente
from services.mercadopago_service import crear_preferencia


pedidos_bp = Blueprint('pedidos', __name__)


COSTO_RM = 9990
COSTO_REGION = 14990


def _costos(entrega):

    mapa = {
        'domicilio_rm': COSTO_RM,
        'domicilio_region': COSTO_REGION,
        'retiro': 0
    }

    return mapa.get(entrega, COSTO_RM)



# ==============================
# CHECKOUT MERCADO PAGO
# ==============================

@pedidos_bp.route('/carrito/checkout', methods=['POST'])
def checkout_json():

    if not session.get('usuario_id'):
        return jsonify({
            'error': 'Debes iniciar sesión para comprar.'
        }), 401


    data = request.get_json(silent=True) or {}

    items = data.get('items', [])


    if not items:
        return jsonify({
            'error': 'Carrito vacío'
        }),400



    usuario = db.session.get(
    Usuario,
    session.get('usuario_id')
    )


    if not usuario:
        return jsonify({
            "error": "Usuario no encontrado"
        }),400


    total = sum(
        i['precio'] * i['cantidad']
        for i in items
    )



    # VALIDAR PRODUCTOS

    for item in items:

        producto_id = item.get('id_producto')


        if not producto_id:

            return jsonify({
                'error':'Producto sin id_producto'
            }),400



        producto = db.session.get(
            Producto,
            producto_id
        )


        if not producto:

            return jsonify({
                'error':'Producto no encontrado'
            }),400



        if producto.stock < item['cantidad']:

            return jsonify({
                'error':
                f'Stock insuficiente para {producto.nombre}'
            }),400




    nuevo_pedido = Pedido(

        cliente=usuario.nombre_usuario,

        cliente_email=usuario.email,

        total=total,

        estado='Pendiente',

        vendedor_id=None,

        items_json=json.dumps(items)

    )



    db.session.add(nuevo_pedido)

    db.session.commit()



    try:


        base = request.host_url.rstrip('/').replace(
            'http://',
            'https://',
            1
        )


        preference = crear_preferencia(

            items,

            usuario.nombre_usuario,

            usuario.email,

            nuevo_pedido.id_usuario,

            base

        )



        if preference.get("id"):


            nuevo_pedido.mp_preference_id = preference["id"]

            db.session.commit()


            return jsonify({

                "checkout_url":
                preference.get("sandbox_init_point")
                or preference.get("init_point")

            })



        return jsonify({
            "error":"Mercado Pago no respondió",
            "detalle":preference
        }),500



    except Exception as e:


        db.session.rollback()

        return jsonify({
            "error":str(e)
        }),500






# ==============================
# MIS PEDIDOS
# ==============================

@pedidos_bp.route('/mis-pedidos')
@requiere_cliente
def mis_pedidos():


    usuario = db.session.get(
        Usuario,
        session['usuario_id']
    )


    pedidos = Pedido.query.filter_by(
        cliente_email=usuario.email
    ).order_by(
        Pedido.id_usuario.desc()
    ).all()



    return render_template(
        'mis_pedidos.html',
        pedidos=pedidos
    )





# ==============================
# CHECKOUT DATOS ENVIO
# ==============================

@pedidos_bp.route('/checkout', methods=['GET','POST'])
def checkout():


    items = session.get('carrito',[])



    if not items:
        return redirect(
            url_for('carrito.carrito')
        )



    entrega = session.get(
        'entrega',
        'domicilio_rm'
    )


    subtotal = sum(
        i['precio'] * i['cantidad']
        for i in items
    )


    envio = _costos(entrega)


    total = subtotal + envio



    if request.method == 'POST':


        session['datos_envio']={

            'nombre':request.form.get('nombre'),

            'email':request.form.get('email'),

            'telefono':request.form.get('telefono'),

            'calle':request.form.get('calle'),

            'comuna':request.form.get('comuna'),

            'region':request.form.get('region')

        }


        return redirect(
            url_for('pedidos.pago')
        )



    return render_template(
        'checkout.html',
        items=items,
        subtotal=subtotal,
        envio=envio,
        total=total,
        entrega=entrega
    )






# ==============================
# PAGO SIMULADO
# ==============================

@pedidos_bp.route('/pago/procesar',methods=['POST'])
def pago_procesar():


    items=session.get(
        'carrito',
        []
    )


    if not items:

        return redirect(
            url_for('carrito.carrito')
        )



    total=sum(
        i['precio']*i['cantidad']
        for i in items
    )



    try:


        pedido=Pedido(

            cliente=session.get('usuario',''),

            cliente_email=session.get(
                'datos_envio',
                {}
            ).get('email',''),


            total=total,

            estado='Pagado',

            vendedor_id=None,

            mp_status='approved',

            items_json=json.dumps(items)

        )



        db.session.add(pedido)



        for item in items:


            producto=db.session.get(

                Producto,

                item['id_producto']

            )


            if producto:

                producto.stock -= item['cantidad']


                if producto.stock <= 0:

                    producto.stock=0

                    producto.estado='Agotado'



        db.session.commit()



        session['carrito']=[]


        return render_template(
            'confirmacion.html',
            pedido={
                'id_orden':pedido.id_usuario,
                'total':total,
                'estado':'Pagado'
            },
            payment_status='approved'
        )



    except Exception as e:


        db.session.rollback()


        return render_template(
            'pago_error.html',
            error=str(e)
        ),500






# ==============================
# HISTORIAL
# ==============================

@pedidos_bp.route('/historial')
def historial():


    pedidos=Pedido.query.order_by(
        Pedido.id_usuario.desc()
    ).all()



    filas=[{

        'id_orden':p.id_usuario,

        'total':p.total,

        'estado':p.estado,

        'codigo_transaccion':
        p.mp_payment_id or '—'

    } for p in pedidos]



    return render_template(
        'historial.html',
        pedidos=filas
    )






# ==============================
# DETALLE
# ==============================

@pedidos_bp.route('/pedido/<int:id>')
def detalle_pedido(id):


    pedido=db.session.get(
        Pedido,
        id
    )



    if not pedido:

        from flask import abort
        abort(404)



    items=json.loads(
        pedido.items_json
    ) if pedido.items_json else []



    return render_template(

        'detalle_pedido.html',

        pedido={

            'id_orden':
            pedido.id_usuario,

            'total':
            pedido.total,

            'estado':
            pedido.estado,

            'lineas':
            items

        }

    )
