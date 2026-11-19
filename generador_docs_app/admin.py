import functools
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash
from db import get_db_connection
from auth import login_required, admin_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/usuarios')
@admin_required
def gestion_usuarios():
    conn = get_db_connection()
    usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    conn.close()
    return render_template('admin/gestion_usuarios.html', usuarios=usuarios)

@bp.route('/usuarios/crear', methods=('GET', 'POST'))
@admin_required
def crear_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nombre_completo = request.form.get('nombre_completo')
        email = request.form.get('email')
        rol = request.form['rol']
        
        db = get_db_connection()
        error = None

        if not username:
            error = 'El usuario es requerido.'
        elif not password:
            error = 'La contraseña es requerida.'

        # Normalizar email a None si está vacío para permitir múltiples usuarios sin email (si la columna lo permite)
        # Sin embargo, la columna es UNIQUE, así que solo permite múltiples NULLs, no "" vacíos.
        if not email:
            email = None

        if error is None:
            # Validaciones manuales para dar feedback preciso
            user_exists = db.execute('SELECT id FROM usuarios WHERE username = ?', (username,)).fetchone()
            email_exists = None
            if email:
                email_exists = db.execute('SELECT id FROM usuarios WHERE email = ?', (email,)).fetchone()

            if user_exists:
                error = f"El usuario {username} ya existe."
            elif email_exists:
                error = f"El email {email} ya está registrado en otro usuario."
            else:
                try:
                    db.execute(
                        'INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol) VALUES (?, ?, ?, ?, ?)',
                        (username, generate_password_hash(password), nombre_completo, email, rol)
                    )
                    db.commit()
                    return redirect(url_for('admin.gestion_usuarios'))
                except db.IntegrityError as e:
                    error = f"Error de integridad en base de datos: {e}"
                
        flash(error)
        db.close()

    return render_template('admin/crear_usuario.html')

@bp.route('/usuarios/<int:id>/editar', methods=('GET', 'POST'))
@admin_required
def editar_usuario(id):
    db = get_db_connection()
    user = db.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()

    if user is None:
        abort(404, f"Usuario id {id} no existe.")

    if request.method == 'POST':
        username = request.form['username']
        nombre_completo = request.form.get('nombre_completo')
        email = request.form.get('email')
        rol = request.form['rol']
        password = request.form.get('password') # Optional

        error = None

        if not username:
            error = 'El usuario es requerido.'

        # Normalizar email
        if not email:
            email = None

        if error is None:
            # Validaciones de existencia (excluyendo al propio usuario actual)
            user_exists = db.execute('SELECT id FROM usuarios WHERE username = ? AND id != ?', (username, id)).fetchone()
            email_exists = None
            if email:
                email_exists = db.execute('SELECT id FROM usuarios WHERE email = ? AND id != ?', (email, id)).fetchone()

            if user_exists:
                error = f"El usuario {username} ya está en uso por otra cuenta."
            elif email_exists:
                error = f"El email {email} ya está registrado en otra cuenta."
            else:
                try:
                    if password:
                        db.execute(
                            'UPDATE usuarios SET username = ?, password_hash = ?, nombre_completo = ?, email = ?, rol = ? WHERE id = ?',
                            (username, generate_password_hash(password), nombre_completo, email, rol, id)
                        )
                    else:
                        db.execute(
                            'UPDATE usuarios SET username = ?, nombre_completo = ?, email = ?, rol = ? WHERE id = ?',
                            (username, nombre_completo, email, rol, id)
                        )
                    db.commit()
                    return redirect(url_for('admin.gestion_usuarios'))
                except db.IntegrityError as e:
                    error = f"Error de integridad: {e}"
        
        flash(error)
    
    db.close()
    return render_template('admin/editar_usuario.html', user=user)

@bp.route('/usuarios/<int:id>/eliminar', methods=('POST',))
@admin_required
def eliminar_usuario(id):
    db = get_db_connection()
    db.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash('Usuario eliminado.')
    return redirect(url_for('admin.gestion_usuarios'))


# --- Gestión de Nomenclaturas ---

@bp.route('/nomenclaturas')
@admin_required
def gestion_nomenclaturas():
    return render_template('admin/nomenclaturas/index.html')

# --- Procesos ---

@bp.route('/nomenclaturas/procesos')
@admin_required
def gestion_procesos():
    conn = get_db_connection()
    procesos = conn.execute('SELECT * FROM procesos ORDER BY nombre').fetchall()
    conn.close()
    return render_template('admin/nomenclaturas/procesos.html', procesos=procesos)

@bp.route('/nomenclaturas/procesos/crear', methods=('GET', 'POST'))
@admin_required
def crear_proceso():
    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        db = get_db_connection()
        error = None

        if not codigo:
            error = 'El código es requerido.'
        elif not nombre:
            error = 'El nombre es requerido.'

        if error is None:
            try:
                db.execute(
                    'INSERT INTO procesos (codigo, nombre) VALUES (?, ?)',
                    (codigo, nombre)
                )
                db.commit()
            except db.IntegrityError:
                error = f"El proceso con código {codigo} ya existe."
            except Exception as e:
                error = f"Error: {e}"
            else:
                db.close()
                return redirect(url_for('admin.gestion_procesos'))
        
        flash(error)
        db.close()

    return render_template('admin/nomenclaturas/crear_proceso.html')

@bp.route('/nomenclaturas/procesos/<codigo>/editar', methods=('GET', 'POST'))
@admin_required
def editar_proceso(codigo):
    db = get_db_connection()
    proceso = db.execute('SELECT * FROM procesos WHERE codigo = ?', (codigo,)).fetchone()

    if proceso is None:
        db.close()
        flash(f"Proceso con código {codigo} no existe.")
        return redirect(url_for('admin.gestion_procesos'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        error = None

        if not nombre:
            error = 'El nombre es requerido.'

        if error is None:
            db.execute(
                'UPDATE procesos SET nombre = ? WHERE codigo = ?',
                (nombre, codigo)
            )
            db.commit()
            db.close()
            return redirect(url_for('admin.gestion_procesos'))
        
        flash(error)
    
    db.close()
    return render_template('admin/nomenclaturas/editar_proceso.html', proceso=proceso)

@bp.route('/nomenclaturas/procesos/<codigo>/eliminar', methods=('POST',))
@admin_required
def eliminar_proceso(codigo):
    db = get_db_connection()
    # Check dependencies before delete?
    # Usually subprocesos depend on procesos.
    count = db.execute('SELECT COUNT(*) FROM subprocesos WHERE codigo_proceso = ?', (codigo,)).fetchone()[0]
    if count > 0:
        flash(f'No se puede eliminar el proceso {codigo} porque tiene {count} subprocesos asociados.')
    else:
        db.execute('DELETE FROM procesos WHERE codigo = ?', (codigo,))
        db.commit()
        flash('Proceso eliminado.')
    
    db.close()
    return redirect(url_for('admin.gestion_procesos'))


# --- Tipos de Documento ---

@bp.route('/nomenclaturas/tipos_documento')
@admin_required
def gestion_tipos_documento():
    conn = get_db_connection()
    tipos = conn.execute('SELECT * FROM tipos_documento ORDER BY nombre').fetchall()
    conn.close()
    return render_template('admin/nomenclaturas/tipos_documento.html', tipos=tipos)

@bp.route('/nomenclaturas/tipos_documento/crear', methods=('GET', 'POST'))
@admin_required
def crear_tipo_documento():
    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        db = get_db_connection()
        error = None

        if not codigo:
            error = 'El código es requerido.'
        elif not nombre:
            error = 'El nombre es requerido.'

        if error is None:
            try:
                db.execute(
                    'INSERT INTO tipos_documento (codigo, nombre) VALUES (?, ?)',
                    (codigo, nombre)
                )
                db.commit()
            except db.IntegrityError:
                error = f"El tipo de documento con código {codigo} ya existe."
            else:
                db.close()
                return redirect(url_for('admin.gestion_tipos_documento'))
        
        flash(error)
        db.close()

    return render_template('admin/nomenclaturas/crear_tipo_documento.html')

@bp.route('/nomenclaturas/tipos_documento/<codigo>/editar', methods=('GET', 'POST'))
@admin_required
def editar_tipo_documento(codigo):
    db = get_db_connection()
    tipo = db.execute('SELECT * FROM tipos_documento WHERE codigo = ?', (codigo,)).fetchone()

    if tipo is None:
        db.close()
        flash(f"Tipo de documento con código {codigo} no existe.")
        return redirect(url_for('admin.gestion_tipos_documento'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        error = None

        if not nombre:
            error = 'El nombre es requerido.'

        if error is None:
            db.execute(
                'UPDATE tipos_documento SET nombre = ? WHERE codigo = ?',
                (nombre, codigo)
            )
            db.commit()
            db.close()
            return redirect(url_for('admin.gestion_tipos_documento'))
        
        flash(error)
    
    db.close()
    return render_template('admin/nomenclaturas/editar_tipo_documento.html', tipo=tipo)

@bp.route('/nomenclaturas/tipos_documento/<codigo>/eliminar', methods=('POST',))
@admin_required
def eliminar_tipo_documento(codigo):
    db = get_db_connection()
    db.execute('DELETE FROM tipos_documento WHERE codigo = ?', (codigo,))
    db.commit()
    db.close()
    flash('Tipo de documento eliminado.')
    return redirect(url_for('admin.gestion_tipos_documento'))


# --- Subprocesos ---

@bp.route('/nomenclaturas/subprocesos')
@admin_required
def gestion_subprocesos():
    conn = get_db_connection()
    subprocesos = conn.execute('''
        SELECT s.*, p.nombre as nombre_proceso 
        FROM subprocesos s 
        JOIN procesos p ON s.codigo_proceso = p.codigo
        ORDER BY p.nombre, s.nombre
    ''').fetchall()
    conn.close()
    return render_template('admin/nomenclaturas/subprocesos.html', subprocesos=subprocesos)

@bp.route('/nomenclaturas/subprocesos/crear', methods=('GET', 'POST'))
@admin_required
def crear_subproceso():
    db = get_db_connection()
    if request.method == 'POST':
        codigo_proceso = request.form['codigo_proceso']
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        error = None

        if not codigo:
            error = 'El código es requerido.'
        elif not nombre:
            error = 'El nombre es requerido.'
        elif not codigo_proceso:
            error = 'El proceso es requerido.'

        if error is None:
            try:
                db.execute(
                    'INSERT INTO subprocesos (codigo_proceso, codigo, nombre) VALUES (?, ?, ?)',
                    (codigo_proceso, codigo, nombre)
                )
                db.commit()
            except Exception as e:
                error = f"Error al crear subproceso: {e}"
            else:
                db.close()
                return redirect(url_for('admin.gestion_subprocesos'))
        
        flash(error)

    procesos = db.execute('SELECT * FROM procesos ORDER BY nombre').fetchall()
    db.close()
    return render_template('admin/nomenclaturas/crear_subproceso.html', procesos=procesos)

@bp.route('/nomenclaturas/subprocesos/<int:id>/editar', methods=('GET', 'POST'))
@admin_required
def editar_subproceso(id):
    db = get_db_connection()
    subproceso = db.execute('SELECT * FROM subprocesos WHERE id = ?', (id,)).fetchone()

    if subproceso is None:
        db.close()
        flash(f"Subproceso con ID {id} no existe.")
        return redirect(url_for('admin.gestion_subprocesos'))

    if request.method == 'POST':
        codigo_proceso = request.form['codigo_proceso']
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        error = None

        if not codigo:
            error = 'El código es requerido.'
        elif not nombre:
            error = 'El nombre es requerido.'

        if error is None:
            db.execute(
                'UPDATE subprocesos SET codigo_proceso = ?, codigo = ?, nombre = ? WHERE id = ?',
                (codigo_proceso, codigo, nombre, id)
            )
            db.commit()
            db.close()
            return redirect(url_for('admin.gestion_subprocesos'))
        
        flash(error)
    
    procesos = db.execute('SELECT * FROM procesos ORDER BY nombre').fetchall()
    db.close()
    return render_template('admin/nomenclaturas/editar_subproceso.html', subproceso=subproceso, procesos=procesos)

@bp.route('/nomenclaturas/subprocesos/<int:id>/eliminar', methods=('POST',))
@admin_required
def eliminar_subproceso(id):
    db = get_db_connection()
    db.execute('DELETE FROM subprocesos WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash('Subproceso eliminado.')
    return redirect(url_for('admin.gestion_subprocesos'))


# --- Gestión de Estilos (Standardizer) ---

@bp.route('/estilos', methods=('GET', 'POST'))
@admin_required
def gestion_estilos():
    db = get_db_connection()
    if request.method == 'POST':
        # Estamos recibiendo un formulario para actualizar un tipo de estilo específico
        # El form debe tener un campo hidden 'style_type' o iteramos por prefijos
        
        # Estrategia: Iteramos por los dos posibles tipos si vienen en el form
        types = ['Procedimiento', 'Formato']
        
        try:
            for t in types:
                # Verificamos si este tipo está siendo enviado (mirando un campo clave)
                # O simplemente asumimos que el form manda todo.
                # Usaremos prefixes: proc_body_font_family, form_body_font_family, etc.
                # O mejor, un id_estilo hidden.
                pass 
            
            # Simplificación: El form envía datos para un ID específico
            style_id = request.form.get('style_id')
            if style_id:
                # 1. Recuperar tipo de estilo
                current = db.execute('SELECT style_type FROM document_styles WHERE id = ?', (style_id,)).fetchone()
                style_type = current['style_type'] if current else ''

                # 2. Obtener valores del formulario (variables mutables)
                vals = {
                    'bf_fam': request.form['body_font_family'],
                    'bf_sz': request.form['body_font_size'],
                    'bf_col': request.form['body_font_color'],
                    'tf_fam': request.form['title_font_family'],
                    'tf_sz': request.form['title_font_size'],
                    'tf_col': request.form['title_font_color'],
                    'th_fill': request.form['table_header_fill'],
                    'th_col': request.form['table_header_text_color'],
                    'hc_fill': request.form['header_code_fill'],
                    'hc_col': request.form['header_code_text_color']
                }

                # 3. Actualizar DB
                db.execute('''
                    UPDATE document_styles SET
                        body_font_family = ?, body_font_size = ?, body_font_color = ?,
                        title_font_family = ?, title_font_size = ?, title_font_color = ?,
                        table_header_fill = ?, table_header_text_color = ?,
                        header_code_fill = ?, header_code_text_color = ?,
                        margin_top = ?, margin_bottom = ?, margin_left = ?, margin_right = ?
                    WHERE id = ?
                ''', (
                    vals['bf_fam'], vals['bf_sz'], vals['bf_col'],
                    vals['tf_fam'], vals['tf_sz'], vals['tf_col'],
                    vals['th_fill'], vals['th_col'],
                    vals['hc_fill'], vals['hc_col'],
                    request.form['margin_top'], request.form['margin_bottom'], request.form['margin_left'], request.form['margin_right'],
                    style_id
                ))
                db.commit()
                flash('Estilo actualizado correctamente.')
        except Exception as e:
            flash(f'Error al actualizar: {e}')
        
        db.close()
        return redirect(url_for('admin.gestion_estilos'))

    estilos = db.execute('SELECT * FROM document_styles').fetchall()
    db.close()
    return render_template('admin/gestion_estilos.html', estilos=estilos)


