from flask import Blueprint, render_template, request, redirect, url_for, session, flash

registro_bp = Blueprint('registro', __name__)

# Simulación de base de datos de usuarios (reemplazar con BD real)
USUARIOS = {}


@registro_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    # Si ya está logueado, redirigir al catálogo
    if 'usuario' in session:
        return redirect(url_for('catalogo.catalogo'))

    if request.method == 'POST':
        nombre             = request.form.get('nombre', '').strip()
        email              = request.form.get('email', '').strip().lower()
        telefono           = request.form.get('telefono', '').strip()
        password           = request.form.get('password', '')
        confirmar_password = request.form.get('confirmar_password', '')

        # Validaciones
        if not nombre or not email or not password:
            flash('Por favor completa todos los campos obligatorios.')
            return redirect(url_for('registro.registro'))

        if password != confirmar_password:
            flash('Las contraseñas no coinciden.')
            return redirect(url_for('registro.registro'))

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.')
            return redirect(url_for('registro.registro'))

        if email in USUARIOS:
            flash('Ya existe una cuenta con ese correo electrónico.')
            return redirect(url_for('registro.registro'))

        # Guardar usuario (reemplazar con INSERT a la BD)
        USUARIOS[email] = {
            'nombre':   nombre,
            'password': password,   # ⚠️ En producción usar hashing: werkzeug.security.generate_password_hash
            'telefono': telefono,
        }

        # Iniciar sesión automáticamente tras el registro
        session['usuario'] = email
        session['nombre']  = nombre

        return redirect(url_for('catalogo.catalogo'))

    return render_template('registro.html')
