"""
Script de inicialización de la base de datos para el Generador Documental.
Crea todas las tablas requeridas e inserta datos iniciales limpios y genéricos.
"""
import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_FILE = 'database.db'

PROCESOS = [['AS', 'Aseguramiento de la Calidad Académica'], ['DI', 'Direccionamiento Institucional'], ['GA', 'Gestión Administrativa'], ['GC', 'Gestión Artística y Cultural'], ['GF', 'Gestión Financiera'], ['GH', 'Gestión del Talento Humano'], ['GI', 'Gestión Integral'], ['GJ', 'Gestión Jurídica'], ['GM', 'Gestión del Medio Universitario'], ['GP', 'Gestión de Comunicaciones'], ['GS', 'Gestión de Soporte Académico'], ['GT', 'Gestión de TI'], ['PD', 'Docencia'], ['PI', 'Investigación'], ['PS', 'Proyección Social'], ['RI', 'Relaciones Interinstitucionales']]

SUBPROCESOS = [['DI', 'E', 'Direccionamiento Estratégico'], ['DI', 'P', 'Presupuesto Institucional'], ['RI', 'C', 'Cancillería'], ['AS', 'A', 'Autoevaluación'], ['AS', 'E', 'Evaluación'], ['AS', 'I', 'Información'], ['AS', 'R', 'Registro Calificado'], ['GI', 'C', 'Administración del SGC'], ['GI', 'A', 'Administración del SGA'], ['PD', 'G', 'Gestión de Programas'], ['PD', 'P', 'Gestión Académica'], ['PD', 'O', 'Otorgamiento de Estímulos y Distinciones'], ['PI', 'I', 'Investigación Formal'], ['PI', 'F', 'Formación Investigativa'], ['PI', 'G', 'Gestión del Capital Humano, Intelectual y Relacional'], ['PI', 'L', 'Laboratorios'], ['PS', 'R', 'Publicaciones Institucionales'], ['PS', 'E', 'Programas de Extensión y Proyectos Especiales'], ['PS', 'A', 'Atención Psicológica'], ['PS', 'G', 'Graduados'], ['PS', 'P', 'Prácticas Profesionales'], ['GS', 'A', 'Admisiones'], ['GS', 'R', 'Registro Académico'], ['GS', 'V', 'Educación Virtual'], ['GS', 'B', 'Biblioteca'], ['GA', 'C', 'Compras'], ['GA', 'S', 'Servicios Generales'], ['GA', 'V', 'Protección de Recursos'], ['GA', 'P', 'Planta Física - Infraestructura'], ['GA', 'E', 'Gestión de Eventos'], ['GA', 'A', 'Administración General'], ['GF', 'A', 'Activos Fijos'], ['GF', 'C', 'Gestión Contable'], ['GF', 'T', 'Tesorería'], ['GF', 'R', 'Cartera'], ['GF', 'F', 'Administración de Gestión Financiera'], ['GH', 'A', 'Administración del Talento Humano'], ['GH', 'S', 'Selección'], ['GH', 'C', 'Contratación'], ['GH', 'N', 'Nómina'], ['GH', 'D', 'Desarrollo Humano y Organizacional (DHO)'], ['GH', 'T', 'Seguridad y Salud en el Trabajo'], ['GH', 'I', 'Inducción'], ['GT', 'A', 'Administración de Gestión de TI'], ['GT', 'I', 'Infraestructura'], ['GT', 'S', 'Seguridad Informática'], ['GT', 'P', 'Aplicaciones'], ['GT', 'T', 'Soporte Técnico'], ['GM', 'A', 'Administración del Gestión del Medio Universitario'], ['GM', 'B', 'Bienestar Institucional'], ['GM', 'C', 'Consejería Académica'], ['GM', 'G', 'Grados'], ['GM', 'S', 'Salud'], ['GP', 'A', 'Administración de Gestión de Comunicaciones'], ['GP', 'E', 'Cubrimiento de Eventos'], ['GP', 'P', 'Página Web'], ['GP', 'V', 'Videos'], ['GP', 'R', 'Redes Sociales'], ['GP', 'D', 'Promoción y Divulgación'], ['GJ', 'J', 'Asesoría Jurídica'], ['GJ', 'A', 'Administración de la Gestión Jurídica'], ['GJ', 'Q', 'FPQRS'], ['GC', 'A', 'Administración de la Gestión Artística y Cultural']]

DOCUMENT_STYLES = [{'style_type': 'Procedimiento', 'body_font_family': 'Calibri', 'body_font_size': 12, 'body_font_color': '#2D3748', 'title_font_family': 'Calibri', 'title_font_size': 12, 'title_font_color': '#1B365D', 'table_header_fill': '#E2E8F0', 'table_header_text_color': '#58595b', 'header_code_fill': '#2D3748', 'header_code_text_color': '#ffffff', 'margin_top': 2.5, 'margin_bottom': 2.5, 'margin_left': 2.0, 'margin_right': 2.0}, {'style_type': 'Formato', 'body_font_family': 'Calibri', 'body_font_size': 10, 'body_font_color': '#2D3748', 'title_font_family': 'Calibri', 'title_font_size': 10, 'title_font_color': '#2D3748', 'table_header_fill': '#E2E8F0', 'table_header_text_color': '#2D3748', 'header_code_fill': '#2D3748', 'header_code_text_color': '#FFFFFF', 'margin_top': 2.54, 'margin_bottom': 2.54, 'margin_left': 2.54, 'margin_right': 2.54}]

CONFIG_PROMPTS = [['PR', 'objetivo', 'Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad. Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional. El idioma debe ser siempre ESPAÑOL.\r\n\r\nEstructura institucional jerárquica (referencial, no exhaustiva):\r\nNivel 1: Consejo Superior.\r\nNivel 2: Rectoría.\r\nNivel 3: Secretaría General; Consejos/Comités; Vicerrectoría Académica e Investigación; Vicerrectoría Administrativa y Financiera; Cancillería; Educación Digital/Virtual; Dirección Artística y Cultural.\r\nNivel 4: Dependencias internas de cada unidad.\r\nNota: Respeta siempre estas jerarquías en la redacción, mencionando primero a los niveles superiores.\r\nIMPORTANTE: Devuelve SOLAMENTE el resultado solicitado. No incluyas meta-comentarios, saludos, introducciones ni repitas estas instrucciones.', 'Completa la idea si parece cortada. Corrige ortografía y gramática. Mejora el tono para que sea formal e institucional. Devuelve SOLAMENTE el texto mejorado.', 1], ['PR', 'responsables', 'Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad. Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional. El idioma debe ser siempre ESPAÑOL.\n\nEstructura institucional jerárquica (referencial, no exhaustiva):\nNivel 1: Consejo Superior.\nNivel 2: Rectoría.\nNivel 3: Secretaría General; Consejos/Comités; Vicerrectoría Académica e Investigación; Vicerrectoría Administrativa y Financiera; Cancillería; Educación Digital/Virtual; Dirección Artística y Cultural.\nNivel 4: Dependencias internas de cada unidad.\nNota: Respeta siempre estas jerarquías en la redacción, mencionando primero a los niveles superiores.\nIMPORTANTE: Devuelve SOLAMENTE el resultado solicitado. No incluyas meta-comentarios, saludos, introducciones ni repitas estas instrucciones.', 'Mejora la redacción técnica de los responsables. Devuelve SOLAMENTE el texto mejorado.', 1], ['PR', 'definiciones', 'Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad. Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional. El idioma debe ser siempre ESPAÑOL.\n\nEstructura institucional jerárquica (referencial, no exhaustiva):\nNivel 1: Consejo Superior.\nNivel 2: Rectoría.\nNivel 3: Secretaría General; Consejos/Comités; Vicerrectoría Académica e Investigación; Vicerrectoría Administrativa y Financiera; Cancillería; Educación Digital/Virtual; Dirección Artística y Cultural.\nNivel 4: Dependencias internas de cada unidad.\nNota: Respeta siempre estas jerarquías en la redacción, mencionando primero a los niveles superiores.\nIMPORTANTE: Devuelve SOLAMENTE el resultado solicitado. No incluyas meta-comentarios, saludos, introducciones ni repitas estas instrucciones.', 'Mejora la redacción técnica de las definiciones. Devuelve SOLAMENTE el texto mejorado.', 1], ['PR', 'tabla-actividades', 'Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad. Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional. El idioma debe ser siempre ESPAÑOL.\n\nEstructura institucional jerárquica (referencial, no exhaustiva):\nNivel 1: Consejo Superior.\nNivel 2: Rectoría.\nNivel 3: Secretaría General; Consejos/Comités; Vicerrectoría Académica e Investigación; Vicerrectoría Administrativa y Financiera; Cancillería; Educación Digital/Virtual; Dirección Artística y Cultural.\nNivel 4: Dependencias internas de cada unidad.\nNota: Respeta siempre estas jerarquías en la redacción, mencionando primero a los niveles superiores.\nIMPORTANTE: Devuelve SOLAMENTE el resultado solicitado. No incluyas meta-comentarios, saludos, introducciones ni repitas estas instrucciones.', 'Procesa la tabla de actividades. Mantén las claves originales. Devuelve un objeto JSON con dos claves: "nuevos_datos" (la lista de filas corregidas) y "analisis_general" (un texto breve sobre coherencia o inconsistencias). Devuelve SOLAMENTE el JSON puro.', 1], ['PR', 'tabla-documentos', 'Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad. Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional. El idioma debe ser siempre ESPAÑOL.\n\nEstructura institucional jerárquica (referencial, no exhaustiva):\nNivel 1: Consejo Superior.\nNivel 2: Rectoría.\nNivel 3: Secretaría General; Consejos/Comités; Vicerrectoría Académica e Investigación; Vicerrectoría Administrativa y Financiera; Cancillería; Educación Digital/Virtual; Dirección Artística y Cultural.\nNivel 4: Dependencias internas de cada unidad.\nNota: Respeta siempre estas jerarquías en la redacción, mencionando primero a los niveles superiores.\nIMPORTANTE: Devuelve SOLAMENTE el resultado solicitado. No incluyas meta-comentarios, saludos, introducciones ni repitas estas instrucciones.', 'Procesa la tabla de documentos relacionados. Compara con los maestros y las actividades previas proporcionadas. Devuelve un objeto JSON con dos claves: "nuevos_datos" (la lista de objetos corregidos) y "analisis_general" (observaciones sobre la relación de documentos). Devuelve SOLAMENTE el JSON puro.', 1], ['PR', 'alcance', 'Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad. Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional. El idioma debe ser siempre ESPAÑOL.\r\n\r\nEstructura institucional jerárquica (referencial, no exhaustiva):\r\nNivel 1: Consejo Superior.\r\nNivel 2: Rectoría.\r\nNivel 3: Secretaría General; Consejos/Comités; Vicerrectoría Académica e Investigación; Vicerrectoría Administrativa y Financiera; Cancillería; Educación Digital/Virtual; Dirección Artística y Cultural.\r\nNivel 4: Dependencias internas de cada unidad.\r\nNota: Respeta siempre estas jerarquías en la redacción, mencionando primero a los niveles superiores.\nIMPORTANTE: Devuelve SOLAMENTE el resultado solicitado. No incluyas meta-comentarios, saludos, introducciones ni repitas estas instrucciones.', 'En esta sección se debe indicar claramente cuándo inicia y cuándo finaliza el procedimiento. Devuelve SOLAMENTE el texto mejorado. No incluyas saludos, explicaciones ni repitas estas instrucciones.', 1], ['PR', 'tabla-documentos-relacionados', 'Sugiere documentos relacionados segun la tabla maestra de documentos', '', 1], ['PR', 'tabla-anexos', 'Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad. Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional. El idioma debe ser siempre ESPAÑOL.', 'Los datos provienen de la tabla \'Lista de Anexos\'. \nColumnas esperadas: anexo_no, anexo_nombre, anexo_descripcion.\n\nINSTRUCCIONES DE FORMATO JSON:\n1. Debes devolver estrictamente una LISTA de objetos JSON.\n2. La respuesta debe comenzar con \'[\' y terminar con \']\'.\n3. NO incluyas texto fuera del JSON.\n4. Ejemplo de formato correcto:\n[\n  {\n    "anexo_no": "1",\n    "anexo_nombre": "Nombre del Anexo",\n    "anexo_descripcion": "Descripción técnica del anexo."\n  }\n]\n', 1], ['DI', 'tabla-anexos', 'Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad. Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional. El idioma debe ser siempre ESPAÑOL.', 'Los datos provienen de la tabla \'Lista de Anexos\'. \nColumnas esperadas: anexo_no, anexo_nombre, anexo_descripcion.\n\nINSTRUCCIONES DE FORMATO JSON:\n1. Debes devolver estrictamente una LISTA de objetos JSON.\n2. La respuesta debe comenzar con \'[\' y terminar con \']\'.\n3. NO incluyas texto fuera del JSON.\n4. Ejemplo de formato correcto:\n[\n  {\n    "anexo_no": "1",\n    "anexo_nombre": "Nombre del Anexo",\n    "anexo_descripcion": "Descripción técnica del anexo."\n  }\n]\n', 1]]

SAMPLE_DOCUMENTOS = [
    ('PR', 'PR-GA-A-101', 'Procedimiento de Gestión de Compras', 'GA', 'A', '1.0', '2028-12-31', 'Líder de Compras', 'Procesos de Soporte/Apoyo', None),
    ('PR', 'PR-GH-T-102', 'Procedimiento de Inducción de Personal', 'GH', 'T', '2.0', '2028-12-31', 'Líder de Talento', 'Procesos de Soporte/Apoyo', None),
    ('PR', 'PR-GT-S-103', 'Procedimiento de Respaldo y Recuperación', 'GT', 'S', '1.0', '2029-01-01', 'Líder de TI', 'Procesos de Soporte/Apoyo', None),
    ('DI', 'DI-DI-E-801', 'Manual del Sistema de Gestión de Calidad', 'DI', 'E', '1.0', '2029-01-01', 'Coordinador de Calidad', 'Procesos Estratégicos', None),
    ('IN', 'IN-GI-C-201', 'Instructivo para el Control de Documentos', 'GI', 'C', '1.0', '2028-06-30', 'Coordinador de Calidad', 'Procesos Estratégicos', None)
]

SAMPLE_FORMATOS = [
    ('FR-GA-A-501', 'Formato Solicitud de Pedido', 'Procesos de Soporte/Apoyo', 'GA', 'A', '1.0', '2025-01-01', '2028-12-31', 'Activo', None),
    ('FR-GH-T-502', 'Formato Evaluación de Desempeño', 'Procesos de Soporte/Apoyo', 'GH', 'T', '1.0', '2025-01-01', '2028-12-31', 'Activo', None),
    ('FR-GT-S-503', 'Formato Reporte de Incidentes de TI', 'Procesos de Soporte/Apoyo', 'GT', 'S', '1.0', '2025-01-01', '2029-01-01', 'Activo', None),
    ('FR-GI-C-504', 'Formato Control de Cambios Documentales', 'Procesos Estratégicos', 'GI', 'C', '1.0', '2025-01-01', '2028-06-30', 'Activo', None),
    ('FR-GI-C-505', 'Formato Lista de Asistencia a Capacitación', 'Procesos Estratégicos', 'GI', 'C', '1.0', '2025-01-01', '2028-06-30', 'Activo', None)
]

SAMPLE_PERSONAL = [
    ('Juan Pérez', 'Director de Operaciones'),
    ('María Gómez', 'Coordinadora de Calidad'),
    ('Carlos López', 'Especialista en Procesos'),
    ('Laura Martínez', 'Directora de Talento Humano')
]

def init_db(db_path=DB_FILE):
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f'Base de datos anterior eliminada: {db_path}')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Crear Tablas
    cursor.execute('''
        CREATE TABLE personal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cargo TEXT NOT NULL,
            UNIQUE(nombre, cargo)
        );
    ''')

    cursor.execute('''
        CREATE TABLE documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            codigo_mergefield TEXT NOT NULL UNIQUE
        );
    ''')

    cursor.execute('''
        CREATE TABLE tipos_documento (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL
        );
    ''')

    cursor.execute('''
        CREATE TABLE procesos (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL
        );
    ''')

    cursor.execute('''
        CREATE TABLE subprocesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_proceso TEXT NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            FOREIGN KEY(codigo_proceso) REFERENCES procesos(codigo)
        );
    ''')

    cursor.execute('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            nombre_completo TEXT,
            email TEXT UNIQUE,
            rol TEXT CHECK(rol IN ('admin', 'user')) NOT NULL DEFAULT 'user',
            activo BOOLEAN DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_acceso TIMESTAMP
        );
    ''')

    cursor.execute('''
        CREATE TABLE lista_formatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            macroproceso TEXT,
            proceso TEXT,
            subproceso TEXT,
            version TEXT,
            fecha_actualizacion DATE,
            fecha_caducidad TEXT,
            estado TEXT,
            url_sharepoint TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE lista_documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_documento TEXT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            macroproceso TEXT,
            proceso TEXT,
            subproceso TEXT,
            version_actual TEXT,
            fecha_caducidad DATE,
            responsable_lider TEXT,
            url_sharepoint TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE config_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_documento TEXT NOT NULL,
            seccion TEXT NOT NULL,
            prompt_sistema TEXT NOT NULL,
            prompt_instrucciones TEXT NOT NULL,
            activo BOOLEAN DEFAULT 1,
            UNIQUE(tipo_documento, seccion)
        );
    ''')

    cursor.execute('''
        CREATE TABLE borradores (
            id TEXT PRIMARY KEY,
            content JSON NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cursor.execute('''
        CREATE TABLE document_styles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            style_type TEXT CHECK(style_type IN ('Procedimiento', 'Formato')) NOT NULL UNIQUE,
            body_font_family TEXT,
            body_font_size INTEGER,
            body_font_color TEXT,
            title_font_family TEXT,
            title_font_size INTEGER,
            title_font_color TEXT,
            table_header_fill TEXT,
            table_header_text_color TEXT,
            header_code_fill TEXT,
            header_code_text_color TEXT,
            margin_top REAL,
            margin_bottom REAL,
            margin_left REAL,
            margin_right REAL
        );
    ''')

    cursor.execute('''
        CREATE TABLE system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    ''')

    # 2. Poblar Tipos de Documento
    tipos = [
        ('PR', 'Procedimiento'),
        ('DI', 'Documento Institucional'),
        ('IN', 'Instructivo'),
        ('FR', 'Formato')
    ]
    cursor.executemany('INSERT INTO tipos_documento (codigo, nombre) VALUES (?, ?);', tipos)

    # 3. Poblar Procesos y Subprocesos
    cursor.executemany('INSERT INTO procesos (codigo, nombre) VALUES (?, ?);', PROCESOS)
    cursor.executemany('INSERT INTO subprocesos (codigo_proceso, codigo, nombre) VALUES (?, ?, ?);', SUBPROCESOS)

    # 4. Poblar Usuarios Demo
    admin_hash = generate_password_hash('admin123')
    user_hash = generate_password_hash('user123')
    usuarios = [
        ('admin', admin_hash, 'Administrador del Sistema', 'admin@example.com', 'admin', 1),
        ('usuario', user_hash, 'Usuario Demostración', 'usuario@example.com', 'user', 1)
    ]
    cursor.executemany('''
        INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol, activo)
        VALUES (?, ?, ?, ?, ?, ?);
    ''', usuarios)

    # 5. Poblar Personal de Ejemplo
    cursor.executemany('INSERT INTO personal (nombre, cargo) VALUES (?, ?);', SAMPLE_PERSONAL)

    # 6. Poblar Estilos de Documento
    for s in DOCUMENT_STYLES:
        cursor.execute('''
            INSERT INTO document_styles (
                style_type, body_font_family, body_font_size, body_font_color,
                title_font_family, title_font_size, title_font_color,
                table_header_fill, table_header_text_color,
                header_code_fill, header_code_text_color,
                margin_top, margin_bottom, margin_left, margin_right
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''', (
            s['style_type'], s['body_font_family'], s['body_font_size'], s['body_font_color'],
            s['title_font_family'], s['title_font_size'], s['title_font_color'],
            s['table_header_fill'], s['table_header_text_color'],
            s['header_code_fill'], s['header_code_text_color'],
            s['margin_top'], s['margin_bottom'], s['margin_left'], s['margin_right']
        ))

    # 7. Poblar Config Prompts
    cursor.executemany('''
        INSERT INTO config_prompts (tipo_documento, seccion, prompt_sistema, prompt_instrucciones, activo)
        VALUES (?, ?, ?, ?, ?);
    ''', CONFIG_PROMPTS)

    # 8. Poblar System Config
    cursor.execute("INSERT INTO system_config (key, value) VALUES ('enable_ia_global', '1');")

    # 9. Poblar Documentos y Formatos de Ejemplo
    cursor.executemany('''
        INSERT INTO lista_documentos (tipo_documento, codigo, nombre, proceso, subproceso, version_actual, fecha_caducidad, responsable_lider, macroproceso, url_sharepoint)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    ''', SAMPLE_DOCUMENTOS)

    cursor.executemany('''
        INSERT INTO lista_formatos (codigo, nombre, macroproceso, proceso, subproceso, version, fecha_actualizacion, fecha_caducidad, estado, url_sharepoint)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    ''', SAMPLE_FORMATOS)

    conn.commit()
    conn.close()
    print('Base de datos inicializada exitosamente con datos limpios y seguros.')

if __name__ == '__main__':
    init_db()
