import os
import io
import json
import uuid
from flask import Blueprint, render_template, request, send_file, redirect, url_for, session, jsonify, abort
from mailmerge import MailMerge
from datetime import datetime
import requests
from dotenv import load_dotenv
from db import get_db_connection
from functools import wraps

load_dotenv()

bp = Blueprint('documents', __name__)

from auth import login_required
from utils.docx_formatter import ProcedureFormatter
from utils.formats_formatter import FormatFormatter

def get_maestros_documento():
    """Recupera tipos, procesos y subprocesos para los selectores."""
    conn = get_db_connection()
    
    tipos = [dict(row) for row in conn.execute('SELECT codigo, nombre FROM tipos_documento').fetchall()]
    procesos = [dict(row) for row in conn.execute('SELECT codigo, nombre FROM procesos').fetchall()]
    
    # Obtenemos subprocesos y los estructuramos para fácil uso en JS
    subprocesos_raw = conn.execute('SELECT codigo_proceso, codigo, nombre FROM subprocesos').fetchall()
    
    # Estructura: {'COD_PROCESO': [{'codigo': 'COD_SUB', 'nombre': 'NOMBRE_SUB'}, ...]}
    subprocesos_dict = {}
    for row in subprocesos_raw:
        proc_code = row['codigo_proceso']
        if proc_code not in subprocesos_dict:
            subprocesos_dict[proc_code] = []
        subprocesos_dict[proc_code].append({'codigo': row['codigo'], 'nombre': row['nombre']})

    conn.close()
    return tipos, procesos, subprocesos_dict

def crear_estructura_datos_vacia():
    return {
        'tipod': '',       # Nuevo campo
        'pro': '',         # Nuevo campo
        'sp': '',          # Nuevo campo
        'titulodocumento': '', # Nuevo campo Titulo Documento
        'objetivo': '',
        'alcance': '',
        'periodicidad': '', # Nuevo campo
        'responsables': '',
        'normatividad': '', # Nuevo campo
        'definiciones': '',
        'actividades': [],
        'documentos_relacionados': [],
        'anexos': [],
        'aprobacion': {
            'nombre_elaboro': '', 'cargo_elaboro': '', 'fecha_elaboro': ''
        }
    }

def procesar_datos_formulario(form_data):
    datos = crear_estructura_datos_vacia()

    # 0. Datos Maestros (Nuevos Selectores)
    datos['tipod'] = form_data.get('tipod', '')
    datos['pro'] = form_data.get('pro', '')
    datos['sp'] = form_data.get('sp', '')
    datos['titulodocumento'] = form_data.get('titulodocumento', '')

    # 1. Campos de texto simples
    datos['objetivo'] = form_data.get('objetivo', '')
    datos['alcance'] = form_data.get('alcance', '')
    datos['periodicidad'] = form_data.get('periodicidad', '')
    datos['responsables'] = form_data.get('responsables', '')
    datos['normatividad'] = form_data.get('normatividad', '')
    datos['definiciones'] = form_data.get('definiciones', '')

    # 2. Tabla Actividades
    act_nos = form_data.getlist('actividad_no')
    act_responsables = form_data.getlist('actividad_responsable')
    act_descripciones = form_data.getlist('actividad_descripcion')
    act_registros = form_data.getlist('actividad_registro')

    for no, resp, act, reg in zip(act_nos, act_responsables, act_descripciones, act_registros):
        if no or resp or act or reg:
            datos['actividades'].append({
                'No': no, 'Responsable': resp, 'Actividad': act, 'Registro': reg
            })

    # 3. Tabla Documentos Relacionados
    insts = form_data.getlist('doc_institucional')
    nombres = form_data.getlist('doc_nombre')
    cods = form_data.getlist('doc_codigo')

    for inst, nom, cod in zip(insts, nombres, cods):
        if inst or nom or cod:
            datos['documentos_relacionados'].append({
                'documentoinstitucional': inst, 'nombredocumento': nom, 'Codigo1': cod
            })

    # 4. Tabla Anexos
    anos = form_data.getlist('anexo_no')
    anoms = form_data.getlist('anexo_nombre')
    adescs = form_data.getlist('anexo_descripcion')
    
    for no, nom, desc in zip(anos, anoms, adescs):
        if no or nom or desc:
            datos['anexos'].append({
                'NoA': no, 'NombreDocumento': nom, 'Descripcion': desc
            })

    # 5. Aprobación
    datos['aprobacion']['nombre_elaboro'] = form_data.get('nombre_elaboro', '')
    datos['aprobacion']['cargo_elaboro'] = form_data.get('cargo_elaboro', '')
    datos['aprobacion']['fecha_elaboro'] = form_data.get('fecha_elaboro', '')

    # 8. Control de Cambios (Automático)
    # Formato fecha Colombia: DD/MM/YYYY
    fecha_colombia = datetime.now().strftime('%d/%m/%Y')
    datos['control_cambios'] = [{
        'NoC': '1',
        'IdentificacionC': 'Versión inicial del procedimiento',
        'FechaC': fecha_colombia
    }]
    
    return datos

@bp.route('/formulario', methods=['GET', 'POST'])
@login_required
def formulario():
    tipos, procesos, subprocesos_dict = get_maestros_documento()
    
    conn = get_db_connection()
    personal = [dict(row) for row in conn.execute('SELECT nombre, cargo FROM personal').fetchall()]
    
    draft_id = request.args.get('draft_id')
    datos_para_plantilla = crear_estructura_datos_vacia() # Default empty

    if request.method == 'POST':
        # Si es POST, procesamos el form normalmente (podría ser un guardado parcial si existiera)
        # Pero normalmente el flujo es Form -> Submit to Preview.
        # Si hay lógica para recargar desde POST, la mantenemos, pero el flujo principal es Preview.
        datos_para_plantilla = procesar_datos_formulario(request.form)
    elif draft_id:
        # Recuperar borrador
        borrador = conn.execute('SELECT content FROM borradores WHERE id = ?', (draft_id,)).fetchone()
        if borrador:
            try:
                datos_para_plantilla = json.loads(borrador['content'])
            except json.JSONDecodeError:
                pass # Manejo de error si el JSON está corrupto
    
    # Check Global AI Switch
    global_switch = conn.execute("SELECT value FROM system_config WHERE key = 'enable_ia_global'").fetchone()
    enable_ia_global = True
    if global_switch and global_switch['value'] == '0':
        enable_ia_global = False
    
    conn.close()

    return render_template('document_form.html', 
                           datos=datos_para_plantilla, 
                           personal=personal,
                           tipos=tipos,
                           procesos=procesos,
                           subprocesos_json=json.dumps(subprocesos_dict),
                           draft_id=draft_id,
                           enable_ia_global=enable_ia_global) # Pasamos draft_id para que el form sepa si está editando

@bp.route('/preview', methods=['POST'])
@login_required
def preview():
    if request.method == 'POST':
        datos_procesados = procesar_datos_formulario(request.form)
        
        # Verificar si ya existe un ID de borrador (campo oculto en el formulario)
        draft_id = request.form.get('draft_id')
        if not draft_id:
            draft_id = str(uuid.uuid4())
            is_new = True
        else:
            is_new = False
        
        # Guardar en BD
        conn = get_db_connection()
        if is_new:
            conn.execute('INSERT INTO borradores (id, content) VALUES (?, ?)', 
                         (draft_id, json.dumps(datos_procesados)))
        else:
            conn.execute('UPDATE borradores SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                         (json.dumps(datos_procesados), draft_id))
        conn.commit()
        conn.close()
        
        # Renderizar preview con el ID
        return render_template('preview.html', datos=datos_procesados, draft_id=draft_id)
    return redirect(url_for('documents.formulario'))

@bp.route('/generar', methods=['POST'])
@login_required
def generar_documento():
    # Recuperar ID del borrador del formulario
    draft_id = request.form.get('draft_id')
    
    if not draft_id:
        return redirect(url_for('documents.formulario'))
    
    conn = get_db_connection()
    borrador = conn.execute('SELECT content FROM borradores WHERE id = ?', (draft_id,)).fetchone()
    conn.close()
    
    if not borrador:
        return "Error: Borrador no encontrado o expirado.", 404
        
    datos = json.loads(borrador['content'])

    # Selección de plantilla basada en el tipo de documento
    tipo_doc = datos.get('tipod', 'DOC')
    if tipo_doc in ['FR', 'FMT', 'FOR']:
        plantilla_path = "PlantillaFormatoVertical.docx"
    elif tipo_doc in ['IN', 'INS']:
        plantilla_path = "PlantillaElaboracionInstructivo.docx"
    else:
        plantilla_path = "plantilla.docx"
    
    try:
        document = MailMerge(plantilla_path)
    except FileNotFoundError:
        return f"Error: No se encuentra el archivo {plantilla_path} en la carpeta raíz.", 404

    # 1. Fusionar campos simples
    document.merge(
        tipod=datos.get('tipod', ''),  
        pro=datos.get('pro', ''),      
        sp=datos.get('sp', ''),        
        Titulodocumento=datos.get('titulodocumento', ''), 
        Objetivo=datos.get('objetivo', ''),
        Alcance=datos.get('alcance', ''),
        Periodicidad=datos.get('periodicidad', ''),
        Responsables=datos.get('responsables', ''),
        Normatividad=datos.get('normatividad', ''),
        Definiciones=datos.get('definiciones', ''),
        Nombre_elaboro=datos['aprobacion'].get('nombre_elaboro', ''),
        Cargo_elaboro=datos['aprobacion'].get('cargo_elaboro', ''),
        fecha_elaboro=datos['aprobacion'].get('fecha_elaboro', '')
    )
    
    # 2. Fusionar tablas dinámicas
    if datos.get('actividades'):
        document.merge_rows('No', datos['actividades'])
    if datos.get('documentos_relacionados'):
        document.merge_rows('documentoinstitucional', datos['documentos_relacionados'])
    if datos.get('anexos'):
        document.merge_rows('NoA', datos['anexos'])
    if datos.get('control_cambios'):
        document.merge_rows('NoC', datos['control_cambios'])

    mem_file = io.BytesIO()
    document.write(mem_file)
    mem_file.seek(0)

    # APLICAR FORMATEADOR ROBUSTO DE ESTILOS INSTITUCIONALES (Carga configuración de BD)
    conn = get_db_connection()
    if tipo_doc in ['FR', 'FMT', 'FOR']:
        style_row = conn.execute("SELECT * FROM document_styles WHERE style_type = 'Formato'").fetchone()
        formatter = FormatFormatter(dict(style_row) if style_row else None)
    else:
        style_row = conn.execute("SELECT * FROM document_styles WHERE style_type = 'Procedimiento'").fetchone()
        formatter = ProcedureFormatter(dict(style_row) if style_row else None)
    conn.close()
    
    formatted_file = formatter.format_document(mem_file)

    # Construir nombre archivo: TIPOD-PRO-SP_Fecha
    nombre_archivo = f"{datos.get('tipod','DOC')}-{datos.get('pro','PRO')}-{datos.get('sp','SUB')}_{datetime.now().strftime('%Y%m%d')}.docx"
    
    return send_file(
        formatted_file,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

def consultar_ia_gemini(prompt):
    api_key = os.getenv('AI_API_KEY')
    base_url = os.getenv('AI_BASE_URL')
    
    if not api_key or not base_url:
        return {'error': 'Configuración de IA faltante (API Key o URL).'}

    url = f"{base_url}?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        try:
            texto_sugerido = result['candidates'][0]['content']['parts'][0]['text']
            return {'sugerencia': texto_sugerido}
        except (KeyError, IndexError):
            return {'error': 'No se pudo interpretar la respuesta de la IA.', 'raw': result}
            
    except requests.exceptions.RequestException as e:
        return {'error': f'Error de conexión con la IA: {str(e)}'}

@bp.route('/api/ia-sugerir', methods=['POST'])
@login_required
def ia_sugerir():
    data = request.json
    contexto_doc = data.get('contexto', {})
    contenido_actual = data.get('contenido', '')
    contenido_previo = data.get('contenido_previo', []) 
    campo = data.get('campo', 'General')
    es_tabla = data.get('es_tabla', False)
    
    tipo_doc = contexto_doc.get('tipod', 'PR')
    
    db = get_db_connection()
    
    # 1. Check Global AI Switch
    global_switch = db.execute("SELECT value FROM system_config WHERE key = 'enable_ia_global'").fetchone()
    if global_switch and global_switch['value'] == '0':
        db.close()
        return jsonify({'error': 'La IA está desactivada globalmente por el administrador.'})

    prompt_config = db.execute(
        'SELECT prompt_sistema, prompt_instrucciones, activo FROM config_prompts WHERE tipo_documento = ? AND seccion = ?',
        (tipo_doc, campo)
    ).fetchone()
    
    if not prompt_config:
        # Default behavior: Active if not configured yet? 
        # Or better: check if row implies config exists. If row doesn't exist, we assume active (default 1) in spirit, 
        # but technically we don't have a row. Let's assume active if not found.
        system_base = "Actúa como un experto en redacción técnica institucional."
        instr_base = "Mejora el texto proporcionando un tono formal. Si es tabla, devuelve JSON estrictamente."
    else:
        # 2. Check Per-Section AI Switch
        if prompt_config['activo'] == 0:
            db.close()
            return jsonify({'error': 'La IA está desactivada para esta sección específica.'})
            
        system_base = prompt_config['prompt_sistema']
        instr_base = prompt_config['prompt_instrucciones']


    master_data_context = ""
    if campo == 'tabla-actividades':
        master_data_context = """
INSTRUCCIONES PARA COLUMNA 'REGISTRO':
1. NO inventar códigos ni buscar en bases de datos.
2. INFERIR la evidencia (física/digital) analizando el verbo y descripción de la actividad.
   - Ej: "Enviar correo" -> "Correo electrónico enviado"
   - Ej: "Pagar en efectivo" -> "Comprobante de egreso"
   - Ej: "Validar visualmente" -> "No Aplica"
3. Si la actividad es intelectual o verbal y no genera documento, poner "No Aplica".
"""
                
    elif campo == 'tabla-documentos' or campo == 'tabla-documentos-relacionados':
        # 1. Recuperar Documentos Maestros
        docs_maestros = db.execute(
            'SELECT codigo, nombre, tipo_documento FROM lista_documentos WHERE proceso = ? AND subproceso = ?',
            (contexto_doc.get('pro'), contexto_doc.get('sp'))
        ).fetchall()

        # 2. Recuperar Formatos Maestros
        formatos_maestros = db.execute(
            'SELECT codigo, nombre FROM lista_formatos WHERE proceso = ? AND subproceso = ?',
            (contexto_doc.get('pro'), contexto_doc.get('sp'))
        ).fetchall()
        
        master_data_context = ""

        if docs_maestros or formatos_maestros:
            master_data_context = "\nBASE DE DATOS MAESTRA (ÚNICA FUENTE DE VERDAD):\n"
            if docs_maestros:
                master_data_context += "--- Documentos Institucionales ---\n"
                for dm in docs_maestros:
                    master_data_context += f"- [{dm['tipo_documento']}] {dm['codigo']}: {dm['nombre']}\n"
            
            if formatos_maestros:
                master_data_context += "--- Formatos ---\n"
                for fm in formatos_maestros:
                    master_data_context += f"- [FR] {fm['codigo']}: {fm['nombre']}\n"

            master_data_context += """
INSTRUCCIONES ESTRICTAS:
1. SOLO y ÚNICAMENTE puedes usar los documentos listados arriba en la sección 'BASE DE DATOS MAESTRA'.
2. Si un documento no está en esa lista, NO lo incluyas. NO inventes códigos ni nombres.
3. Analiza el 'Objetivo', 'Alcance' y las 'Actividades' previas para seleccionar SOLO los documentos de la lista que sean pertinentes.
4. Usa el CÓDIGO y NOMBRE EXACTOS como aparecen en la lista.
5. Si ningún documento de la lista es relevante, devuelve una tabla vacía.
"""
        else:
            master_data_context += "\nAVISO: No se encontraron documentos maestros para este Proceso/Subproceso. Devuelve una tabla vacía, NO inventes datos.\n"
        
        if contenido_previo:
            master_data_context += f"\nContexto Adicional (Actividades previas):\n{json.dumps(contenido_previo, ensure_ascii=False)}\n"

    db.close()

    prompt = f"""
{system_base}

Contexto del Documento:
- Tipo: {contexto_doc.get('tipod', 'N/A')}
- Proceso: {contexto_doc.get('pro', 'N/A')}
- Subproceso: {contexto_doc.get('sp', 'N/A')}
- Título del Documento: {contexto_doc.get('titulodocumento', 'N/A')}
- Objetivo: {contexto_doc.get('objetivo', 'N/A')}
- Alcance: {contexto_doc.get('alcance', 'N/A')}
{master_data_context}

Campo a editar: {campo}
Contenido actual: {json.dumps(contenido_actual, ensure_ascii=False) if es_tabla else contenido_actual}

{instr_base}
"""
    respuesta = consultar_ia_gemini(prompt)
    
    if es_tabla and 'sugerencia' in respuesta:
        sug = respuesta['sugerencia']
        
        # 1. Eliminar bloques de código Markdown si existen
        sug = sug.strip()
        if sug.startswith('```json'):
            sug = sug[7:]
        if sug.startswith('```'):
            sug = sug[3:]
        if sug.endswith('```'):
            sug = sug[:-3]
        sug = sug.strip()

        # 2. Intentar extraer JSON de lista [...]
        start_list = sug.find('[')
        end_list = sug.rfind(']')
        
        # 3. Intentar extraer JSON de objeto {...}
        start_obj = sug.find('{')
        end_obj = sug.rfind('}')

        if start_list != -1 and end_list != -1:
            # Prioridad a la lista si existe, ya que para tablas esperamos lista
            sug = sug[start_list:end_list+1]
        elif start_obj != -1 and end_obj != -1:
            # Si no hay lista pero hay objetos, podría ser un objeto único o varios mal formateados
            candidate = sug[start_obj:end_obj+1]
            # Si parece que son varios objetos separados por coma fuera de una lista (e.g. {...}, {...})
            # Tratamos de detectarlo. Pero es arriesgado. 
            # Si el usuario recibe "Error ... position X", es porque el frontend espera una lista válida.
            # Si la IA devolvió {...}, {...} sin corchetes, aquí lo capturamos "tal cual" y fallará en el frontend o será un solo objeto.
            # Vamos a intentar envolverlo si parece necesario, pero mejor confiamos en el prompt.
            sug = candidate
        
        respuesta['sugerencia'] = sug

    return jsonify(respuesta)
