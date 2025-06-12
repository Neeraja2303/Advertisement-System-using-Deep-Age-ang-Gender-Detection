# face_utils.py
import face_recognition
import numpy as np
import sqlite3
import datetime
import io
import pickle

DB_PATH = "advertisement.db"

def is_unique_face(face_encoding):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT encoding, timestamp FROM unique_faces")
    known_faces = c.fetchall()
    conn.close()

    for enc_blob, ts in known_faces:
        known_encoding = pickle.loads(enc_blob)
        if face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.5)[0]:
            # Match found
            time_diff = datetime.datetime.now() - datetime.datetime.fromisoformat(ts)
            if time_diff.total_seconds() < 3600:  # within 1 hour
                return False
    return True

def save_unique_face_to_db(face_encoding, gender, age, ad_image):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    blob = pickle.dumps(face_encoding)
    timestamp = datetime.datetime.now().isoformat()

    c.execute("INSERT INTO unique_faces (gender, age, ad_image, timestamp, encoding) VALUES (?, ?, ?, ?, ?)",
              (gender, age, ad_image, timestamp, blob))
    conn.commit()
    conn.close()
