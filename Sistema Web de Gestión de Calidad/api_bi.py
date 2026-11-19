import os
import sqlite3
from flask import Blueprint, jsonify, request
from db import DB_FILE

# Blueprint para Power BI
bp = Blueprint('api_bi', __name__, url_prefix='/api/bi')

# Configuración de Seguridad
# La API Key se lee exclusivamente desde la variable de entorno POWERBI_API_KEY
# Configura esta variable en tu archivo .env antes de usar la integración con Power BI.
API_KEY_POWERBI = os.getenv('POWERBI_API_KEY', '')

def get_readonly_db():
    """
    Crea una conexión estricta de SOLO LECTURA a la base de datos.
    Cualquier intento de escritura generará un error inmediato.
    """
    try:
        # Usamos URI con mode=ro (Read Only)
        abs_path = os.path.abspath(DB_FILE)
        conn = sqlite3.connect(f"file:{abs_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error conectando a BD Read-Only: {e}")
        return None

def require_api_key(view_function):
    """Decorador para validar la API Key en Headers o URL"""
    def decorated_function(*args, **kwargs):
        # Power BI y otros clientes pueden enviar la clave de varias formas:
        # 1. Query Params: key, api_key
        # 2. Headers: ApiKey, X-API-KEY, Authorization (Bearer)
        
        # Intentar obtener de Query Params
        request_key = request.args.get('key') or request.args.get('api_key')
        
        # Si no está en Query Params, intentar Headers
        if not request_key:
            request_key = request.headers.get('ApiKey') or request.headers.get('X-API-KEY')
            
        # Si aun no está, verifiar Authorization: Bearer <token>
        if not request_key:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith("Bearer "):
                request_key = auth_header.split(" ")[1]
        
        if request_key and request_key == API_KEY_POWERBI:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"error": "Acceso denegado. API Key inválida o no proporcionada."}), 401
    
    # Necesario para evitar conflictos de nombres en Flask
    decorated_function.__name__ = view_function.__name__
    return decorated_function

# --- ENDPOINTS (Solo GET) ---

@bp.route('/documentos', methods=['GET'])
@require_api_key
def get_documentos():
    conn = get_readonly_db()
    if not conn: return jsonify({"error": "Error de conexión BD"}), 500
    
    try:
        rows = conn.execute('SELECT * FROM lista_documentos').fetchall()
        data = [dict(row) for row in rows]
        return jsonify(data)
    finally:
        conn.close()

@bp.route('/formatos', methods=['GET'])
@require_api_key
def get_formatos():
    conn = get_readonly_db()
    if not conn: return jsonify({"error": "Error de conexión BD"}), 500
    
    try:
        rows = conn.execute('SELECT * FROM lista_formatos').fetchall()
        data = [dict(row) for row in rows]
        return jsonify(data)
    finally:
        conn.close()

@bp.route('/procesos', methods=['GET'])
@require_api_key
def get_procesos():
    conn = get_readonly_db()
    if not conn: return jsonify({"error": "Error de conexión BD"}), 500
    
    try:
        rows = conn.execute('SELECT * FROM procesos').fetchall()
        data = [dict(row) for row in rows]
        return jsonify(data)
    finally:
        conn.close()

@bp.route('/subprocesos', methods=['GET'])
@require_api_key
def get_subprocesos():
    conn = get_readonly_db()
    if not conn: return jsonify({"error": "Error de conexión BD"}), 500
    
    try:
        rows = conn.execute('SELECT * FROM subprocesos').fetchall()
        data = [dict(row) for row in rows]
        return jsonify(data)
    finally:
        conn.close()
