from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import wikipedia
import bcrypt
import os

app = Flask(__name__)
app.secret_key = "=!oa-ggrrvi8mj9)y*_hdm^e=@!rjsoms&mh+_3h(038*pbtd&"

# --- INIT DATABASES ---
def init_user_db():
    conn = sqlite3.connect('users2.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def init_chat_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            user_message TEXT,
            bot_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_user_db()
init_chat_db()

# --- ROUTES ---
@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["username"])

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        try:
            conn = sqlite3.connect("users2.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists!"
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        conn = sqlite3.connect("users2.db")
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user[0]):
            session["username"] = username
            return redirect(url_for("home"))
        else:
            return "Invalid credentials!"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/get", methods=["GET"])              #api
def get_bot_response():
    user_input = request.args.get('msg', '').strip()
    username = session.get("username", "guest")

    if not user_input:
        return jsonify({'response': "Please enter a valid question."})#api

    try:
        summary = wikipedia.summary(user_input, sentences=2)
        bot_response = summary
    except wikipedia.exceptions.DisambiguationError as e:
        bot_response = f"Be more specific. Did you mean: {', '.join(e.options[:5])}?"
    except wikipedia.exceptions.PageError:
        bot_response = "Sorry, I couldn't find anything on that topic."
    except Exception as e:
        bot_response = f"Error: {str(e)}"

    # Save to chat history
    conn = sqlite3.connect("chat_history.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO chat (username, user_message, bot_response) VALUES (?, ?, ?)",
                (username, user_input, bot_response))
    conn.commit()
    conn.close()

    return jsonify({'response': bot_response})

if __name__ == "__main__":
    app.run(debug=True)
