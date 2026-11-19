import sqlite3
import json

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row

tables = [
    'personal', 'documentos', 'tipos_documento', 'procesos', 'subprocesos',
    'usuarios', 'lista_formatos', 'lista_documentos', 'config_prompts',
    'borradores', 'document_styles', 'system_config'
]

output = {}

for table in tables:
    try:
        cursor = conn.execute(f'SELECT * FROM {table}')
        rows = [dict(row) for row in cursor.fetchall()]
        output[table] = rows
        print(f"{table}: {len(rows)} rows")
    except Exception as e:
        print(f"{table}: ERROR - {e}")
        output[table] = []

with open('data_export.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

conn.close()
print("\nData exported to data_export.json")
