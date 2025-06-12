import sqlite3

conn = sqlite3.connect("advertisement.db")
c = conn.cursor()

for row in c.execute("SELECT * FROM demographics"):
    print(row)

conn.close()

"""
import sqlite3

# Connect to the database
conn = sqlite3.connect("advertisement.db")
c = conn.cursor()

# Delete all rows from the table
c.execute("DELETE FROM demographics")

# Optional: Reset auto-increment ID (if any)
c.execute("DELETE FROM sqlite_sequence WHERE name='demographics'")

# Save changes and close connection
conn.commit()
conn.close()

print("All data cleared from 'demographics' table.")




import sqlite3

# Connect to the database
conn = sqlite3.connect("advertisement.db")
c = conn.cursor()

# Delete all rows where gender is 'Male'
c.execute("DELETE FROM demographics WHERE gender = 'Male'")

# Save changes and close connection
conn.commit()
conn.close()

print("All male records deleted from 'demographics' table.")

"""