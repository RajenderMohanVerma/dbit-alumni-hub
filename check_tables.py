import sqlite3
conn = sqlite3.connect('alumni_network.db')
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables in database:")
for t in tables:
    print(f"  - {t[0]}")
conn.close()
