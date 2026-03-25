from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db", check_same_thread=False)

def init_db():
    conn = sqlite3.connect("database.db")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aadhaar TEXT UNIQUE,
        name TEXT,
        voted INTEGER DEFAULT 0
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        party TEXT
    )
    """)

    # 🔥 Insert demo user (VERY IMPORTANT)
    conn.execute("INSERT OR IGNORE INTO users (aadhaar, name, voted) VALUES ('1234', 'Kunal', 0)")
    conn.execute("INSERT OR IGNORE INTO users (aadhaar, name, voted) VALUES ('5678', 'sakshi', 0)")
    conn.execute("INSERT OR IGNORE INTO users (aadhaar, name, voted) VALUES ('1468', 'munazeh', 0)")


    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template("login.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    aadhaar = request.form['aadhaar']

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE aadhaar=?", (aadhaar,)).fetchone()

    if user:
        session['temp_user'] = aadhaar
        return render_template("otp.html")
    else:
        return "Invalid Aadhaar!"

# ---------------- VERIFY OTP ----------------
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    entered = request.form['otp'].strip()

    # 🔥 FIXED OTP (NO BUGS)
    if entered == "1234":
        session['user'] = session.get('temp_user')
        return redirect('/vote')

    return "Wrong OTP!"

# ---------------- VOTING PAGE ----------------
@app.route('/vote')
def vote():
    if 'user' not in session:
        return redirect('/')
    return render_template("vote.html")

# ---------------- CAST VOTE ----------------
@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    if 'user' not in session:
        return redirect('/')

    aadhaar = session['user']
    party = request.form['party']

    db = get_db()

    user = db.execute("SELECT voted FROM users WHERE aadhaar=?", (aadhaar,)).fetchone()

    if user[0] == 1:
        return "You have already voted!"

    db.execute("INSERT INTO votes (party) VALUES (?)", (party,))
    db.execute("UPDATE users SET voted=1 WHERE aadhaar=?", (aadhaar,))
    db.commit()

    # 🔥 GET RESULTS FOR CHART
    results = db.execute("SELECT party, COUNT(*) FROM votes GROUP BY party").fetchall()

    return render_template("result.html", results=results)
# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)