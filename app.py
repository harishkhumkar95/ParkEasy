# app.py
# Author: Harish Khumkar
# Description: Flask backend for ParkEasy app (handles registration, login, session, MongoDB, and parking data search)
# Last updated: 31-07-2025
#.\venv\Scripts\Activate

import csv
import os
from pathlib import Path
from flask_mail import Mail, Message
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_pymongo import PyMongo
import bcrypt
import stripe
import joblib
from datetime import datetime
import random
from datetime import datetime
from flask import request, jsonify
from joblib import load
ml_model = load("parking_model.pkl")
from dotenv import load_dotenv
load_dotenv() 

# --------------------------------------------
# Initialize Flask app and secret key
# --------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
# ✅ Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")


mail = Mail(app)

# Load trained ML model once
MODEL_PATH = Path(__file__).parent / "parking_model.pkl"
ml_model = joblib.load(MODEL_PATH)


# --------------------------------------------
# Load Parking Data into memory (lat/lon ready)
# --------------------------------------------
PARKING_DATA = []
csv_file_path = Path(__file__).parent / 'Dublin_City_Centre_Accessible_Parking_2021.csv'

#To get remote acces to the payment system
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

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
app.config['MONGO_URI'] = os.getenv("MONGO_URI")
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



@app.route('/api/filtered-status', methods=['POST'])
def filtered_status():
    try:
        coords = request.json.get('coordinates', [])
        updates = []

        for coord in coords:
            lat = coord.get("lat")
            lon = coord.get("lon")

            spot = mongo.db.parking_spots.find_one({
                "latitude": lat,
                "longitude": lon
            }, {"_id": 0})

            if spot:
                updates.append(spot)

        return jsonify(updates)

    except Exception as e:
        print("❌ filtered_status error:", e)
        return jsonify({"error": str(e)}), 500


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

@app.route('/api/parking')
def get_parking_data():
    data = list(collection.find({}, {"_id": 0}))
    return jsonify(data)




#----------------------------------------
#predictive machine learning model 
#----------------------------------------
@app.route('/predict-availability', methods=['POST'])
def predict_availability():
    from flask import request, jsonify
    from datetime import datetime
    data = request.get_json()
    try:
        lat = float(data['lat'])
        lon = float(data['lon'])
        date = data['date']
        time = data['time']

        day = datetime.strptime(date, "%Y-%m-%d").weekday()
        hour = int(time.split(":")[0])

        prediction = ml_model.predict([[lat, lon, hour, day]])[0]
        result = "Available" if prediction == 1 else "Full"

        return jsonify({"prediction": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

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
         'status': 'Confirmed',  
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
        mongo.db.emails.insert_one({
    'to': user_email,
    'subject': msg.subject,
    'body': msg.body,
    'html': msg.html,
    'sent_at': datetime.utcnow(),
    'ticket': ticket_number
    })
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
    bookings = list(mongo.db.bookings.find({'user': user_email}).sort('timestamp', -1))

    return render_template('my_bookings.html', bookings=bookings)

#cancel booking 
@app.route('/cancel-booking', methods=['POST'])
def cancel_booking():
    if 'email' not in session:
        return redirect('/login')

    ticket_number = request.form.get('ticket_number')
    user_email = session['email']

    result = mongo.db.bookings.update_one(
        {'ticket_number': ticket_number, 'user': user_email},
        {'$set': {'status': 'Cancelled'}}
    )

    if result.modified_count == 1:
        print(f"🟥 Booking {ticket_number} cancelled.")
    else:
        print(f"⚠️ Booking not found or not updated.")

    return redirect('/my-bookings')

#Admin Dashboard
@app.route('/admin-dashboard')
def admin_dashboard():
    from datetime import datetime, timedelta
    if 'email' not in session:
        return redirect('/login')

    # Restrict to your admin email
    if session['email'] != 'harishkhumkar95@gmail.com':
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


#Payment method
@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        # Booking form data
        customer_name = request.form.get('customer_name')
        spot_name = request.form.get('spot_name')
        date = request.form.get('date')
        time = request.form.get('time')
        hours = int(request.form.get('hours', 1))
        user_email = session.get('email', 'guest')

        total_price = hours * 2  # €2/hour

        # ✅ Save data in session for later use
        session['booking_temp'] = {
            'customer_name': customer_name,
            'spot_name': spot_name,
            'date': date,
            'time': time,
            'hours': hours,
            'email': user_email,
            'total_price': total_price
        }

        stripe_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=user_email,
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': total_price * 100,  # in cents
                    'product_data': {
                        'name': f'Parking at {spot_name}',
                        'description': f'{hours}h on {date} at {time}'
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', _external=True),
            cancel_url=url_for('home', _external=True),
        )

        return redirect(stripe_session.url, code=303)

    except Exception as e:
        return str(e)

    try:
        # Get booking details from form
        customer_name = request.form.get('customer_name')
        spot_name = request.form.get('spot_name')
        date = request.form.get('date')
        time = request.form.get('time')
        hours = int(request.form.get('hours', 1))
        user_email = session.get('email', 'guest')

        total_price = hours * 200  # €2/hour → in cents

        session_stripe = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=user_email,
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': total_price,
                    'product_data': {
                        'name': f'Parking at {spot_name}',
                        'description': f'{hours} hour(s) on {date} at {time}'
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', _external=True),
            cancel_url=url_for('home', _external=True),
        )

        return redirect(session_stripe.url, code=303)

    except Exception as e:
        return str(e)
#payment succses route
@app.route('/payment-success')
def payment_success():
    booking = session.get('booking_temp')
    if not booking:
        return "❌ No booking data found. Please try again.", 400

    # Generate ticket
    ticket_number = f"TKT{datetime.now().strftime('%H%M%S')}{random.randint(100, 999)}"

    # Save to MongoDB
    mongo.db.bookings.insert_one({
        'ticket_number': ticket_number,
        'customer_name': booking['customer_name'],
        'user': booking['email'],
        'spot_name': booking['spot_name'],
        'date': booking['date'],
        'time': booking['time'],
        'duration_hours': booking['hours'],
        'total_price_eur': booking['total_price'],
        'status': 'confirmed',
        'timestamp': datetime.utcnow()
    })

    # ✅ Send confirmation email (optional reuse)
    try:
        msg = Message(f"Your ParkEasy Booking: {ticket_number}", recipients=[booking['email']])
        msg.body = f"""
Hi {booking['customer_name']},

Your parking booking is confirmed!

📍 Spot: {booking['spot_name']}
📅 Date: {booking['date']}
⏰ Time: {booking['time']}
⏳ Duration: {booking['hours']} hour(s)
🎫 Ticket No: {ticket_number}
💶 Total: €{booking['total_price']}

Thank you for using ParkEasy!
        """
        mail.send(msg)
    except Exception as e:
        print("❌ Email send failed:", e)

    # Clear session data
    session.pop('booking_temp', None)

    return render_template('payment_success.html')

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
