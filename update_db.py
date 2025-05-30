import sqlite3

conn = sqlite3.connect("todo.db")
conn.execute("ALTER TABLE tasks ADD COLUMN category TEXT")
conn.commit()
conn.close()
