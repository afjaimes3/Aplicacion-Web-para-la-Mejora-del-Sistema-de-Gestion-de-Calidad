import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

print("=" * 60)
print("DATABASE SCHEMA ANALYSIS")
print("=" * 60)

for (table_name,) in tables:
    print(f"\n### TABLE: {table_name}")
    print("-" * 40)
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        cid, name, col_type, notnull, default, pk = col
        pk_str = " [PK]" if pk else ""
        nn_str = " NOT NULL" if notnull else ""
        print(f"  - {name}: {col_type}{pk_str}{nn_str}")
    
    # Show row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    print(f"  (Rows: {count})")

conn.close()
