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

    return mapa.get(
        entrega,
        COSTO_RM
    )





@pedidos_bp.route('/carrito/checkout', methods=['POST'])
def checkout_json():


    if not session.get('usuario_id'):

        return jsonify({
            'error': 'Debes iniciar sesión para comprar.'
        }), 401



    if session.get('rol') == 'Vendedor':

        return jsonify({
            'error': 'Los vendedores no pueden comprar.'
        }), 403



    data = request.get_json(
        silent=True
    ) or {}



    items = data.get(
        'items',
        []
    )



    if not items:

        return jsonify({
            'error': 'Carrito vacío'
        }), 400




    usuario = db.session.get(
        Usuario,
        session['usuario_id']
    )



    total = sum(
        item['precio'] * item['cantidad']
        for item in items
    )




    # VALIDAR STOCK

    for item in items:


        producto_id = item.get(
            'id_producto'
        )


        producto = db.session.get(
            Producto,
            producto_id
        )



        if not producto:

            return jsonify({
                'error': f"Producto no encontrado"
            }), 400



        if producto.stock < item['cantidad']:

            return jsonify({
                'error': f"Stock insuficiente para {producto.nombre}"
            }), 400






    nuevo_pedido = Pedido(

        cliente=usuario.nombre,

        cliente_email=usuario.email,

        total=total,

        estado='Pendiente',

        vendedor_id=None,

        items_json=json.dumps(items)

    )



    db.session.add(
        nuevo_pedido
    )


    db.session.commit()






    try:


        base = request.host_url.rstrip('/').replace(
            'http://',
            'https://',
            1
        )



        preference = crear_preferencia(

            items,

            usuario.nombre,

            usuario.email,

            nuevo_pedido.id,

            base

        )



        if preference.get("id"):


            nuevo_pedido.mp_preference_id = preference["id"]

            db.session.commit()



            checkout_url = (

                preference.get("sandbox_init_point")

                or preference.get("init_point")

            )



            return jsonify({

                'checkout_url': checkout_url

            })




        db.session.delete(
            nuevo_pedido
        )


        db.session.commit()



        return jsonify({

            'error': 'Mercado Pago no respondió correctamente',

            'detalle': preference

        }), 500





    except Exception as e:


        db.session.delete(
            nuevo_pedido
        )


        db.session.commit()



        return jsonify({

            'error': str(e)

        }), 500







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

        Pedido.id.desc()

    ).all()



    return render_template(

        'mis_pedidos.html',

        pedidos=pedidos

    )








@pedidos_bp.route('/checkout', methods=['GET','POST'])
def checkout():


    items = session.get(
        'carrito',
        []
    )



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



    envio = _costos(
        entrega
    )



    total = subtotal + envio




    if request.method == 'POST':


        session['datos_envio'] = {

            'nombre': request.form.get('nombre',''),

            'email': request.form.get('email',''),

            'telefono': request.form.get('telefono',''),

            'calle': request.form.get('calle',''),

            'depto': request.form.get('depto',''),

            'comuna': request.form.get('comuna',''),

            'region': request.form.get('region','')

        }



        session.modified = True



        return redirect(
            url_for('pedidos.pago')
        )





    return render_template(

        'checkout.html',

        items=items,

        subtotal=subtotal,

        envio=envio,

        total=total,

        entrega=entrega,

        usuario=session.get(
            'usuario',
            ''
        )

    )









@pedidos_bp.route('/pago')
def pago():


    items = session.get(
        'carrito',
        []
    )


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


    envio = _costos(
        entrega
    )



    total = subtotal + envio



    return render_template(

        'pago_form.html',

        items=items,

        subtotal=subtotal,

        envio=envio,

        total=total,

        entrega=entrega

    )









@pedidos_bp.route('/pago/procesar', methods=['POST'])
def pago_procesar():


    items = session.get(
        'carrito',
        []
    )


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



    envio = _costos(
        entrega
    )


    total = subtotal + envio




    try:


        cliente_nombre = session.get(
            'usuario',
            ''
        )



        cliente_email = session.get(
            'datos_envio',
            {}
        ).get(
            'email',
            ''
        )




        nuevo_pedido = Pedido(

            cliente=cliente_nombre,

            cliente_email=cliente_email,

            total=total,

            estado='Pagado',

            vendedor_id=None,

            mp_status='approved',

            items_json=json.dumps(items)

        )



        db.session.add(
            nuevo_pedido
        )





        # DESCONTAR STOCK

        for item in items:


            producto = db.session.get(

                Producto,

                item.get('id_producto')

            )


            if producto:


                producto.stock -= item['cantidad']


                if producto.stock <= 0:

                    producto.stock = 0

                    producto.estado = 'Agotado'





        db.session.commit()




        session['carrito'] = []

        session.modified = True




        return render_template(

            'confirmacion.html',

            pedido={

                'id_orden': nuevo_pedido.id,

                'total': total,

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







@pedidos_bp.route('/historial')
def historial():


    if 'usuario' not in session:

        return redirect(
            url_for('auth.login')
        )



    pedidos = Pedido.query.order_by(
        Pedido.id.desc()
    ).all()



    filas = [

        {

            'id_orden': p.id,

            'total': p.total,

            'estado': p.estado,

            'codigo_transaccion': p.mp_payment_id or '—'

        }

        for p in pedidos

    ]



    return render_template(

        'historial.html',

        pedidos=filas

    )







@pedidos_bp.route('/pedido/<int:id>')
def detalle_pedido(id):


    pedido = db.session.get(
        Pedido,
        id
    )



    if not pedido:

        from flask import abort

        abort(404)



    items = json.loads(
        pedido.items_json
    ) if pedido.items_json else []



    return render_template(

        'detalle_pedido.html',

        pedido={

            'id_orden': pedido.id,

            'total': pedido.total,

            'estado': pedido.estado,

            'lineas': items

        }

    )
