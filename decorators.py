from functools import wraps
from flask import session, flash, redirect, url_for


def requiere_admin(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if session.get('rol') != 'Admin':
            flash('Debes iniciar sesión como administrador.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorado


def requiere_vendedor(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if session.get('rol') not in ('Vendedor', 'Admin'):
            flash('Debes iniciar sesión como vendedor.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorado


def requiere_cliente(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if not session.get('usuario_id'):
            flash('Debes iniciar sesión para comprar.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorado
