from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort, send_file, jsonify
from db import get_db_connection
from auth import admin_required
import pandas as pd
import io
import json
from datetime import datetime

bp = Blueprint('gestion_maestros', __name__, url_prefix='/maestros')

# --- Maestro de Formatos ---

@bp.route('/formatos')
@admin_required
def index_formatos():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    offset = (page - 1) * per_page

    db = get_db_connection()
    
    # Get total count for pagination
    total = db.execute('SELECT COUNT(*) FROM lista_formatos').fetchone()[0]
    total_pages = (total + per_page - 1) // per_page

    formatos = db.execute(
        'SELECT * FROM lista_formatos LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    
    db.close()
    return render_template('admin/maestros/formatos/index.html', 
                           formatos=formatos, 
                           page=page, 
                           total_pages=total_pages)

@bp.route('/formatos/crear', methods=('GET', 'POST'))
@admin_required
def crear_formato():
    _, procesos, subprocesos_dict = get_maestros_documento()
    
    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        macroproceso = request.form.get('macroproceso')
        proceso = request.form.get('proceso')
        subproceso = request.form.get('subproceso')
        version = request.form.get('version')
        fecha_actualizacion = request.form.get('fecha_actualizacion')
        fecha_caducidad = request.form.get('fecha_caducidad')
        estado = request.form.get('estado')
        url_sharepoint = request.form.get('url_sharepoint')

        db = get_db_connection()
        error = None

        if not codigo:
            error = 'El código es requerido.'
        elif not nombre:
            error = 'El nombre es requerido.'

        if error is None:
            try:
                db.execute(
                    'INSERT INTO lista_formatos (codigo, nombre, macroproceso, proceso, subproceso, version, fecha_actualizacion, fecha_caducidad, estado, url_sharepoint) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (codigo, nombre, macroproceso, proceso, subproceso, version, fecha_actualizacion, fecha_caducidad, estado, url_sharepoint)
                )
                db.commit()
                flash('Formato creado exitosamente.')
                return redirect(url_for('gestion_maestros.index_formatos'))
            except db.IntegrityError:
                error = f"El código {codigo} ya existe."
        
        flash(error)
        db.close()

    return render_template('admin/maestros/formatos/crear.html', 
                           procesos=procesos, 
                           subprocesos_json=json.dumps(subprocesos_dict),
                           macroprocesos=MACROPROCESOS)

@bp.route('/formatos/<int:id>/editar', methods=('GET', 'POST'))
@admin_required
def editar_formato(id):
    db = get_db_connection()
    formato = db.execute('SELECT * FROM lista_formatos WHERE id = ?', (id,)).fetchone()

    if formato is None:
        db.close()
        abort(404, f"Formato id {id} no existe.")

    _, procesos, subprocesos_dict = get_maestros_documento()

    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        macroproceso = request.form.get('macroproceso')
        proceso = request.form.get('proceso')
        subproceso = request.form.get('subproceso')
        version = request.form.get('version')
        fecha_actualizacion = request.form.get('fecha_actualizacion')
        fecha_caducidad = request.form.get('fecha_caducidad')
        estado = request.form.get('estado')
        url_sharepoint = request.form.get('url_sharepoint')

        error = None
        if not codigo:
            error = 'El código es requerido.'
        elif not nombre:
            error = 'El nombre es requerido.'

        if error is None:
            try:
                db.execute(
                    'UPDATE lista_formatos SET codigo = ?, nombre = ?, macroproceso = ?, proceso = ?, subproceso = ?, version = ?, fecha_actualizacion = ?, fecha_caducidad = ?, estado = ?, url_sharepoint = ? WHERE id = ?',
                    (codigo, nombre, macroproceso, proceso, subproceso, version, fecha_actualizacion, fecha_caducidad, estado, url_sharepoint, id)
                )
                db.commit()
                flash('Formato actualizado exitosamente.')
                return redirect(url_for('gestion_maestros.index_formatos'))
            except db.IntegrityError:
                error = f"El código {codigo} ya existe."
        
        flash(error)
    
    db.close()
    return render_template('admin/maestros/formatos/editar.html', 
                           formato=formato, 
                           procesos=procesos, 
                           subprocesos_json=json.dumps(subprocesos_dict),
                           macroprocesos=MACROPROCESOS)

@bp.route('/formatos/<int:id>/eliminar', methods=('POST',))
@admin_required
def eliminar_formato(id):
    db = get_db_connection()
    db.execute('DELETE FROM lista_formatos WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash('Formato eliminado.')
    return redirect(url_for('gestion_maestros.index_formatos'))

# --- Carga Masiva Formatos (Excel) ---

@bp.route('/formatos/descargar-plantilla')
@admin_required
def descargar_plantilla_formatos():
    cols = ["codigo", "nombre", "macroproceso", "proceso", "subproceso", "version", "fecha_actualizacion", "fecha_caducidad", "estado", "url_sharepoint"]
    df = pd.DataFrame(columns=cols)
    
    # Datos de ejemplo
    df.loc[0] = ["FR-DI-E-01", "Ejemplo Formato", "Procesos Misionales", "DI", "E", "1.0", "2024-01-01", "2026-01-01", "Activo", "https://sharepoint.com/fr"]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Formatos')
    output.seek(0)
    
    return send_file(output, download_name="plantilla_maestro_formatos.xlsx", as_attachment=True)

@bp.route('/formatos/importar-excel', methods=['POST'])
@admin_required
def importar_formatos_excel():
    if 'archivo' not in request.files:
        flash('No se seleccionó ningún archivo.')
        return redirect(url_for('gestion_maestros.index_formatos'))
    
    archivo = request.files['archivo']
    if archivo.filename == '':
        flash('Archivo sin nombre.')
        return redirect(url_for('gestion_maestros.index_formatos'))

    try:
        df = pd.read_excel(archivo)
        db = get_db_connection()
        success_count = 0
        error_count = 0
        
        required_cols = ["codigo", "nombre", "macroproceso", "proceso", "subproceso", "version", "fecha_actualizacion", "fecha_caducidad", "estado", "url_sharepoint"]
        for col in required_cols:
            if col not in df.columns:
                flash(f"Error: La columna '{col}' no existe en el Excel.")
                db.close()
                return redirect(url_for('gestion_maestros.index_formatos'))

        for _, row in df.iterrows():
            try:
                # Convert dates if they are not string
                fa = row['fecha_actualizacion']
                if hasattr(fa, 'strftime'): fa = fa.strftime('%Y-%m-%d')
                
                fc = row['fecha_caducidad']
                if hasattr(fc, 'strftime'): fc = fc.strftime('%Y-%m-%d')
                
                db.execute(
                    'INSERT OR REPLACE INTO lista_formatos (codigo, nombre, macroproceso, proceso, subproceso, version, fecha_actualizacion, fecha_caducidad, estado, url_sharepoint) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (str(row['codigo']), str(row['nombre']), str(row['macroproceso']), str(row['proceso']), str(row['subproceso']), str(row['version']), fa, fc, str(row['estado']), str(row['url_sharepoint']))
                )
                success_count += 1
            except Exception as e:
                print(f"Error en fila Formatos: {e}")
                error_count += 1
        
        db.commit()
        db.close()
        flash(f"Carga finalizada: {success_count} registros procesados correctamente. {error_count} errores.")
    except Exception as e:
        flash(f"Error al procesar el archivo: {e}")
        
    return redirect(url_for('gestion_maestros.index_formatos'))

# --- Maestro de Documentos ---

MACROPROCESOS = [
    "Procesos de Calidad",
    "Procesos Estrategicos",
    "Procesos de Soporte/Apoyo",
    "Procesos Misionales"
]

def get_maestros_documento():
    """Recupera tipos (sin FR), procesos y subprocesos para los selectores."""
    conn = get_db_connection()
    
    tipos = [dict(row) for row in conn.execute("SELECT codigo, nombre FROM tipos_documento WHERE codigo != 'FR'").fetchall()]
    procesos = [dict(row) for row in conn.execute('SELECT codigo, nombre FROM procesos ORDER BY nombre').fetchall()]
    
    subprocesos_raw = conn.execute('SELECT codigo_proceso, codigo, nombre FROM subprocesos ORDER BY nombre').fetchall()
    subprocesos_dict = {}
    for row in subprocesos_raw:
        proc_code = row['codigo_proceso']
        if proc_code not in subprocesos_dict:
            subprocesos_dict[proc_code] = []
        subprocesos_dict[proc_code].append({'codigo': row['codigo'], 'nombre': row['nombre']})

    conn.close()
    return tipos, procesos, subprocesos_dict

@bp.route('/documentos')
@admin_required
def index_documentos():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    offset = (page - 1) * per_page

    db = get_db_connection()
    
    # Get total count for pagination
    total = db.execute('SELECT COUNT(*) FROM lista_documentos').fetchone()[0]
    total_pages = (total + per_page - 1) // per_page

    documentos = db.execute(
        'SELECT * FROM lista_documentos LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    
    db.close()
    return render_template('admin/maestros/documentos/index.html', 
                           documentos=documentos, 
                           page=page, 
                           total_pages=total_pages)

@bp.route('/documentos/crear', methods=('GET', 'POST'))
@admin_required
def crear_documento():
    tipos, procesos, subprocesos_dict = get_maestros_documento()
    
    if request.method == 'POST':
        tipo_documento = request.form.get('tipo_documento')
        macroproceso = request.form.get('macroproceso')
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        proceso = request.form.get('proceso')
        subproceso = request.form.get('subproceso')
        version_actual = request.form.get('version_actual')
        fecha_caducidad = request.form.get('fecha_caducidad')
        responsable_lider = request.form.get('responsable_lider')
        url_sharepoint = request.form.get('url_sharepoint')

        db = get_db_connection()
        error = None

        if not codigo:
            error = 'El código es requerido.'
        elif not nombre:
            error = 'El nombre es requerido.'

        if error is None:
            try:
                db.execute(
                    'INSERT INTO lista_documentos (tipo_documento, macroproceso, codigo, nombre, proceso, subproceso, version_actual, fecha_caducidad, responsable_lider, url_sharepoint) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (tipo_documento, macroproceso, codigo, nombre, proceso, subproceso, version_actual, fecha_caducidad, responsable_lider, url_sharepoint)
                )
                db.commit()
                flash('Documento creado exitosamente.')
                return redirect(url_for('gestion_maestros.index_documentos'))
            except db.IntegrityError:
                error = f"El código {codigo} ya existe."
        
        flash(error)
        db.close()

    return render_template('admin/maestros/documentos/crear.html', 
                           tipos=tipos, procesos=procesos, 
                           subprocesos_json=json.dumps(subprocesos_dict),
                           macroprocesos=MACROPROCESOS)

@bp.route('/documentos/<int:id>/editar', methods=('GET', 'POST'))
@admin_required
def editar_documento(id):
    db = get_db_connection()
    documento = db.execute('SELECT * FROM lista_documentos WHERE id = ?', (id,)).fetchone()

    if documento is None:
        db.close()
        abort(404, f"Documento id {id} no existe.")

    tipos, procesos, subprocesos_dict = get_maestros_documento()

    if request.method == 'POST':
        tipo_documento = request.form.get('tipo_documento')
        macroproceso = request.form.get('macroproceso')
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        proceso = request.form.get('proceso')
        subproceso = request.form.get('subproceso')
        version_actual = request.form.get('version_actual')
        fecha_caducidad = request.form.get('fecha_caducidad')
        responsable_lider = request.form.get('responsable_lider')
        url_sharepoint = request.form.get('url_sharepoint')

        error = None
        if not codigo:
            error = 'El código es requerido.'
        elif not nombre:
            error = 'El nombre es requerido.'

        if error is None:
            try:
                db.execute(
                    'UPDATE lista_documentos SET tipo_documento = ?, macroproceso = ?, codigo = ?, nombre = ?, proceso = ?, subproceso = ?, version_actual = ?, fecha_caducidad = ?, responsable_lider = ?, url_sharepoint = ? WHERE id = ?',
                    (tipo_documento, macroproceso, codigo, nombre, proceso, subproceso, version_actual, fecha_caducidad, responsable_lider, url_sharepoint, id)
                )
                db.commit()
                flash('Documento actualizado exitosamente.')
                return redirect(url_for('gestion_maestros.index_documentos'))
            except db.IntegrityError:
                error = f"El código {codigo} ya existe."
        
        flash(error)
    
    db.close()
    return render_template('admin/maestros/documentos/editar.html', 
                           documento=documento, 
                           tipos=tipos, procesos=procesos, 
                           subprocesos_json=json.dumps(subprocesos_dict),
                           macroprocesos=MACROPROCESOS)

@bp.route('/documentos/<int:id>/eliminar', methods=('POST',))
@admin_required
def eliminar_documento(id):
    db = get_db_connection()
    db.execute('DELETE FROM lista_documentos WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash('Documento eliminado.')
    return redirect(url_for('gestion_maestros.index_documentos'))

# --- Carga Masiva (Excel) ---

@bp.route('/documentos/descargar-plantilla')
@admin_required
def descargar_plantilla_excel():
    cols = ["tipo_documento", "macroproceso", "codigo", "nombre", "proceso", "subproceso", "version_actual", "fecha_caducidad", "responsable_lider", "url_sharepoint"]
    df = pd.DataFrame(columns=cols)
    
    # Datos de ejemplo
    df.loc[0] = ["PR", "Procesos Misionales", "PR-DI-E-101", "Ejemplo Procedimiento", "DI", "E", "1.0", "2026-12-31", "Rector", "https://sharepoint.com/doc"]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Documentos')
    output.seek(0)
    
    return send_file(output, download_name="plantilla_maestro_documentos.xlsx", as_attachment=True)

@bp.route('/documentos/importar-excel', methods=['POST'])
@admin_required
def importar_excel():
    if 'archivo' not in request.files:
        flash('No se seleccionó ningún archivo.')
        return redirect(url_for('gestion_maestros.index_documentos'))
    
    archivo = request.files['archivo']
    if archivo.filename == '':
        flash('Archivo sin nombre.')
        return redirect(url_for('gestion_maestros.index_documentos'))

    try:
        df = pd.read_excel(archivo)
        db = get_db_connection()
        success_count = 0
        error_count = 0
        
        required_cols = ["tipo_documento", "macroproceso", "codigo", "nombre", "proceso", "subproceso", "version_actual", "fecha_caducidad", "responsable_lider", "url_sharepoint"]
        for col in required_cols:
            if col not in df.columns:
                flash(f"Error: La columna '{col}' no existe en el Excel.")
                db.close()
                return redirect(url_for('gestion_maestros.index_documentos'))

        for _, row in df.iterrows():
            try:
                # Convert date if it's not string
                fecha = row['fecha_caducidad']
                if hasattr(fecha, 'strftime'):
                    fecha = fecha.strftime('%Y-%m-%d')
                
                db.execute(
                    'INSERT OR REPLACE INTO lista_documentos (tipo_documento, macroproceso, codigo, nombre, proceso, subproceso, version_actual, fecha_caducidad, responsable_lider, url_sharepoint) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (str(row['tipo_documento']), str(row['macroproceso']), str(row['codigo']), str(row['nombre']), str(row['proceso']), str(row['subproceso']), str(row['version_actual']), fecha, str(row['responsable_lider']), str(row['url_sharepoint']))
                )
                success_count += 1
            except Exception as e:
                print(f"Error en fila: {e}")
                error_count += 1
        
        db.commit()
        db.close()
        flash(f"Carga finalizada: {success_count} registros procesados correctamente. {error_count} errores.")
    except Exception as e:
        flash(f"Error al procesar el archivo: {e}")
        
    return redirect(url_for('gestion_maestros.index_documentos'))
