from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import json
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from leitner import get_cards_collection  # reutilizamos conexión
import re 
import warnings
import numpy as np
warnings.filterwarnings("ignore", message=".*torch_dtype.*")
warnings.filterwarnings("ignore", message=".*Truncation.*")
warnings.filterwarnings("ignore", message=".*max_new_tokens.*")

# --- Carga env ---
load_dotenv()

def _safe_print(*a, **k):
    try:
        print(*a, **k)
    except OSError:
        pass

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "sargento-secret-key")

# --- Blueprints ---
try:
    from leitner import leitner_bp
    app.register_blueprint(leitner_bp)
    _safe_print("✅ Blueprint Leitner registrado")
except Exception as e:
    _safe_print(f"⚠️ No se pudo registrar el blueprint Leitner: {e}")

# --- IA: carga perezosa (evita errores raros de stdout) ---
chatbot_pipeline = None
def get_chatbot():
    global chatbot_pipeline
    if chatbot_pipeline is not None:
        return chatbot_pipeline
    try:
        from transformers import pipeline
        import torch
        print("🔁 Cargando modelo de IA (DialoGPT-small)...")
        chatbot_pipeline = pipeline(
            "text-generation",
            model="microsoft/DialoGPT-small",
            tokenizer="microsoft/DialoGPT-small",
            device=0 if torch.cuda.is_available() else -1
        )
        print("✅ Modelo cargado (DialoGPT-small).")
    except Exception as e:
        print(f"⚠️ Error con DialoGPT-small: {e}. Probando distilgpt2…")
        try:
            from transformers import pipeline
            chatbot_pipeline = pipeline("text-generation", model="distilgpt2")
            print("✅ Respaldo cargado (distilgpt2).")
        except Exception as e2:
            print(f"❌ Sin modelos: {e2}")
            chatbot_pipeline = None
    return chatbot_pipeline

def _ensure_text_index(col):
    # Creamos índice de texto una sola vez
    try:
        col.create_index([("front", "text"), ("back", "text")], name="text_search")
    except Exception:
        pass

def find_relevant_cards(query: str, username: str, deck: str = "", limit: int = 6):
    """
    Busca tarjetas relevantes por $text (si hay índice) y cae a regex si no.
    """
    col = get_cards_collection()
    if not col:
        return []

    _ensure_text_index(col)

    q_filter = {"user": username}
    if deck:
        q_filter["deck"] = deck.strip().lower()

    # 1) intenta búsqueda texto
    try:
        cursor = col.find(
            {**q_filter, "$text": {"$search": query}},
            {"front": 1, "back": 1, "box": 1, "deck": 1, "score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        docs = list(cursor)
        if docs:
            return docs
    except Exception:
        pass

    # 2) fallback simple por regex
    try:
        rx = re.compile(re.escape(query), re.IGNORECASE)
        cursor = col.find(
            {
                **q_filter,
                "$or": [{"front": rx}, {"back": rx}]
            },
            {"front": 1, "back": 1, "box": 1, "deck": 1}
        ).limit(limit)
        return list(cursor)
    except Exception:
        return []

def build_prompt(user_question: str, cards: list, strict: bool) -> str:
    """
    Construye un prompt compacto para modelos pequeños, reforzando el uso del contexto.
    """
    ctx_lines = []
    for i, c in enumerate(cards, 1):
        f = str(c.get("front", "")).strip()
        b = str(c.get("back", "")).strip()
        if f or b:
            ctx_lines.append(f"- {f} → {b}")
    context_block = "\n".join(ctx_lines[:10]) if ctx_lines else "— (no se encontraron tarjetas relevantes) —"

    policy = (
        "Responde COMO INSTRUCTOR DE BOMBEROS.\n"
        "Usa SOLO el contexto si es suficiente. Si falta info, dilo claramente y sugiere qué repasar.\n"
    )
    if strict:
        policy += "MODO ESTRICTO ACTIVADO: NO inventes nada fuera del contexto.\n"

    prompt = (
        f"{policy}\n"
        f"Contexto (tarjetas Leitner):\n{context_block}\n\n"
        f"Pregunta del alumno: {user_question}\n"
        f"Respuesta clara y breve:"
    )
    return prompt



# --- Auth helpers ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Debes iniciar sesión para acceder a esta página.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Fallbacks locales (si la API no responde) ---
def register_local_fallback(username, password, email):
    import hashlib
    USERS_FILE = 'users_local.json'

    def load_users():
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_users(users):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

    def hash_password(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

    if len(username.strip()) < 3:
        flash('❌ El usuario debe tener al menos 3 caracteres.')
        return render_template('register.html')
    if len(password) < 8:
        flash('❌ La contraseña debe tener al menos 8 caracteres.')
        return render_template('register.html')

    users = load_users()
    key = username.strip().lower()
    if key in users:
        flash('❌ El usuario ya existe.')
        return render_template('register.html')

    try:
        users[key] = {
            "password": hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        save_users(users)
        flash('✅ Registro exitoso (modo local). Ahora puedes iniciar sesión.')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'❌ Error guardando usuario: {str(e)}')
        return render_template('register.html')

def login_local_fallback(username, password):
    import hashlib
    USERS_FILE = 'users_local.json'

    def load_users():
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def hash_password(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

    users = load_users()
    key = username.strip().lower()
    if key not in users:
        flash("❌ Credenciales incorrectas")
        return render_template('login.html')

    data = users[key]
    if not data.get('active', True):
        flash("❌ Usuario desactivado")
        return render_template('login.html')
    if data['password'] != hash_password(password):
        flash("❌ Credenciales incorrectas")
        return render_template('login.html')

    session['user'] = key
    flash('✅ Sesión iniciada (modo local)')
    return redirect(url_for('home'))

from chat_model import chat_model

@app.route('/api/chat/ask', methods=['POST'])
def chat_ask():
    """Endpoint robusto para chat de bomberos"""
    try:
        # Verificar contenido JSON
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "response": "Error de formato. Usa JSON.",
                "success": False
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Empty JSON data",
                "response": "Datos vacíos. Envía un mensaje.",
                "success": False
            }), 400
        
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({
                "error": "Empty message",
                "response": "Por favor, escribe un mensaje.",
                "success": False
            }), 400
        
        print(f"💬 Chat: '{user_message}'")
        
        # Generar respuesta
        response_text = chat_model.generate_response(user_message)
        print(f"✅ Respuesta: '{response_text}'")
        
        # Respuesta exitosa
        return jsonify({
            "response": response_text,
            "success": True,
            "user": session.get('user', 'anonymous'),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO en /api/chat/ask: {str(e)}")
        import traceback
        traceback.print_exc()  # Esto mostrará el traceback completo
        
        return jsonify({
            "error": str(e),
            "response": f"Error en el servidor: {str(e)}",
            "success": False
        }), 500
    
@app.route('/api/chat/status', methods=['GET'])
def chat_status():
    return jsonify({
        "status": "active",
        "model": "local_bert",
        "knowledge_topics": len(chat_model.knowledge_base),
        "has_generator": chat_model.generator is not None,
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    })

@app.route("/api/chat/clear", methods=["POST"])
@login_required
def api_chat_clear():
    session["chat_history"] = []
    session.modified = True
    return jsonify({"ok": True})

# Endpoint sencillo para poblar el selector de barajas
@app.route("/api/leitner/decks", methods=["GET"])
@login_required
def api_leitner_decks():
    col = get_cards_collection()
    username = session.get("user")
    decks = []
    try:
        if col:
            decks = sorted({(doc.get("deck") or "general") for doc in col.find({"user": username}, {"deck": 1})})
        return jsonify({"ok": True, "decks": list(decks)})
    except Exception:
        return jsonify({"ok": True, "decks": []})

# --- API externa (tu backend auth) ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api")

# --- Preguntas para home ---
try:
    with open("data/questions/questions.json", "r", encoding="utf-8") as f:
        questions_data = json.load(f)
except Exception as e:
    _safe_print(f"⚠️ Error cargando questions.json: {e}")
    questions_data = {"preguntas": []}

# --- Rutas Auth ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        email = request.form.get('email', f"{username}@firefighter.com")
        payload = {'username': username, 'password': password, 'email': email}

        try:
            _safe_print(f"🔗 POST {API_BASE_URL}/register")
            res = requests.post(f"{API_BASE_URL}/register", json=payload, timeout=10)
            data = res.json() if res.content else {}
            if res.status_code == 201:
                flash('✅ Registro exitoso. Ahora puedes iniciar sesión.')
                return redirect(url_for('login'))
            elif res.status_code == 409:
                flash(f'❌ {data.get("detail", "El usuario ya existe.")}')
            else:
                flash(f'❌ {data.get("detail", "Error durante el registro.")}')
        except requests.exceptions.ConnectionError:
            flash('⚠️ API no disponible. Usando registro local.')
            return register_local_fallback(username, password, email)
        except requests.exceptions.Timeout:
            flash('❌ Tiempo de espera agotado. Inténtalo nuevamente.')
        except Exception as e:
            flash(f'❌ Error inesperado: {str(e)}')
            return register_local_fallback(username, password, email)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        try:
            _safe_print(f"🔗 POST {API_BASE_URL}/login")
            res = requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password}, timeout=10)
            data = res.json() if res.content else {}
            if res.status_code == 200:
                session['user'] = data['user']['username']
                session['user_id'] = data['user']['id']
                session['user_role'] = data['user'].get('role', 'user')
                flash('✅ Sesión iniciada correctamente')
                return redirect(url_for('home'))
            else:
                flash(data.get("detail", "Credenciales incorrectas"))
        except requests.exceptions.ConnectionError:
            flash('⚠️ API no disponible. Usando autenticación local.')
            return login_local_fallback(username, password)
        except requests.exceptions.Timeout:
            flash('❌ Tiempo de espera agotado. Inténtalo nuevamente.')
        except Exception as e:
            flash(f'❌ Error de conexión: {str(e)}')
            return login_local_fallback(username, password)

    return render_template('login.html')


# --- Rutas generales ---
@app.route("/", endpoint="home")
def home_view():
    return render_template("index.html", questions=questions_data)

@app.route("/chat")
@login_required
def chat():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template("chat.html", history=session["chat_history"])

@app.route("/generate", methods=["POST"])
@login_required
def generate():
    try:
        data = request.get_json()
        user_answer = data.get("user_answer", "")
        question_text = data.get("question_text", "")
        correct_option = data.get("correct_option", "")
        if not all([user_answer, question_text, correct_option]):
            return jsonify({"response": "❌ Datos incompletos para la evaluación."})

        prompt = (
            f"Como experto en bomberos, evalúa esta respuesta:\n"
            f"Pregunta: {question_text}\n"
            f"Respuesta del usuario: {user_answer}\n"
            f"Respuesta correcta: {correct_option}\n"
            f"¿Es correcta? Explica brevemente:"
        )
        pipe = get_chatbot()
        if pipe is None:
            return jsonify({"response": "✅ Revisa tu respuesta comparando con el material de estudio oficial."})

        result = pipe(prompt, max_length=150, num_return_sequences=1, temperature=0.7, do_sample=True)
        response = result[0]['generated_text'].replace(prompt, '').strip()
        return jsonify({"response": response})
    except Exception:
        return jsonify({"response": "✅ Revisa tu respuesta con el material de estudio."})

@app.route("/ask", methods=["POST"])
@login_required
def ask():
    try:
        data = request.get_json()
        user_question = data.get("message", "").strip()
        if not user_question or len(user_question) < 3:
            return jsonify({"response": "❌ Formula una pregunta más clara."})

        prompt = f"Como experto bombero, responde conciso: {user_question}\nRespuesta:"
        pipe = get_chatbot()
        if pipe is None:
            return jsonify({"response": "⚠️ IA no disponible. Consulta el manual."})

        result = pipe(prompt, max_length=200, num_return_sequences=1, temperature=0.7, do_sample=True)
        response = result[0]['generated_text'].replace(prompt, '').strip()
        if len(response) > 300:
            response = response[:300] + "..."
        if len(response) < 10:
            response = "No pude generar una respuesta adecuada. Reformula tu pregunta."
        session.setdefault("chat_history", [])
        session["chat_history"].append({
            "time": datetime.now().strftime("%H:%M"),
            "user": user_question,
            "bot": response
        })
        if len(session["chat_history"]) > 20:
            session["chat_history"] = session["chat_history"][-10:]
        session.modified = True
        return jsonify({"response": response})
    except Exception:
        return jsonify({"response": "⚠️ Error al procesar tu pregunta."})

@app.route("/clear-chat", methods=["POST"])
@login_required
def clear_chat():
    session["chat_history"] = []
    session.modified = True
    return jsonify({"success": True, "message": "Chat limpiado"})

@app.route("/certificaciones", methods=["GET", "POST"])
@login_required
def certificacion():
    return render_template("certificaciones.html")

# --- Estado de la API Auth ---
@app.route("/api-status")
def api_status():
    try:
        res = requests.get(f"{API_BASE_URL.replace('/api', '/api/health')}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return jsonify({"api_available": True, "api_status": data, "fallback_mode": False})
        return jsonify({"api_available": False, "fallback_mode": True, "error": "API no responde"})
    except Exception as e:
        return jsonify({"api_available": False, "fallback_mode": True, "error": str(e)})
    
@app.route('/logout')
def logout():
    """Cierra la sesión y limpia todas las cookies"""
    # Limpiar la sesión
    session.clear()
    
    # Crear respuesta de redirección
    response = redirect(url_for('login'))
    
    # Limpiar todas las cookies relacionadas con la sesión
    response.delete_cookie('session')
    response.delete_cookie('user')
    response.delete_cookie('username')
    response.delete_cookie('remember_token')
    
    # Opcional: limpiar otras cookies que puedas tener
    response.delete_cookie('preferences')
    response.delete_cookie('theme')
    
    flash('Sesión cerrada correctamente', 'success')
    return response

if __name__ == "__main__":
    _safe_print("🚀 Frontend iniciando...")
    _safe_print(f"🔗 API configurada en: {API_BASE_URL}")
    try:
        _safe_print("🔄 Verificando conexión con API...")
        r = requests.get(f"{API_BASE_URL.replace('/api', '/api/health')}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            _safe_print("✅ API disponible")
            _safe_print(f"📊 Usuarios en BD: {data.get('users_count', 'N/A')}")
        else:
            _safe_print("⚠️ API responde pero con errores")
    except Exception as e:
        _safe_print(f"⚠️ API no disponible: {e}")
        _safe_print("🔄 Funcionando en modo fallback (local)")
    _safe_print("🌐 Frontend corriendo en http://localhost:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
