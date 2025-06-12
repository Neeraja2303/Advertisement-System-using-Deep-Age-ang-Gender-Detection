def init_db():
    conn = sqlite3.connect("advertisement.db")
    c = conn.cursor()
    
    # Table to store every demographic detection
    c.execute('''CREATE TABLE IF NOT EXISTS demographics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gender TEXT,
                    age TEXT,
                    ad_image TEXT,
                    timestamp TEXT
                )''')

    # Table to store unique faces (once per hour)
    c.execute('''CREATE TABLE IF NOT EXISTS unique_faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gender TEXT,
                    age TEXT,
                    ad_image TEXT,
                    timestamp TEXT,
                    encoding BLOB
                )''')

    conn.commit()
    conn.close()
