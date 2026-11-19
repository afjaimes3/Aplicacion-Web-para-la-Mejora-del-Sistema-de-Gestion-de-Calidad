import os
import sqlite3
import io
import json
from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify
from mailmerge import MailMerge
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_dev_only')

DB_FILE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

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
        'responsables': '',
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
    datos['responsables'] = form_data.get('responsables', '')
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

@app.route('/', methods=['GET', 'POST'])
def formulario():
    tipos, procesos, subprocesos_dict = get_maestros_documento()
    
    conn = get_db_connection()
    personal = [dict(row) for row in conn.execute('SELECT nombre, cargo FROM personal').fetchall()]
    conn.close()

    if request.method == 'POST':
        # Viene de editar
        datos_para_plantilla = procesar_datos_formulario(request.form)
    else:
        # Carga inicial
        datos_para_plantilla = crear_estructura_datos_vacia()

    return render_template('index.html', 
                           datos=datos_para_plantilla, 
                           personal=personal,
                           tipos=tipos,
                           procesos=procesos,
                           subprocesos_json=json.dumps(subprocesos_dict)) # Pasamos JSON al template

@app.route('/preview', methods=['POST'])
def preview():
    if request.method == 'POST':
        datos_procesados = procesar_datos_formulario(request.form)
        
        # Recuperamos nombres legibles para la vista previa (opcional pero recomendado)
        # Esto requiere una consulta rápida o pasarlos desde el form hidden. 
        # Para simplificar, mostraremos los códigos en el preview, o podríamos
        # buscar el nombre en la BD si fuera crítico.
        
        session['form_data'] = datos_procesados
        return render_template('preview.html', datos=datos_procesados)
    return redirect(url_for('formulario'))

@app.route('/generar', methods=['POST'])
def generar_documento():
    datos = session.get('form_data', None)
    if not datos:
        return redirect(url_for('formulario'))

    plantilla_path = "plantilla.docx"
    
    try:
        document = MailMerge(plantilla_path)
    except FileNotFoundError:
        return "Error: No se encuentra el archivo plantilla.docx en la carpeta raíz.", 404

    # 1. Fusionar campos simples (incluyendo los nuevos selectores)
    document.merge(
        tipod=datos.get('tipod', ''),  # Mapeo al campo «tipod»
        pro=datos.get('pro', ''),      # Mapeo al campo «pro»
        sp=datos.get('sp', ''),        # Mapeo al campo «sp»
        Titulodocumento=datos.get('titulodocumento', ''), # Mapeo al campo «Titulodocumento»
        Objetivo=datos.get('objetivo', ''),
        Alcance=datos.get('alcance', ''),
        Responsables=datos.get('responsables', ''),
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

    session.pop('form_data', None)

    # Construir nombre archivo: TIPOD-PRO-SP_Fecha
    nombre_archivo = f"{datos.get('tipod','DOC')}-{datos.get('pro','PRO')}-{datos.get('sp','SUB')}_{datetime.now().strftime('%Y%m%d')}.docx"
    
    return send_file(
        mem_file,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

def consultar_ia_gemini(prompt):
    api_key = os.getenv('AI_API_KEY')
    base_url = os.getenv('AI_BASE_URL')
    
    if not api_key or not base_url:
        return {'error': 'Configuración de IA faltante (API Key o URL).'}

    # Añadimos la key a la URL si es Gemini
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
        
        # Parseo específico para Gemini
        try:
            texto_sugerido = result['candidates'][0]['content']['parts'][0]['text']
            return {'sugerencia': texto_sugerido}
        except (KeyError, IndexError):
            return {'error': 'No se pudo interpretar la respuesta de la IA.', 'raw': result}
            
    except requests.exceptions.RequestException as e:
        return {'error': f'Error de conexión con la IA: {str(e)}'}

@app.route('/api/ia-sugerir', methods=['POST'])
def ia_sugerir():
    data = request.json
    
    contexto_doc = data.get('contexto', {})
    contenido_actual = data.get('contenido', '')
    campo = data.get('campo', 'General')
    es_tabla = data.get('es_tabla', False)

    # Construcción del Prompt
    prompt = f"""
Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad.
Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional.
El idioma debe ser siempre ESPAÑOL.

Estructura institucional jerárquica (referencial, no exhaustiva):
Nivel 1: Consejo Superior.
Nivel 2: Rectoría.
Nivel 3: Secretaría General; Consejos/Comités; Vicerrectoría Académica e Investigación; Vicerrectoría Administrativa y Financiera; Cancillería; Educación Digital/Virtual; Dirección Artística y Cultural.
Nivel 4: Dependencias internas de cada unidad.
Nota: Respeta siempre estas jerarquías en la redacción, mencionando primero a los niveles superiores.

Contexto del Documento:
- Tipo: {contexto_doc.get('tipod', 'N/A')}
- Proceso: {contexto_doc.get('pro', 'N/A')}
- Subproceso: {contexto_doc.get('sp', 'N/A')}
- Título del Documento: {contexto_doc.get('titulodocumento', 'N/A')}

Campo a editar: {campo}
"""

    if es_tabla:
        if campo == 'tabla-actividades':
            prompt += f"""
Los datos provienen de la tabla 'Descripción de Actividades'.
Columnas:
- actividad_no: Consecutivo (NO MODIFICAR).
- actividad_responsable: Cargo del responsable. Corrige ortografía (ej. 'Retor' -> 'Rector').
- actividad_descripcion: Descripción de la actividad. Mejora la redacción, coherencia y tono institucional.
- actividad_registro: Documento de registro. Corrige ortografía y formato.

Formato de entrada (JSON):
{json.dumps(contenido_actual, ensure_ascii=False)}

Instrucciones:
1. Procesa TODAS las filas.
2. Mantén las claves EXACTAS del JSON de entrada ({list(contenido_actual[0].keys()) if contenido_actual else 'claves actuales'}).
3. Devuelve un objeto JSON con dos claves:
   - "nuevos_datos": Lista de objetos con las filas corregidas (formato idéntico al de entrada).
   - "analisis_general": Texto breve con advertencias o comentarios sobre la consistencia global (ej. actividades repetidas, contradicciones, saltos lógicos). Si todo está correcto, indica "Sin inconsistencias detectadas".

Formato de respuesta esperado (estrictamente JSON):
{{
  "nuevos_datos": [ ... ],
  "analisis_general": "..."
}}
"""
        else:
            prompt += f"""
Los datos provienen de una tabla. Por favor, revisa la coherencia, redacción y ortografía de cada elemento.
Formato de entrada (JSON):
{json.dumps(contenido_actual, ensure_ascii=False)}

Instrucciones:
1. Analiza cada fila.
2. Mejora la redacción técnica.
3. Devuelve los datos en el MISMO formato JSON estrictamente, listo para parsear, sin texto adicional antes o después (sin markdown ```json).
"""
    else:
        if campo == 'alcance':
            prompt += """
Requisito Específico para 'Alcance':
En esta sección se debe indicar claramente cuándo inicia y cuándo finaliza el procedimiento descrito en el documento.
Por ejemplo:
“Este procedimiento aplica para la solicitud, aprobación y apoyo logístico para eventos en la Institución. Inicia con la solicitud de la pre-reserva del espacio para el evento y termina con la consolidación de la documentación generada.”
"""

        prompt += f"""
Contenido actual:
"{contenido_actual}"

Instrucciones:
1. Completa la idea si parece cortada.
2. Corrige ortografía y gramática.
3. Mejora el tono para que sea formal e institucional.
4. Devuelve SOLAMENTE el texto mejorado.
"""

    respuesta = consultar_ia_gemini(prompt)
    
    # Limpieza básica si devuelve markdown en json
    if es_tabla and 'sugerencia' in respuesta:
        sug = respuesta['sugerencia']
        if sug.startswith('```json'):
            sug = sug.replace('```json', '').replace('```', '')
        respuesta['sugerencia'] = sug.strip()

    return jsonify(respuesta)

if __name__ == '__main__':
    app.run()