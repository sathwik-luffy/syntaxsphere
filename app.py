from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
import google.generativeai as genai

app = Flask(__name__)
# Enable CORS so the local HTML files can make fetch requests to this backend without issue
CORS(app)

# Configure Gemini API
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

DB_PATH = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template("syntax-sphere.html")

@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/app')
def app_page():
    return render_template("syntaxsphere-app.html")

@app.route('/data-structures')
def data_structures():
    return render_template("data_structures.html")

@app.route('/companies')
def companies():
    return render_template("syntax-sphere-companies.html")

@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"message": "Email and password required", "success": False}), 400
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        conn.close()
        return jsonify({"message": "User created successfully. You can now login.", "success": True}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "User already exists", "success": False}), 409
    except Exception as e:
        return jsonify({"message": str(e), "success": False}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"message": "Email and password required", "success": False}), 400
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # user tuple: (id, email, password)
        username = email.split('@')[0]
        return jsonify({
            "message": "Login successful", 
            "success": True,
            "user": {
                "email": user[1],
                "username": username
            }
        }), 200
    else:
        return jsonify({"message": "Invalid email or password", "success": False}), 401

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt')
    context = data.get('context', '')
    
    if not prompt:
        return jsonify({"message": "Prompt is required", "success": False}), 400
        
    if not GENAI_API_KEY:
        return jsonify({"message": "Gemini API key is not configured.", "success": False}), 500
        
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        full_prompt = f"Context: {context}\n\nUser Question: {prompt}\n\nPlease provide a clear, helpful, and concise explanation formatting with markdown."
        response = model.generate_content(full_prompt)
        return jsonify({"response": response.text, "success": True}), 200
    except Exception as e:
        return jsonify({"message": str(e), "success": False}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
