# app.py
# Author: Harish Khumkar
# Description: Flask backend for ParkEasy app (handles registration, login, session, MongoDB, and parking data search)
# Last updated: 31-07-2025

import csv
import os
from pathlib import Path
from flask_mail import Mail, Message
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_pymongo import PyMongo
import bcrypt

# --------------------------------------------
# Initialize Flask app and secret key
# --------------------------------------------
app = Flask(__name__)
app.secret_key = 'p@rke@sy2025'
# ✅ Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'harishkhumkar95@gmail.com'         # ⬅️ Your Gmail
app.config['MAIL_PASSWORD'] = 'yiulkdccmaurooce'            # ⬅️ App Password (not your real Gmail password)
app.config['MAIL_DEFAULT_SENDER'] = 'harishkumkar2014@gmail.com'   # ⬅️ Same as username

mail = Mail(app)


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
# csv_file_path = Path(__file__).parent / 'Dublin_City_Centre_Accessible_Parking_2021.csv'
csv_file_path = Path(__file__).parent / 'Cleaned_Parking_Dublin_V2.csv'


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

from datetime import datetime

import random
from datetime import datetime


# @app.route('/test-email')
# def test_email():
#     try:
#         msg = Message("🚀 ParkEasy Email Test", recipients=["your_email@gmail.com"])
#         msg.body = "This is a test email sent from your Flask app."
#         mail.send(msg)
#         return "✅ Test email sent successfully!"
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return f"❌ Test email failed: {e}"
    
@app.route('/book', methods=['POST'])
def book():
    customer_name = request.form.get('customer_name')
    spot_name = request.form.get('spot_name')
    date = request.form.get('date')
    time = request.form.get('time')
    hours = int(request.form.get('hours', 1))
    user_email = session.get('email', 'guest')

    if not all([customer_name, spot_name, date, time]):
        return "❌ Missing booking data", 400

    # Generate ticket
    ticket_number = f"TKT{datetime.now().strftime('%H%M%S')}{random.randint(100, 999)}"
    total_price = 2  # Flat rate

    # Store in MongoDB
    bookings = mongo.db.bookings
    bookings.insert_one({
        'ticket_number': ticket_number,
        'customer_name': customer_name,
        'user': user_email,
        'spot_name': spot_name,
        'date': date,
        'time': time,
        'duration_hours': hours,
        'total_price_eur': total_price,
        'timestamp': datetime.utcnow()
    })

    # ✅ Send Email Confirmation
    try:
        msg = Message(f"Your ParkEasy Booking: {ticket_number}", recipients=[user_email])

        # Render HTML template
        msg.html = render_template(
            'email_receipt.html',
            customer_name=customer_name,
            spot_name=spot_name,
            date=date,
            time=time,
            hours=hours,
            ticket_number=ticket_number,
            total=total_price
        )

        # Optional plain text fallback
        msg.body = f"""Hi {customer_name},

Your parking booking is confirmed!

Spot: {spot_name}
Date: {date}
Time: {time}
Duration: {hours} hour(s)
Ticket No: {ticket_number}
Total: €{total_price}

Thank you for using ParkEasy!
        """
  # ✅ Generate PDF receipt
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer)
        c.setFont("Helvetica", 12)
        c.drawString(100, 800, "ParkEasy Booking Receipt")
        c.drawString(100, 780, f"Customer: {customer_name}")
        c.drawString(100, 760, f"Spot: {spot_name}")
        c.drawString(100, 740, f"Date: {date}")
        c.drawString(100, 720, f"Time: {time}")
        c.drawString(100, 700, f"Hours: {hours}")
        c.drawString(100, 680, f"Ticket No: {ticket_number}")
        c.drawString(100, 660, f"Total: €{total_price}")
        c.save()
        pdf_buffer.seek(0)

        msg.attach(
            filename=f"ParkEasy_Receipt_{ticket_number}.pdf",
            content_type="application/pdf",
            data=pdf_buffer.read()
        )
        mail.send(msg)
        print("📧 Booking confirmation email sent.")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")

    return render_template(
        'booking_confirmation.html',
        ticket=ticket_number,
        customer=customer_name,
        spot=spot_name,
        date=date,
        time=time,
        hours=hours,
        total=total_price
    )

#my booking history
@app.route('/my-bookings')
def my_bookings():
    if 'email' not in session:
        return redirect('/login')

    user_email = session['email']
    bookings = mongo.db.bookings.find({'user': user_email}).sort('timestamp', -1)

    return render_template('my_bookings.html', bookings=bookings)

#Admin Dashboard
@app.route('/admin-dashboard')
def admin_dashboard():
    from datetime import datetime, timedelta
    if 'email' not in session:
        return redirect('/login')

    # Restrict to your admin email
    if session['email'] != 'youradmin@email.com':
        return "❌ Access denied", 403

    today = datetime.utcnow().date()
    bookings = mongo.db.bookings.find()
    
    daily_count = {}
    hourly_count = {}

    for b in bookings:
        day = b['timestamp'].strftime('%Y-%m-%d')
        hour = b['timestamp'].strftime('%H:00')
        daily_count[day] = daily_count.get(day, 0) + 1
        hourly_count[hour] = hourly_count.get(hour, 0) + 1

    return render_template('admin_dashboard.html', daily=daily_count, hourly=hourly_count)


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
