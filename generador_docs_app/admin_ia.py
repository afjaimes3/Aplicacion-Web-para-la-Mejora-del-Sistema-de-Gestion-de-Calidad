from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from db import get_db_connection
from auth import admin_required
import json

bp = Blueprint('admin_ia', __name__, url_prefix='/admin/ia')

@bp.route('/')
@admin_required
def index():
    db = get_db_connection()
    prompts = db.execute('SELECT * FROM config_prompts').fetchall()
    
    # Get Global Setting
    global_setting = db.execute("SELECT value FROM system_config WHERE key = 'enable_ia_global'").fetchone()
    enable_ia_global = True
    if global_setting and global_setting['value'] == '0':
        enable_ia_global = False
    
    # Organize prompts by tipo_documento then by seccion
    prompts_dict = {}
    for p in prompts:
        td = p['tipo_documento']
        if td not in prompts_dict:
            prompts_dict[td] = {}
        # Convert row to dict to be mutable if needed, though here we just read
        prompts_dict[td][p['seccion']] = dict(p)
    
    db.close()
    
    # Document types for tabs
    tipos = [
        {'codigo': 'PR', 'nombre': 'Procedimiento'},
        {'codigo': 'DI', 'nombre': 'Documento Institucional'},
        {'codigo': 'IN', 'nombre': 'Instructivo'},
        {'codigo': 'FR', 'nombre': 'Formato'}
    ]
    
    # Sections to display
    secciones = [
        {'id': 'objetivo', 'nombre': 'Objetivo'},
        {'id': 'alcance', 'nombre': 'Alcance'},
        {'id': 'responsables', 'nombre': 'Responsables'},
        {'id': 'definiciones', 'nombre': 'Definiciones'},
        {'id': 'tabla-actividades', 'nombre': '5. Descripción de Actividades'},
        {'id': 'tabla-documentos-relacionados', 'nombre': '6. Documentos Relacionados'}
    ]
    
    return render_template('admin/admin_ia.html', 
                           prompts=prompts_dict, 
                           tipos=tipos, 
                           secciones=secciones,
                           enable_ia_global=enable_ia_global)

@bp.route('/save_global', methods=['POST'])
@admin_required
def save_global():
    enable = '1' if request.form.get('enable_ia_global') == 'on' else '0'
    db = get_db_connection()
    db.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('enable_ia_global', ?)", (enable,))
    db.commit()
    db.close()
    flash('Configuración global de IA actualizada.')
    return redirect(url_for('admin_ia.index'))

@bp.route('/save', methods=['POST'])
@admin_required
def save():
    tipo_documento = request.form.get('tipo_documento')
    seccion = request.form.get('seccion')
    prompt_sistema = request.form.get('prompt_sistema')
    prompt_instrucciones = request.form.get('prompt_instrucciones')
    activo = 1 if request.form.get('activo') == 'on' else 0
    
    if not tipo_documento or not seccion:
        flash('Datos incompletos.')
        return redirect(url_for('admin_ia.index'))
    
    db = get_db_connection()
    # Check if exists to update or insert (using ID would be safer but composite key works)
    # SQLite INSERT OR REPLACE works but deletes old row and makes new ID. 
    # Better to use UPDATE if exists else INSERT for ID stability, but here ID references aren't critical yet.
    # However, 'activo' column was added.
    
    # Let's use an UPSERT approach or check existence.
    exists = db.execute('SELECT id FROM config_prompts WHERE tipo_documento = ? AND seccion = ?', (tipo_documento, seccion)).fetchone()
    
    if exists:
        db.execute('''
            UPDATE config_prompts 
            SET prompt_sistema = ?, prompt_instrucciones = ?, activo = ?
            WHERE tipo_documento = ? AND seccion = ?
        ''', (prompt_sistema, prompt_instrucciones, activo, tipo_documento, seccion))
    else:
        db.execute('''
            INSERT INTO config_prompts (tipo_documento, seccion, prompt_sistema, prompt_instrucciones, activo)
            VALUES (?, ?, ?, ?, ?)
        ''', (tipo_documento, seccion, prompt_sistema, prompt_instrucciones, activo))
        
    db.commit()
    db.close()
    
    flash(f'Prompt de {seccion} para {tipo_documento} actualizado correctamente.')
    return redirect(url_for('admin_ia.index') + f'?tab={tipo_documento}')
