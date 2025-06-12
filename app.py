import cv2
import numpy as np
import json
import time
import sqlite3
from flask import Flask, render_template, Response, jsonify, request
import threading
from datetime import datetime, timedelta

app = Flask(__name__)

# Load models
AGE_MODEL = "models/age_net.caffemodel"
GENDER_MODEL = "models/gender_net.caffemodel"
AGE_PROTO = "models/deploy_age.prototxt"
GENDER_PROTO = "models/deploy_gender.prototxt"

age_net = cv2.dnn.readNet(AGE_MODEL, AGE_PROTO)
gender_net = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)

GENDER_CLASSES = ["Male", "Female"]
AGE_BUCKETS = ['0-2', '4-6', '8-12', '15-20', '25-32','38-43', '48-53', '60-100']
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
cap = cv2.VideoCapture(0)

current_ad = "static/default_ad.jpg"
detected_faces = {}
start_time = time.time()

# Load advertisement data from JSON
try:
    with open("adv.json", "r") as file:
        ad_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    ad_data = {}

def get_age_label(index):
    if index == 0:
        return "0-2"
    elif index == 1:
        return "4-6"
    elif index == 2:
        return "8-12"
    elif index == 3:
        return "15-20"
    elif index == 4:
        return "25-32"
    elif index == 5:
        return "38-43"
    elif index == 6:
        return "48-53"
    else:
        return "60-100"

def get_demographic_counts():
    conn = sqlite3.connect("advertisement.db")
    c = conn.cursor()

    counts = {
        "Male": {age: 0 for age in AGE_BUCKETS},
        "Female": {age: 0 for age in AGE_BUCKETS}
    }

    for gender in GENDER_CLASSES:
        for age in AGE_BUCKETS:
            c.execute("SELECT COUNT(*) FROM demographics WHERE gender=? AND age=?", (gender, age))
            result = c.fetchone()
            counts[gender][age] = result[0] if result else 0

    conn.close()
    return counts

@app.route('/filter_data', methods=['GET'])
def filter_data():
    gender = request.args.get('gender')
    age = request.args.get('age')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = sqlite3.connect("advertisement.db")
    c = conn.cursor()

    query = "SELECT gender, age, COUNT(*) FROM demographics WHERE 1=1"
    params = []

    if gender:
        query += " AND gender = ?"
        params.append(gender)
    if age:
        query += " AND age = ?"
        params.append(age)
    if start_date and end_date:
        query += " AND timestamp BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    query += " GROUP BY gender, age"

    c.execute(query, params)
    results = c.fetchall()
    conn.close()

    data = [{"gender": row[0], "age": row[1], "count": row[2]} for row in results]
    return jsonify(data)

@app.route('/get_counts')
def get_counts():
    return jsonify(get_demographic_counts())

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

def get_advertisement(gender, age):
    if gender in ad_data and age in ad_data[gender]:
        return ad_data[gender][age]
    return "static/default_ad.jpg"

def save_data(gender, age, ad_image):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("advertisement.db")
    c = conn.cursor()
    c.execute("INSERT INTO demographics (gender, age, ad_image, timestamp) VALUES (?, ?, ?, ?)",
              (gender, age, ad_image, timestamp))
    conn.commit()
    conn.close()

    try:
        with open("data.json", "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({
        "gender": gender,
        "age": age,
        "time": timestamp,
        "ad_image": ad_image
    })

    with open("data.json", "w") as file:
        json.dump(data, file, indent=4)

def is_new_face(x, y, w, h):
    global detected_faces
    now = time.time()
    for (px, py, pw, ph, _, _, ts) in detected_faces.values():
        if abs(px - x) < 50 and abs(py - y) < 50 and abs(pw - w) < 20 and abs(ph - h) < 20:
            return False
    detected_faces[(x, y, w, h)] = (x, y, w, h, None, None, now)
    detected_faces = {key: val for key, val in detected_faces.items() if now - val[-1] < 10}
    return True

def detect_gender():
    global current_ad, detected_faces, start_time

    while True:
        if time.time() - start_time < 3:
            continue

        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        for (x, y, w, h) in faces:
            if not is_new_face(x, y, w, h):
                continue

            face = frame[y:y+h, x:x+w]
            blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227),
                                         (78.426, 87.769, 114.896), swapRB=False)

            gender_net.setInput(blob)
            gender_preds = gender_net.forward()
            gender = GENDER_CLASSES[gender_preds[0].argmax()]

            age_net.setInput(blob)
            age_preds = age_net.forward()
            age_index = age_preds[0].argmax()
            age = get_age_label(age_index)

            color = (255, 0, 0) if gender == "Male" else (147, 20, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, f"{gender}, {age}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            current_ad = get_advertisement(gender, age)
            save_data(gender, age, current_ad)

        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

threading.Thread(target=detect_gender, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(detect_gender(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_ad')
def get_ad():
    """Returns the latest advertisement based on detected gender & age."""
    global current_ad
    if time.time() - start_time < 10:
        return jsonify({"ad_image": "static/default_ad.jpg"})  
    return jsonify({"ad_image": current_ad})


@app.route('/get_unique_count')
def get_unique_count():
    conn = sqlite3.connect("advertisement.db")
    c = conn.cursor()
    one_hour_ago = datetime.now() - timedelta(hours=1)
    c.execute("SELECT COUNT(*) FROM demographics WHERE timestamp >= ?", (one_hour_ago.strftime("%Y-%m-%d %H:%M:%S"),))
    count = c.fetchone()[0]
    conn.close()
    return jsonify({"unique_visitors": count})

def init_db():
    conn = sqlite3.connect("advertisement.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS demographics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gender TEXT,
                    age TEXT,
                    ad_image TEXT,
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/status')
def get_status():
    global no_face_detected
    return jsonify({"no_face": no_face_detected})

if __name__ == "__main__":
    app.run(debug=True)
