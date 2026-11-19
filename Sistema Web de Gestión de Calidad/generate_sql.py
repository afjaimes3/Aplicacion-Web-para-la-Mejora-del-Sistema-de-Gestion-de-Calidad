"""
Generate SQL insert statements from data_export.json
"""
import json

with open('data_export.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def escape_sql(val):
    if val is None or val == 'nan':
        return 'NULL'
    if isinstance(val, str):
        # Escape single quotes
        escaped = val.replace("'", "''")
        return f"'{escaped}'"
    return str(val)

# Generate SQL for lista_formatos
formatos = data.get('lista_formatos', [])
print(f"-- lista_formatos: {len(formatos)} records")

with open('insert_formatos.sql', 'w', encoding='utf-8') as f:
    f.write("-- Insert lista_formatos\n")
    for fmt in formatos:
        cols = ['codigo', 'nombre', 'macroproceso', 'proceso', 'subproceso', 'version', 'fecha_actualizacion', 'fecha_caducidad', 'estado', 'url_sharepoint']
        vals = [escape_sql(fmt.get(c)) for c in cols]
        f.write(f"INSERT INTO lista_formatos ({', '.join(cols)}) VALUES ({', '.join(vals)});\n")

# Generate SQL for lista_documentos  
docs = data.get('lista_documentos', [])
print(f"-- lista_documentos: {len(docs)} records")

with open('insert_documentos.sql', 'w', encoding='utf-8') as f:
    f.write("-- Insert lista_documentos\n")
    for doc in docs:
        cols = ['tipo_documento', 'codigo', 'nombre', 'macroproceso', 'proceso', 'subproceso', 'version_actual', 'fecha_caducidad', 'responsable_lider', 'url_sharepoint']
        vals = [escape_sql(doc.get(c)) for c in cols]
        f.write(f"INSERT INTO lista_documentos ({', '.join(cols)}) VALUES ({', '.join(vals)});\n")

# Generate SQL for borradores
borradores = data.get('borradores', [])
print(f"-- borradores: {len(borradores)} records")

with open('insert_borradores.sql', 'w', encoding='utf-8') as f:
    f.write("-- Insert borradores\n")
    for b in borradores:
        content = b.get('content', '{}')
        if isinstance(content, str):
            content_escaped = content.replace("'", "''")
        else:
            content_escaped = json.dumps(content, ensure_ascii=False).replace("'", "''")
        updated = escape_sql(b.get('updated_at'))
        f.write(f"INSERT INTO borradores (id, content, updated_at) VALUES ('{b['id']}', '{content_escaped}'::jsonb, {updated});\n")

print("\nSQL files generated:")
print("  - insert_formatos.sql")
print("  - insert_documentos.sql") 
print("  - insert_borradores.sql")
