import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, g
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import auth
import document_app
from flask import Blueprint

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_dev_only')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'plantillas_descargas')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.register_blueprint(auth.bp)
app.register_blueprint(document_app.bp)

# Menu Routes defined here for simplicity
menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/menu/user')
@auth.login_required
def user_menu():
    return render_template('menu/user_menu.html')

@menu_bp.route('/menu/admin')
@auth.admin_required
def admin_menu():
    return render_template('menu/admin_menu.html')

@menu_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@menu_bp.route('/plantillas')
@auth.login_required
def descargas():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.lower().endswith(('.doc', '.docx'))]
    return render_template('plantillas/descargas.html', files=files)

@menu_bp.route('/plantillas/descargar/<filename>')
@auth.login_required
def descargar_plantilla(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@menu_bp.route('/plantillas/subir', methods=['POST'])
@auth.admin_required
def subir_plantilla():
    if 'archivo' not in request.files:
        flash('No se seleccionó ningún archivo.')
        return redirect(url_for('menu.descargas'))
    
    file = request.files['archivo']
    if file.filename == '':
        flash('No se seleccionó ningún archivo.')
        return redirect(url_for('menu.descargas'))
        
    if file:
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in ['.doc', '.docx']:
             flash('Solo se permiten archivos Word (.doc, .docx)')
             return redirect(url_for('menu.descargas'))

        # Check file size (2MB limit)
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        
        if file_length > 2 * 1024 * 1024:
            flash('El archivo supera el límite de 2MB.')
            return redirect(url_for('menu.descargas'))

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('Plantilla subida exitosamente.')
    else:
        flash('Error al subir el archivo.')
        
    return redirect(url_for('menu.descargas'))

@menu_bp.route('/plantillas/eliminar', methods=['POST'])
@auth.admin_required
def eliminar_plantilla():
    filename = request.form.get('filename')
    password = request.form.get('password')
    
    if not check_password_hash(g.user['password_hash'], password):
        flash('Contraseña incorrecta. No se pudo eliminar el archivo.')
        return redirect(url_for('menu.descargas'))

    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f'Archivo {filename} eliminado.')
        else:
            flash('El archivo no existe.')
    except Exception as e:
        flash(f'Error al eliminar: {e}')
        
    return redirect(url_for('menu.descargas'))

app.register_blueprint(menu_bp)

import admin
import maestros
import admin_ia
app.register_blueprint(admin.bp)
app.register_blueprint(maestros.bp)
app.register_blueprint(admin_ia.bp)

# Registro API Power BI
import api_bi
app.register_blueprint(api_bi.bp)

import standardizer_tool
app.register_blueprint(standardizer_tool.bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
