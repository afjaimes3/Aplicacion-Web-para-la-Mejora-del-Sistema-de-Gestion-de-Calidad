from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import tempfile
from db import get_db_connection
from utils.docx_formatter import ProcedureFormatter
from utils.formats_formatter import FormatFormatter

bp = Blueprint('standardizer', __name__, url_prefix='/herramientas')

@bp.route('/estandarizador', methods=['GET', 'POST'])
def estandarizar():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo.')
            return redirect(request.url)
            
        file = request.files['file']
        style_type = request.form.get('style_type') # 'Procedimiento' or 'Formato'
        
        if file.filename == '':
            flash('No se seleccionó ningún archivo.')
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in ['.doc', '.docx']:
                flash('Solo se permiten archivos Word (.doc, .docx)')
                return redirect(request.url)
            
            # Check file size (2MB limit)
            file.seek(0, os.SEEK_END)
            file_length = file.tell()
            file.seek(0)
            
            if file_length > 2 * 1024 * 1024:
                flash('El archivo supera el límite de 2MB.')
                return redirect(request.url)

            # 1. Save temp input
            filename = secure_filename(file.filename)
            fd, input_path = tempfile.mkstemp(suffix='.docx')
            os.close(fd)
            file.save(input_path)
            
            # 2. Get config from DB
            conn = get_db_connection()
            config_row = conn.execute('SELECT * FROM document_styles WHERE style_type = ?', (style_type,)).fetchone()
            conn.close()
            
            if not config_row:
                flash(f"No se encontró configuración para '{style_type}'. Contacte al administrador.")
                return redirect(request.url)
            
            # Convert row to dict (se mantiene por compatibilidad futura)
            config = dict(config_row)
            
            # 3. Process con el formateador adecuado según selección
            if style_type == 'Formato':
                formatter = FormatFormatter()
            else:
                formatter = ProcedureFormatter()
            fd_out, output_path = tempfile.mkstemp(suffix=f'_estandarizado.docx')
            os.close(fd_out)
            
            try:
                # Usar el formateador completo para cualquier tipo de documento
                formatter.format_document(input_path, output_path)
                    
                return send_file(output_path, as_attachment=True, download_name=f"STD_{filename}")
            except Exception as e:
                flash(f"Error procesando el archivo: {e}")
                return redirect(request.url)
            finally:
                # Cleanup input
                try:
                    os.remove(input_path)
                except:
                    pass

    return render_template('tools/standardize.html')
