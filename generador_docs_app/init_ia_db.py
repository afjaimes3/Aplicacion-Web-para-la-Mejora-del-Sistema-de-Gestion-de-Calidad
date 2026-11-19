import sqlite3
import os

DB_FILE = "database.db"

def init_ia_config():
    if not os.path.exists(DB_FILE):
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Create table for prompts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_documento TEXT NOT NULL,
                seccion TEXT NOT NULL,
                prompt_sistema TEXT NOT NULL,
                prompt_instrucciones TEXT NOT NULL,
                UNIQUE(tipo_documento, seccion)
            )
        ''')

        # Default system prompt
        system_base = """Actúa como un experto en redacción técnica, gestión de procesos y normas ISO de calidad. Tu tarea es corregir, completar y mejorar el texto proporcionado para un documento institucional. El idioma debe ser siempre ESPAÑOL.

Estructura institucional jerárquica (referencial, no exhaustiva):
Nivel 1: Consejo Superior.
Nivel 2: Rectoría.
Nivel 3: Secretaría General; Consejos/Comités; Vicerrectoría Académica e Investigación; Vicerrectoría Administrativa y Financiera; Cancillería; Educación Digital/Virtual; Dirección Artística y Cultural.
Nivel 4: Dependencias internas de cada unidad.
Nota: Respeta siempre estas jerarquías en la redacción, mencionando primero a los niveles superiores."""

        # Prompts for PR (Procedimiento)
        prompts_pr = [
            ('PR', 'objetivo', system_base, 'Completa la idea si parece cortada. Corrige ortografía y gramática. Mejora el tono para que sea formal e institucional. Devuelve SOLAMENTE el texto mejorado.'),
            ('PR', 'alcance', system_base, 'Requisito Específico para "Alcance": En esta sección se debe indicar claramente cuándo inicia y cuándo finaliza el procedimiento descrito en el documento. Ejemplo: “Este procedimiento aplica para la solicitud, aprobación y apoyo logístico para eventos... Inicia con la solicitud de la pre-reserva y termina con la consolidación de la documentación.”'),
            ('PR', 'responsables', system_base, 'Mejora la redacción técnica de los responsables. Devuelve SOLAMENTE el texto mejorado.'),
            ('PR', 'definiciones', system_base, 'Mejora la redacción técnica de las definiciones. Devuelve SOLAMENTE el texto mejorado.'),
            ('PR', 'tabla-actividades', system_base, """Los datos provienen de la tabla 'Descripción de Actividades'. Columnas: actividad_no (NO MODIFICAR), actividad_responsable (Cargo del responsable), actividad_descripcion (Descripción de la actividad), actividad_registro (Documento de registro).
Instrucciones:
1. Procesa TODAS las filas.
2. Mantén las claves EXACTAS.
3. Devuelve un objeto JSON con "nuevos_datos" y "analisis_general" (advertencias sobre consistencia global, repetidos, saltos lógicos).
4. Formato strictly JSON."""),
            ('PR', 'tabla-documentos-relacionados', system_base, """Los datos provienen de la tabla 'Documentos Relacionados'.
Instrucciones:
1. Analiza cada fila.
2. Compara con los documentos maestros sugeridos y la descripción de actividades previa para asegurar coherencia.
3. Devuelve un objeto JSON con "nuevos_datos" (filas corregidas) y "analisis_general" (sugerencias globales o advertencias).
4. Formato strictly JSON.""")
        ]

        for p in prompts_pr:
            cursor.execute('''
                INSERT OR REPLACE INTO config_prompts (tipo_documento, seccion, prompt_sistema, prompt_instrucciones)
                VALUES (?, ?, ?, ?)
            ''', p)

        conn.commit()
        print("Tabla config_prompts inicializada correctamente.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_ia_config()
