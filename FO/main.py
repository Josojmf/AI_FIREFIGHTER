from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import json
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "sargento-secret-key"

# Cargar modelo FLAN-T5
print("🔁 Cargando modelo FLAN-T5 base...")
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print("✅ Modelo cargado correctamente.")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api")

# Leer preguntas locales (solo para vista de inicio)
with open("questions/questions.json", "r", encoding="utf-8") as f:
    questions_data = json.load(f)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Debes iniciar sesión para acceder a esta página.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        res = requests.post('http://localhost:5000/api/register', json={
            'username': username,
            'password': password
        })

        if res.status_code == 201:
            flash('✅ Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect(url_for('login'))
        elif res.status_code == 409:
            flash('❌ El usuario ya existe.')
        else:
            flash('❌ Error durante el registro.')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        res = requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password})
        if res.status_code == 200:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            flash(res.json().get("error", "Credenciales incorrectas"))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route("/", endpoint="home")
def home_view():
    return render_template("index.html", questions=questions_data)

@app.route("/study")
@login_required
def study():
    from pymongo import MongoClient

    # Conexión a MongoDB Atlas
    client = MongoClient(f"mongodb+srv://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_CLUSTER')}.yzzh9ig.mongodb.net/?retryWrites=true&w=majority&appName=Final")
    db = client.FIREFIGHTER

    # Acceso a la colección Study
    study_collection = db["Study"]
    boxes = study_collection.find()
    
    result = {}
    for box in boxes:
        box_id = str(box["_id"])
        result[box_id] = {
            "title": box.get("title", ""),
            "description": box.get("description", ""),
            "cards": box.get("cards", []) or []
        }

    return render_template("study.html", leitner=result)


@app.route("/chat")
@login_required
def chat():
    if "history" not in session:
        session["history"] = []
    return render_template("chat.html", history=session["history"])

@app.route("/generate", methods=["POST"])
@login_required
def generate():
    try:
        data = request.get_json()
        user_answer = data.get("user_answer")
        question_text = data.get("question_text")
        correct_option = data.get("correct_option")

        prompt = (
            f"Pregunta: '{question_text}'\n"
            f"Respuesta del usuario: '{user_answer}'\n"
            f"Respuesta correcta: '{correct_option}'\n"
            f"¿Es correcta la respuesta del usuario? Da una explicación breve y razonada."
        )

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=True,
            top_k=50,
            top_p=0.9,
            temperature=0.7
        )

        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return jsonify({"response": decoded})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"response": "❌ Error al generar la respuesta."}), 500

@app.route("/ask", methods=["POST"])
@login_required
def ask():
    try:
        data = request.get_json()
        user_question = data.get("message", "").strip()

        if not user_question or len(user_question) < 3:
            return jsonify({"response": "❌ Pregunta no válida. Intenta con una más clara."})

        prompt = (
            f"Tarea: Responde como experto en bomberos a la siguiente pregunta del temario.\n"
            f"Pregunta: {user_question}\n"
            f"Respuesta:"
        )

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=True,
            top_k=50,
            top_p=0.9,
            temperature=0.7
        )

        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

        session.setdefault("history", [])
        session["history"].append({
            "time": datetime.now().strftime("%H:%M"),
            "user": user_question,
            "bot": decoded
        })
        session.modified = True

        return jsonify({"response": decoded})

    except Exception as e:
        print("❌ ERROR en chatbot:", str(e))
        return jsonify({"response": "❌ Error al responder tu pregunta."}), 500
    
@app.route("/certificacion", methods=["GET", "POST"])
@login_required
def certificacion():
    return render_template("certificacion.html")
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
