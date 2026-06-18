from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import Usuario

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
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
                return redirect(url_for('admin.admin_dashboard'))
            elif usuario.rol == 'Vendedor':
                return redirect(url_for('vendedor.vendedor_dashboard'))
            else:
                return redirect(url_for('publico.inicio'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
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
        return redirect(url_for('auth.login'))
    return render_template('registro.html')


@auth_bp.route('/cerrar_sesion')
def cerrar_sesion():
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('publico.inicio'))
