
import sqlite3
import os

def check_db(path):
    print(f"\n--- Checking {path} ---")
    if not os.path.exists(path):
        print("File does not exist.")
        return

    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # 1. List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", [t[0] for t in tables])
        
        # 2. Check global_memory if it exists
        if ('global_memory',) in tables:
            cursor.execute("SELECT count(*) FROM global_memory")
            print("global_memory count:", cursor.fetchone()[0])
            
            cursor.execute("SELECT * FROM global_memory LIMIT 5")
            for row in cursor.fetchall():
                print("  Memory:", row)
        else:
            print("No 'global_memory' table.")

        # 3. Check tutor_chat if it exists (for chronos.db)
        if ('tutor_chat',) in tables:
            cursor.execute("SELECT count(*) FROM tutor_chat")
            print("tutor_chat count:", cursor.fetchone()[0])
            
            cursor.execute("SELECT title, created_at FROM tutor_chat LIMIT 3")
            for row in cursor.fetchall():
                print("  Chat:", row)
                
        conn.close()
    except Exception as e:
        print(f"Error reading {path}: {e}")

if __name__ == "__main__":
    check_db('data/chronomem.db')
    check_db('data/chronos.db')
