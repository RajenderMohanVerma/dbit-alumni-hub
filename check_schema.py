#!/usr/bin/env python3
import sqlite3

DB_FILE = 'college_pro.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def main():
    conn = get_db_connection()
    
    # Check alumni_profile columns
    print("=" * 80)
    print("ALUMNI_PROFILE TABLE STRUCTURE")
    print("=" * 80)
    
    columns = conn.execute("PRAGMA table_info(alumni_profile)").fetchall()
    for col in columns:
        print(f"{col['name']}: {col['type']}")
    
    conn.close()

if __name__ == '__main__':
    main()
