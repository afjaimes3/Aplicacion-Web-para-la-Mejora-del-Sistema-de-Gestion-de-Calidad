import functools
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from db import get_db_connection

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db_connection()
        error = None
        user = db.execute(
            'SELECT * FROM usuarios WHERE username = ?', (username,)
        ).fetchone()
        db.close()

        if user is None:
            error = 'Usuario incorrecto.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Contraseña incorrecta.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['user_role'] = user['rol']
            
            if user['rol'] == 'admin':
                return redirect(url_for('menu.admin_menu'))
            else:
                return redirect(url_for('menu.user_menu'))

        flash(error)

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        conn = get_db_connection()
        g.user = conn.execute(
            'SELECT * FROM usuarios WHERE id = ?', (user_id,)
        ).fetchone()
        conn.close()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user['rol'] != 'admin':
             # Optionally flash specific error
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view
