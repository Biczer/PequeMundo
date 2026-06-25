from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import Producto

carrito_bp = Blueprint('carrito', __name__)

COSTO_RM = 9990
COSTO_REGION = 14990


def _costos(entrega):
    mapa = {
        'domicilio_rm': COSTO_RM,
        'domicilio_region': COSTO_REGION,
        'retiro': 0
    }

    return mapa.get(entrega, COSTO_RM)



@carrito_bp.route('/carrito')
def carrito():

    items = session.get('carrito', [])

    entrega = session.get(
        'entrega',
        'domicilio_rm'
    )

    subtotal = sum(
        item['precio'] * item['cantidad']
        for item in items
    )

    total = subtotal + _costos(entrega)


    return render_template(
        'carrito.html',
        items=items,
        subtotal=subtotal,
        total=total,
        entrega=entrega,
        costo_rm=COSTO_RM,
        costo_region=COSTO_REGION
    )




# AGREGAR PRODUCTO
@carrito_bp.route('/carrito/agregar/<int:id_producto>')
def agregar_al_carrito(id_producto):

    producto = Producto.query.filter_by(
        id_producto=id_producto,
        estado='Activo'
    ).first()


    if not producto:

        return redirect(
            url_for('publico.catalogo')
        )



    items = session.get(
        'carrito',
        []
    )


    existe = False


    for item in items:


        if item['id_producto'] == id_producto:


            if item['cantidad'] < producto.stock:

                item['cantidad'] += 1


            existe = True

            break




    if not existe:


        items.append({

            'id_producto': producto.id_producto,

            'nombre': producto.nombre,

            'precio': int(producto.precio),

            'cantidad': 1,

            'imagen': producto.imagen

        })



    session['carrito'] = items

    session.modified = True



    if request.headers.get(
        'X-Requested-With'
    ) == 'XMLHttpRequest':


        return jsonify({
            'ok': True
        })



    return redirect(
        url_for('carrito.carrito')
    )





# AUMENTAR CANTIDAD
@carrito_bp.route('/carrito/aumentar/<int:id_producto>')
def aumentar_cantidad(id_producto):


    items = session.get(
        'carrito',
        []
    )


    for item in items:


        if item['id_producto'] == id_producto:


            item['cantidad'] += 1

            break



    session['carrito'] = items

    session.modified = True



    return redirect(
        url_for('carrito.carrito')
    )





# DISMINUIR CANTIDAD
@carrito_bp.route('/carrito/disminuir/<int:id_producto>')
def disminuir_cantidad(id_producto):


    items = session.get(
        'carrito',
        []
    )


    for item in items:


        if item['id_producto'] == id_producto:



            if item['cantidad'] > 1:


                item['cantidad'] -= 1



            else:


                items.remove(item)



            break




    session['carrito'] = items

    session.modified = True



    return redirect(
        url_for('carrito.carrito')
    )





# ELIMINAR PRODUCTO
@carrito_bp.route('/carrito/eliminar/<int:id_producto>')
def eliminar_del_carrito(id_producto):


    items = session.get(
        'carrito',
        []
    )


    session['carrito'] = [

        item for item in items

        if item['id_producto'] != id_producto

    ]



    session.modified = True



    return redirect(
        url_for('carrito.carrito')
    )





# VACIAR CARRITO
@carrito_bp.route('/carrito/vaciar')
def vaciar_carrito():


    session['carrito'] = []

    session.modified = True



    return redirect(
        url_for('carrito.carrito')
    )





# CAMBIAR ENTREGA
@carrito_bp.route('/carrito/entrega/<tipo>')
def cambiar_entrega(tipo):


    if tipo in (
        'domicilio_rm',
        'domicilio_region',
        'retiro'
    ):


        session['entrega'] = tipo

        session.modified = True



    return redirect(
        url_for('carrito.carrito')
    )
