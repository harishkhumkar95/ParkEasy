# app.py
# Author: Harish Khumkar
# Description: Flask backend for ParkEasy app (handles registration, login, session, MongoDB, and parking data search)
# Last updated: 31-07-2025

import csv
import os
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_pymongo import PyMongo
import bcrypt

# --------------------------------------------
# Initialize Flask app and secret key
# --------------------------------------------
app = Flask(__name__)
app.secret_key = 'p@rke@sy2025'

# --------------------------------------------
# Load Parking Data into memory (lat/lon ready)
# --------------------------------------------
PARKING_DATA = []
csv_file_path = Path(__file__).parent / 'Dublin_City_Centre_Accessible_Parking_2021.csv'


# if csv_file_path.exists():
#     try:
#         with open(csv_file_path, newline='', encoding='ISO-8859-1') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 if row['lat'] and row['lon']:
#                     PARKING_DATA.append({
#                         'spot_name': row['spot_name'],
#                         'availability': row['availability'],
#                         'lat': float(row['lat']),
#                         'lon': float(row['lon'])
#                     })

#         print(f"✅ Loaded {len(PARKING_DATA)} parking spots.")
#         for spot in PARKING_DATA[:3]:
#             print("📍 Example spot:", spot['spot_name'])

#     except Exception as e:
#         print(f"❌ Error reading CSV: {e}")
# else:
#     print("⚠️ Parking CSV not found!")

# --------------------------------------------
# Load Parking Data with coordinate validation
# --------------------------------------------
PARKING_DATA = []
csv_file_path = Path(__file__).parent / 'Dublin_City_Centre_Accessible_Parking_2021.csv'

if csv_file_path.exists():
    try:
        with open(csv_file_path, newline='', encoding='ISO-8859-1') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    lat_raw = row.get('lat', '').strip()
                    lon_raw = row.get('lon', '').strip()

                    if not lat_raw or not lon_raw:
                        print(f"⚠️ Missing coordinates: {row}")
                        continue

                    lat = float(lat_raw.replace(",", "").strip())
                    lon = float(lon_raw.replace(",", "").strip())

                    # Filter: only valid Dublin points
                    if 53.2 <= lat <= 53.8 and -6.5 <= lon <= -5.6:
                        PARKING_DATA.append({
                            'spot_name': row.get('spot_name', 'Unknown Spot'),
                            'availability': row.get('availability', '0'),
                            'lat': lat,
                            'lon': lon
                        })
                    else:
                        print(f"🛑 Rejected (outside range): {lat}, {lon} -> {row.get('spot_name')}")
                except Exception as e:
                    print(f"⚠️ Skipped due to parse error: {e} → Row: {row}")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
else:
    print("🚫 CSV file not found!")



# --------------------------------------------
# MongoDB Atlas Configuration
# --------------------------------------------
app.config['MONGO_URI'] = "mongodb+srv://harishkumkar2014:Harish12345@parkeasycluster.sjyzlz3.mongodb.net/ParkEasy?retryWrites=true&w=majority&appName=ParkEasyCluster"
mongo = PyMongo(app)

# --------------------------------------------
# Route: Home Page (Dashboard)
# --------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'email' not in session:
        return redirect('/login')

    if request.method == 'POST':
        mode = request.form['mode']
        location = request.form['location']
        date = request.form['date']
        time = request.form['time']

        matched_spots = [
            spot for spot in PARKING_DATA
            if location.lower() in spot['spot_name'].lower()
        ]

        print(f"🔍 User searched: {location}")
        print(f"✅ Found {len(matched_spots)} matching parking spots.")

        return render_template(
            'home.html',
            email=session['email'],
            results=matched_spots,
            all_spots=PARKING_DATA,
            mode=mode,
            location=location,
            date=date,
            time=time
        )

    # GET: show all spots on map
    return render_template(
        'home.html',
        email=session['email'],
        results=PARKING_DATA,      # map will use this
        all_spots=PARKING_DATA     # dropdown will use this
    )



# --------------------------------------------
# API Endpoint: Return all matched parking data (for Leaflet map)
# --------------------------------------------
@app.route('/api/parking', methods=['GET'])
def api_parking():
    query = request.args.get('location', '')
    filtered = [spot for spot in PARKING_DATA if query.lower() in spot['spot_name'].lower()]
    return jsonify(filtered)

# --------------------------------------------
# Static Pages
# --------------------------------------------
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# --------------------------------------------
# User Registration
# --------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'email': request.form['email']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'email': request.form['email'], 'password': hashpass})
            return redirect(url_for('login'))

        return '❌ That email already exists!'

    return render_template('register.html')

# --------------------------------------------
# User Login
# --------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        user = users.find_one({'email': request.form['email']})

        if user and bcrypt.checkpw(request.form['password'].encode('utf-8'), user['password']):
            session['email'] = request.form['email']
            return redirect('/')
        return '❌ Invalid email/password combination.'

    return render_template('login.html')

# --------------------------------------------
# Logout
# --------------------------------------------
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

# --------------------------------------------
# Run App
# --------------------------------------------
if __name__ == '__main__':
    print("🚀 Starting ParkEasy Flask App...")
    app.run(debug=True)
