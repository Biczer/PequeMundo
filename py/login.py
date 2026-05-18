from flask import Blueprint, render_template, request, redirect, url_for, session, flash

login_bp = Blueprint('login', __name__)

# Usuarios de prueba (reemplazar con consulta a base de datos)
USUARIOS = {
    "cliente@ejemplo.com": {"password": "1234", "nombre": "Cliente"},
    "admin@pequemundo.cl": {"password": "admin123", "nombre": "Admin"},
}


@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está logueado, redirigir al catálogo
    if 'usuario' in session:
        return redirect(url_for('catalogo.catalogo'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        usuario = USUARIOS.get(email)

        if usuario and usuario['password'] == password:
            session['usuario'] = email
            session['nombre']  = usuario['nombre']
            return redirect(url_for('catalogo.catalogo'))
        else:
            flash('Correo o contraseña incorrectos.')
            return redirect(url_for('login.login'))

    return render_template('login.html')


@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.login'))
