from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Producto, Pedido, Usuario
from decorators import requiere_admin

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@requiere_admin
def dashboard():
    productos = Producto.query.all()
    pedidos = Pedido.query.all()
    usuarios = Usuario.query.all()
    return render_template('dashboard.html', productos=productos, pedidos=pedidos, usuarios=usuarios)


@admin_bp.route('/admin/panel')
@requiere_admin
def admin_dashboard():
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/admin/productos')
@requiere_admin
def productos():
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)


@admin_bp.route('/admin/agregar', methods=['GET', 'POST'])
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
        return redirect(url_for('admin.productos'))
    return render_template('agregar_producto.html')


@admin_bp.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
@requiere_admin
def editar_producto(id):
    producto = db.session.get(Producto, id)
    if not producto:
        from flask import abort
        abort(404)
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
        return redirect(url_for('admin.productos'))
    return render_template('editar_producto.html', producto=producto)


@admin_bp.route('/admin/eliminar/<int:id>', methods=['POST'])
@requiere_admin
def eliminar_producto(id):
    producto = db.session.get(Producto, id)
    if not producto:
        from flask import abort
        abort(404)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado.', 'success')
    return redirect(url_for('admin.productos'))


@admin_bp.route('/admin/pedidos')
@requiere_admin
def pedidos():
    pedidos = Pedido.query.all()
    return render_template('pedidos.html', pedidos=pedidos)


@admin_bp.route('/admin/usuarios')
@requiere_admin
def usuarios():
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)


@admin_bp.route('/admin/actualizar_rol/<int:id>', methods=['POST'])
@requiere_admin
def actualizar_rol(id):
    usuario = db.session.get(Usuario, id)
    if not usuario:
        from flask import abort
        abort(404)
    usuario.rol = request.form['rol']
    db.session.commit()
    flash('Rol actualizado.', 'success')
    return redirect(url_for('admin.usuarios'))
