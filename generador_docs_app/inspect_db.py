import sqlite3
import os

db_path = 'database.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        target_tables = ['lista_documentos', 'lista_formatos']
        
        for table_name in target_tables:
            print(f"\nSchema for {table_name}:")
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                found = False
                for col in columns:
                    print(col)
                    if 'url_sharepoint' in col[1]:
                        found = True
                if found:
                    print(f"CONFIRMED: {table_name} has url_sharepoint")
                else:
                    print(f"WARNING: {table_name} does NOT have url_sharepoint")
            except Exception as e:
                print(f"Error checking {table_name}: {e}")
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
