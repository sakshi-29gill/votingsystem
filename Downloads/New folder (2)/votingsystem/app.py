from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import random
from blockchain import Blockchain

app = Flask(__name__)
app.secret_key = "secret123"

blockchain = Blockchain()
otp_storage = {}

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    if not os.path.exists("database.db"):
        conn = sqlite3.connect("database.db")
        conn.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aadhaar TEXT UNIQUE,
            name TEXT,
            voted INTEGER DEFAULT 0
        )
        ''')
        conn.execute('''
        CREATE TABLE votes (
            party TEXT
        )
        ''')
        conn.close()

init_db()

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return render_template('login.html')

# -------- REGISTER --------
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    aadhaar = request.form['aadhaar']

    db = get_db()
    try:
        db.execute("INSERT INTO users(aadhaar, name, voted) VALUES (?, ?, 0)", (aadhaar, name))
        db.commit()
    except:
        return "⚠️ User already exists!"

    return redirect('/')

# -------- LOGIN + OTP --------
@app.route('/login', methods=['POST'])
def login():
    aadhaar = request.form['aadhaar']

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE aadhaar=?", (aadhaar,)).fetchone()

    if user:
        otp = str(random.randint(1000, 9999))
        otp_storage[aadhaar] = otp

        print("🔐 OTP:", otp)  # shown in terminal

        session['temp_user'] = aadhaar
        return render_template('otp.html')

    return "❌ Invalid Aadhaar!"

# -------- VERIFY OTP --------
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    entered = request.form['otp']
    aadhaar = session.get('temp_user')

    if otp_storage.get(aadhaar) == entered:
        session['user'] = aadhaar
        return redirect('/vote')

    return "❌ Wrong OTP!"

# -------- VOTING PAGE --------
@app.route('/vote')
def vote():
    if 'user' not in session:
        return redirect('/')
    return render_template('vote.html')

# -------- CAST VOTE --------
@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    if 'user' not in session:
        return redirect('/')

    party = request.form['party']
    aadhaar = session['user']

    db = get_db()
    check = db.execute("SELECT voted FROM users WHERE aadhaar=?", (aadhaar,)).fetchone()

    if check[0] == 1:
        return "❌ You have already voted!"

    # Blockchain logic
    prev_block = blockchain.get_previous_block()
    prev_hash = blockchain.hash(prev_block)
    blockchain.create_block(proof=1, previous_hash=prev_hash)

    db.execute("UPDATE users SET voted=1 WHERE aadhaar=?", (aadhaar,))
    db.execute("INSERT INTO votes(party) VALUES (?)", (party,))
    db.commit()

    return redirect('/result')

# -------- RESULTS --------
@app.route('/result')
def result():
    db = get_db()
    results = db.execute("SELECT party, COUNT(*) FROM votes GROUP BY party").fetchall()
    return render_template('result.html', results=results)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()