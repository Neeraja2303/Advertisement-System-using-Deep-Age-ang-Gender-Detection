import sqlite3

conn = sqlite3.connect('advertisement.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM unique_faces')
count = c.fetchone()[0]

print(f"Total unique faces in DB: {count}")

conn.close()
