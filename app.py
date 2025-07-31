# app.py
# Author: Harish Khumkar
# Description: Flask backend for ParkEasy app (handles registration, login, session, MongoDB)
# Last updated: 30-07-2025

from flask import Flask, render_template, request, redirect, url_for, session
from flask_pymongo import PyMongo
import bcrypt

# -----------------------------------------------------------
# Initialize Flask app and secret key for session management
# -----------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'p@rke@sy2025'  # Used to secure session cookies

# -----------------------------------------------------------
# Configure MongoDB Atlas connection
# Replace <username>, <password>, <cluster> with your details
# -----------------------------------------------------------
app.config['MONGO_URI'] = "mongodb+srv://harishkumkar2014:Harish12345@parkeasycluster.sjyzlz3.mongodb.net/ParkEasy?retryWrites=true&w=majority&appName=ParkEasyCluster"
mongo = PyMongo(app)



# ---------------------------------------
# Route: Home page (dashboard after login)
# ---------------------------------------
@app.route('/')
def home():
    if 'email' in session:
        return render_template('home.html', email=session['email'])
    return redirect('/login')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')
# ---------------------------------------
# Route: Register new user
# ---------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'email': request.form['email']})

        # If user doesn't exist, create new user with hashed password
        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'email': request.form['email'], 'password': hashpass})
            return redirect(url_for('login'))

        return '❌ That email already exists!'

    return render_template('register.html')

# ---------------------------------------
# Route: Login existing user
# ---------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        user = users.find_one({'email': request.form['email']})

        # Validate entered password with stored hash
        if user and bcrypt.checkpw(request.form['password'].encode('utf-8'), user['password']):
            session['email'] = request.form['email']
            return redirect('/')
        return '❌ Invalid email/password combination.'

    return render_template('login.html')

# ---------------------------------------
# Route: Logout and clear session
# ---------------------------------------
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

# ---------------------------------------
# Start the Flask development server
# ---------------------------------------
if __name__ == '__main__':
    print("🚀 Starting ParkEasy Flask App...")
    app.run(debug=True)
