from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
# Cache en memoria para Frontend
from simple_memory_cache import memory_cache, cache_result

import requests
import json
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from leitner import get_cards_collection  # reutilizamos conexiÃ³n
import re 
import warnings
import numpy as np
warnings.filterwarnings("ignore", message=".*torch_dtype.*")
warnings.filterwarnings("ignore", message=".*Truncation.*")
warnings.filterwarnings("ignore", message=".*max_new_tokens.*")
from flask_login import logout_user

# --- Carga env ---
load_dotenv()

def _safe_print(*a, **k):
    try:
        print(*a, **k)
    except OSError:
        pass

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FRONTEND_SECRET_KEY", "firefighter-frontend-secret-2024")

# 🔥 CONFIGURACIÓN DE COOKIES ESPECÍFICA PARA FRONTEND
app.config.update(
    SESSION_COOKIE_NAME='firefighter_session',  # Nombre diferente al BackOffice
    SESSION_COOKIE_PATH='/',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,  # True en producción HTTPS
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=86400,  # 24 horas
    SESSION_COOKIE_DOMAIN=None  # Para localhost
)

print(f"🔥 FrontEnd configurado con:")
print(f"   - Session cookie: {app.config['SESSION_COOKIE_NAME']}")
print(f"   - Secret key: {app.secret_key[:20]}...")
print(f"   - Lifetime: {app.config['PERMANENT_SESSION_LIFETIME']}s")

# --- Blueprints ---
try:
    from leitner import leitner_bp
    app.register_blueprint(leitner_bp)
    _safe_print("âœ… Blueprint Leitner registrado")
except Exception as e:
    _safe_print(f"âš ï¸ No se pudo registrar el blueprint Leitner: {e}")

# --- IA: carga perezosa (evita errores raros de stdout) ---
chatbot_pipeline = None
def get_chatbot():
    global chatbot_pipeline
    if chatbot_pipeline is not None:
        return chatbot_pipeline
    try:
        from transformers import pipeline
        import torch
        print("ðŸ” Cargando modelo de IA (DialoGPT-small)...")
        chatbot_pipeline = pipeline(
            "text-generation",
            model="microsoft/DialoGPT-small",
            tokenizer="microsoft/DialoGPT-small",
            device=0 if torch.cuda.is_available() else -1
        )
        print("âœ… Modelo cargado (DialoGPT-small).")
    except Exception as e:
        print(f"âš ï¸ Error con DialoGPT-small: {e}. Probando distilgpt2â€¦")
        try:
            from transformers import pipeline
            chatbot_pipeline = pipeline("text-generation", model="distilgpt2")
            print("âœ… Respaldo cargado (distilgpt2).")
        except Exception as e2:
            print(f"âŒ Sin modelos: {e2}")
            chatbot_pipeline = None
    return chatbot_pipeline

def _ensure_text_index(col):
    # Creamos Ã­ndice de texto una sola vez
    try:
        col.create_index([("front", "text"), ("back", "text")], name="text_search")
    except Exception:
        pass

def find_relevant_cards(query: str, username: str, deck: str = "", limit: int = 6):
    """
    Busca tarjetas relevantes por $text (si hay Ã­ndice) y cae a regex si no.
    """
    col = get_cards_collection()
    if not col:
        return []

    _ensure_text_index(col)

    q_filter = {"user": username}
    if deck:
        q_filter["deck"] = deck.strip().lower()

    # 1) intenta bÃºsqueda texto
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
    Construye un prompt compacto para modelos pequeÃ±os, reforzando el uso del contexto.
    """
    ctx_lines = []
    for i, c in enumerate(cards, 1):
        f = str(c.get("front", "")).strip()
        b = str(c.get("back", "")).strip()
        if f or b:
            ctx_lines.append(f"- {f} â†’ {b}")
    context_block = "\n".join(ctx_lines[:10]) if ctx_lines else "â€” (no se encontraron tarjetas relevantes) â€”"

    policy = (
        "Responde COMO INSTRUCTOR DE BOMBEROS.\n"
        "Usa SOLO el contexto si es suficiente. Si falta info, dilo claramente y sugiere quÃ© repasar.\n"
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
            flash("Debes iniciar sesiÃ³n para acceder a esta pÃ¡gina.")
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
        flash('âŒ El usuario debe tener al menos 3 caracteres.')
        return render_template('register.html')
    if len(password) < 8:
        flash('âŒ La contraseÃ±a debe tener al menos 8 caracteres.')
        return render_template('register.html')

    users = load_users()
    key = username.strip().lower()
    if key in users:
        flash('âŒ El usuario ya existe.')
        return render_template('register.html')

    try:
        users[key] = {
            "password": hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        save_users(users)
        flash('âœ… Registro exitoso (modo local). Ahora puedes iniciar sesiÃ³n.')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'âŒ Error guardando usuario: {str(e)}')
        return render_template('register.html')

def login_local_fallback(username, password):
    """Fallback local para login - CORREGIDO"""
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

    def hash_password(pwd): 
        return hashlib.sha256(pwd.encode()).hexdigest()

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
    session['user_id'] = f"local_{key}"  # ID local
    session['user_role'] = 'user'
    
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
                "response": "Datos vacÃ­os. EnvÃ­a un mensaje.",
                "success": False
            }), 400
        
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({
                "error": "Empty message",
                "response": "Por favor, escribe un mensaje.",
                "success": False
            }), 400
        
        print(f"ðŸ’¬ Chat: '{user_message}'")
        
        # Generar respuesta
        response_text = chat_model.generate_response(user_message)
        print(f"âœ… Respuesta: '{response_text}'")
        
        # Respuesta exitosa
        return jsonify({
            "response": response_text,
            "success": True,
            "user": session.get('user', 'anonymous'),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"âŒ ERROR CRÃTICO en /api/chat/ask: {str(e)}")
        import traceback
        traceback.print_exc()  # Esto mostrarÃ¡ el traceback completo
        
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

@app.route('/logout')
def logout():
    """Cerrar sesión - VERSIÓN CORREGIDA"""
    try:
        # Limpiar la sesión manualmente
        session.pop('user_id', None)
        session.pop('username', None)
        session.pop('access_token', None)
        session.pop('user_data', None)
        
        print("✅ Sesión cerrada correctamente")
        return redirect(url_for('login'))
        
    except Exception as e:
        print(f"⚠️ Error en logout: {e}")
        # Redirigir a login de todas formas
        return redirect(url_for('login'))


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
API_BASE_URL = os.getenv("API_BASE_URL", "http://firefighter_backend:5000/api")

# --- Preguntas para home ---
try:
    with open("data/questions/questions.json", "r", encoding="utf-8") as f:
        questions_data = json.load(f)
except Exception as e:
    _safe_print(f"âš ï¸ Error cargando questions.json: {e}")
    questions_data = {"preguntas": []}

# --- Rutas Auth ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        email = request.form.get('email', '').strip()  # Cambio importante
        access_token = request.form.get('access_token', '').strip()
        
        print(f"🔍 Frontend - Datos del formulario:")
        print(f"   - Username: {username}")
        print(f"   - Email: {email}")
        print(f"   - Token: {access_token}")
        print(f"   - Password length: {len(password)}")
        
        if not access_token:
            flash('❌ Token de acceso requerido para el registro')
            return render_template('register.html')
            
        # Si no se proporciona email, usar uno por defecto basado en username
        if not email:
            email = f"{username}@firefighter.com"
            print(f"🔍 Email automático generado: {email}")
            
        payload = {
            'username': username, 
            'password': password, 
            'email': email,
            'access_token': access_token
        }

        try:
            _safe_print(f"📤 POST {API_BASE_URL}/register")
            res = requests.post(f"{API_BASE_URL}/register", json=payload, timeout=10)
            
            print(f"🔍 Respuesta API - Status: {res.status_code}")
            
            # Manejar respuesta vacía
            if not res.content:
                flash('❌ Error: Respuesta vacía del servidor')
                return render_template('register.html')
                
            data = res.json()
            print(f"🔍 Respuesta API - Data: {data}")
            
            if res.status_code == 201:
                flash('✅ Registro exitoso. Ahora puedes iniciar sesión.')
                return redirect(url_for('login'))
            elif res.status_code == 400:
                error_msg = data.get("detail", "Error durante el registro.")
                flash(f'❌ {error_msg}')
                print(f"❌ Error 400: {error_msg}")
            elif res.status_code == 409:
                flash(f'❌ {data.get("detail", "El usuario ya existe.")}')
            else:
                flash(f'❌ Error {res.status_code}: {data.get("detail", "Error durante el registro.")}')
                
        except requests.exceptions.ConnectionError:
            flash('⚠️ API no disponible. El registro con tokens no está disponible en modo local.')
        except requests.exceptions.Timeout:
            flash('❌ Tiempo de espera agotado. Inténtalo nuevamente.')
        except json.JSONDecodeError:
            flash('❌ Error: Respuesta inválida del servidor')
            print(f"❌ JSON decode error. Response text: {res.text}")
        except Exception as e:
            flash(f'❌ Error inesperado: {str(e)}')
            print(f"❌ Exception: {e}")

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        try:
            _safe_print(f"📤 POST {API_BASE_URL}/login")
            res = requests.post(f"{API_BASE_URL}/auth/login", json={"username": username, "password": password}, timeout=10)

            
            print(f"🔍 Respuesta login - Status: {res.status_code}")
            
            if not res.content:
                flash('❌ Error: Respuesta vacía del servidor')
                return render_template('login.html')
                
            data = res.json()
            print(f"🔍 Respuesta login - Data: {data}")
            
            if res.status_code == 200:
                # CORREGIDO: Manejar correctamente la respuesta
                user_data = data.get('user', {})
                
                session['user'] = user_data.get('username', username)
                session['user_id'] = user_data.get('id', '')  # Usar 'id' en lugar de 'user_id'
                session['user_role'] = user_data.get('role', 'user')
                
                # Guardar token en sesión si está disponible
                if 'access_token' in data:
                    session['access_token'] = data['access_token']
                
                flash('✅ Sesión iniciada correctamente')
                return redirect(url_for('home'))
            else:
                error_msg = data.get("detail", "Credenciales incorrectas")
                flash(f'❌ {error_msg}')
                
        except requests.exceptions.ConnectionError:
            flash('⚠️ API no disponible. Usando autenticación local.')
            return login_local_fallback(username, password)
        except requests.exceptions.Timeout:
            flash('❌ Tiempo de espera agotado. Inténtalo nuevamente.')
        except json.JSONDecodeError:
            flash('❌ Error: Respuesta inválida del servidor')
            print(f"❌ JSON decode error. Response text: {res.text}")
        except Exception as e:
            flash(f'❌ Error de conexión: {str(e)}')
            print(f"❌ Exception en login: {e}")
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
            return jsonify({"response": "âŒ Datos incompletos para la evaluaciÃ³n."})

        prompt = (
            f"Como experto en bomberos, evalÃºa esta respuesta:\n"
            f"Pregunta: {question_text}\n"
            f"Respuesta del usuario: {user_answer}\n"
            f"Respuesta correcta: {correct_option}\n"
            f"Â¿Es correcta? Explica brevemente:"
        )
        pipe = get_chatbot()
        if pipe is None:
            return jsonify({"response": "âœ… Revisa tu respuesta comparando con el material de estudio oficial."})

        result = pipe(prompt, max_length=150, num_return_sequences=1, temperature=0.7, do_sample=True)
        response = result[0]['generated_text'].replace(prompt, '').strip()
        return jsonify({"response": response})
    except Exception:
        return jsonify({"response": "âœ… Revisa tu respuesta con el material de estudio."})

@app.route("/ask", methods=["POST"])
@login_required
def ask():
    try:
        data = request.get_json()
        user_question = data.get("message", "").strip()
        if not user_question or len(user_question) < 3:
            return jsonify({"response": "âŒ Formula una pregunta mÃ¡s clara."})

        prompt = f"Como experto bombero, responde conciso: {user_question}\nRespuesta:"
        pipe = get_chatbot()
        if pipe is None:
            return jsonify({"response": "âš ï¸ IA no disponible. Consulta el manual."})

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
        return jsonify({"response": "âš ï¸ Error al procesar tu pregunta."})

@app.route("/clear-chat", methods=["POST"])
@login_required
def clear_chat():
    session["chat_history"] = []
    session.modified = True
    return jsonify({"success": True, "message": "Chat limpiado"})

@app.route("/certificaciones", methods=["GET"])
@login_required
def certificaciones():
    """PÃ¡gina de certificaciones con mÃºltiples opciones de carga"""
    
    # URLs especÃ­ficas que quieres embeber
    urls = {
        'main': '/onfire-academy/',  # https://www.onfireacademy.es/
        'header': '/onfire-academy/index.html#header13-2w',  # Con fragmento especÃ­fico
        'examinadores': '/onfire-academy/examinadores.html',  # PÃ¡gina de examinadores
        'formacion': '/formacion-certificada/',  # https://www.formacioncertificadoprofesional.com/
        'direct_main': 'https://www.onfireacademy.es/',
        'direct_header': 'https://www.onfireacademy.es/index.html#header13-2w',
        'direct_examinadores': 'https://www.onfireacademy.es/examinadores.html',
        'direct_formacion': 'https://www.formacioncertificadoprofesional.com/'
    }
    
    # Detectar modo y URL especÃ­fica
    mode = request.args.get('mode', 'main')
    proxy_type = request.args.get('proxy', 'internal')
    
    if proxy_type == 'direct':
        proxied_url = urls.get(f'direct_{mode}', urls['direct_main'])
    else:
        proxied_url = urls.get(mode, urls['main'])
    
    return render_template("certificaciones.html", 
                         proxied_url=proxied_url,
                         proxy_mode=proxy_type,
                         current_mode=mode,
                         available_urls=urls)


# PROXY PRINCIPAL - ONFIREACADEMY.ES (mejorado)
@app.route("/onfire-academy/")
@app.route("/onfire-academy/<path:subpath>")
@login_required  
def proxy_onfire(subpath=""):
    """Proxy avanzado para www.onfireacademy.es"""
    return _enhanced_proxy("https://www.onfireacademy.es", subpath)


# PROXY PARA FORMACIONCERTIFICADOPROFESIONAL.COM
@app.route("/formacion-certificada/")
@app.route("/formacion-certificada/<path:subpath>")
@login_required  
def proxy_formacion(subpath=""):
    """Proxy avanzado para www.formacioncertificadoprofesional.com"""
    return _enhanced_proxy("https://www.formacioncertificadoprofesional.com", subpath)


# FUNCIÃ“N CENTRALIZADA DE PROXY (DRY principle)
def _enhanced_proxy(base_url, subpath=""):
    """FunciÃ³n centralizada para proxy con bypass completo"""
    import requests
    import re
    from urllib.parse import urlparse
    
    try:
        # Construir URL objetivo
        if subpath:
            target_url = f"{base_url}/{subpath}"
        else:
            target_url = base_url + "/"
        
        domain = urlparse(base_url).netloc
        print(f"ðŸ”— Proxy request: {target_url} (domain: {domain})")
        
        # Headers realistas
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': base_url
        }
        
        response = requests.get(target_url, headers=headers, timeout=20, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.text
            content_type = response.headers.get('content-type', 'text/html')
            
            if 'text/html' in content_type:
                # Determinar proxy path basado en el dominio
                if 'onfireacademy' in domain:
                    proxy_path = '/onfire-academy/'
                elif 'formacioncertificado' in domain:
                    proxy_path = '/formacion-certificada/'
                else:
                    proxy_path = '/proxy-generic/'
                
                content = _process_html_content(content, base_url, domain, proxy_path)
            
            # Crear respuesta
            resp = make_response(content)
            resp.headers['Content-Type'] = content_type
            
            # Eliminar headers restrictivos
            headers_to_remove = [
                'X-Frame-Options', 'Content-Security-Policy', 'X-Content-Type-Options',
                'X-XSS-Protection', 'Strict-Transport-Security', 'X-Frame-Options'
            ]
            
            for header in headers_to_remove:
                resp.headers.pop(header, None)
            
            # Headers permisivos
            resp.headers['X-Frame-Options'] = 'ALLOWALL'
            resp.headers['Content-Security-Policy'] = "frame-ancestors *; default-src * 'unsafe-inline' 'unsafe-eval' data: blob:"
            resp.headers['X-Content-Type-Options'] = 'nosniff'
            
            print(f"âœ… Proxy success: {domain} - {response.status_code} - {len(content)} chars")
            return resp
        else:
            print(f"âŒ Proxy failed: {response.status_code}")
            return redirect(target_url, code=302)
            
    except requests.exceptions.Timeout:
        print(f"âš ï¸ Proxy timeout: {domain}")
        return redirect(base_url, code=302)
    except Exception as e:
        print(f"âš ï¸ Proxy error: {domain} - {e}")
        return redirect(base_url, code=302)


# VERSIÃ“N FINAL CORREGIDA - FILTRA CORRECTAMENTE


def _process_html_content(content, base_url, domain, proxy_path):
    """Procesa HTML para assets - VERSIÃ“N LIMPIA Y FINAL"""
    import re
    
    print(f"ðŸ”§ Processing HTML for {domain} with proxy_path: {proxy_path}")
    
    # PASO 1: Eliminar meta tags restrictivos
    patterns_to_remove = [
        r'<meta[^>]*http-equiv=["\']?X-Frame-Options["\']?[^>]*>',
        r'<meta[^>]*name=["\']?X-Frame-Options["\']?[^>]*>',
        r'<meta[^>]*http-equiv=["\']?Content-Security-Policy["\']?[^>]*>',
        r'<meta[^>]*name=["\']?Content-Security-Policy["\']?[^>]*>'
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # PASO 2: Reemplazar referencias restrictivas
    replacements = {
        'X-Frame-Options': 'X-Frame-Options-Disabled',
        'frame-ancestors': 'frame-ancestors-disabled',
        "frame-ancestors 'none'": "frame-ancestors *",
        "frame-ancestors 'self'": "frame-ancestors *",
        'SAMEORIGIN': 'ALLOWALL',
        'DENY': 'ALLOWALL'
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # PASO 3: Procesamiento de assets
    replacements_made = 0
    
    # Helper function para verificar si es un asset vÃ¡lido
    def is_valid_asset(url):
        if not url:
            return False
        if proxy_path.rstrip('/') in url:
            return False
        if any(url.startswith(prefix) for prefix in ['http:', 'https:', 'data:', 'mailto:', 'tel:', 'javascript:', '//']):
            return False
        if url.startswith(('#', '?')):
            return False
        return True
    
    # CSS Links
    def replace_css(match):
        nonlocal replacements_made
        original = match.group(1)
        
        if not is_valid_asset(original):
            return match.group(0)
            
        if not original.endswith('.css') and '.css?' not in original:
            return match.group(0)
        
        if original.startswith('/'):
            new_path = proxy_path + original[1:]
        else:
            new_path = proxy_path + original
            
        print(f"ðŸŽ¨ CSS: {original} â†’ {new_path}")
        replacements_made += 1
        return f'href="{new_path}"'
    
    content = re.sub(r'href="([^"]*\.css[^"]*)"', replace_css, content)
    content = re.sub(r"href='([^']*\.css[^']*)'", replace_css, content)
    
    # JavaScript
    def replace_js(match):
        nonlocal replacements_made
        original = match.group(1)
        
        if not is_valid_asset(original):
            return match.group(0)
            
        if not original.endswith('.js') and '.js?' not in original:
            return match.group(0)
        
        if original.startswith('/'):
            new_path = proxy_path + original[1:]
        else:
            new_path = proxy_path + original
            
        print(f"ðŸ“œ JS: {original} â†’ {new_path}")
        replacements_made += 1
        return f'src="{new_path}"'
    
    content = re.sub(r'src="([^"]*\.js[^"]*)"', replace_js, content)
    content = re.sub(r"src='([^']*\.js[^']*)'", replace_js, content)
    
    # Images
    def replace_img(match):
        nonlocal replacements_made
        original = match.group(1)
        
        if not is_valid_asset(original):
            return match.group(0)
        
        if original.startswith('/'):
            new_path = proxy_path + original[1:]
        else:
            new_path = proxy_path + original
            
        print(f"ðŸ–¼ï¸ IMG: {original} â†’ {new_path}")
        replacements_made += 1
        return f'src="{new_path}"'
    
    content = re.sub(r'src="([^"]*\.(png|jpg|jpeg|gif|webp|svg|ico)[^"]*)"', replace_img, content)
    content = re.sub(r"src='([^']*\.(png|jpg|jpeg|gif|webp|svg|ico)[^']*)'", replace_img, content)
    
    # PASO 4: URLs absolutas del dominio
    domain_pattern = f'https?://{re.escape(domain)}/'
    content = re.sub(domain_pattern, proxy_path, content)
    
    print(f"âœ… Made {replacements_made} path replacements")
    
    # PASO 5: JavaScript bypass
    bypass_js = f'''
    <script>
    console.log('ðŸ”¥ FirefighterAI Proxy v7.0 - Clean Processing');
    
    // Frame busting protection
    if (window.top !== window.self) {{
        window.top = window.self;
        window.parent = window.self;
        
        // Disable problematic methods
        window.location.replace = function() {{ console.log('ðŸ”¥ Blocked location.replace'); }};
        window.location.assign = function() {{ console.log('ðŸ”¥ Blocked location.assign'); }};
    }}
    
    // Remove any remaining restrictive meta tags
    document.addEventListener('DOMContentLoaded', function() {{
        const restrictiveMetas = document.querySelectorAll(
            'meta[http-equiv*="X-Frame"], meta[name*="X-Frame"], ' +
            'meta[http-equiv*="Content-Security-Policy"], meta[name*="Content-Security-Policy"]'
        );
        restrictiveMetas.forEach(meta => {{
            console.log('ðŸ”¥ Removing:', meta.outerHTML);
            meta.remove();
        }});
    }});
    </script>
    '''
    
    # Inyectar JavaScript
    if '</head>' in content:
        content = content.replace('</head>', f'{bypass_js}</head>')
    else:
        content = bypass_js + content
    
    return content


@app.route("/certificaciones/selector")
@login_required
def certificaciones_selector():
    """PÃ¡gina de selecciÃ³n de sitios de certificaciÃ³n"""
    sites = {
        'onfireacademy_main': {
            'name': 'OnFire Academy - Principal',
            'url': '/certificaciones?mode=main',
            'description': 'Plataforma principal de formaciÃ³n'
        },
        'onfireacademy_header': {
            'name': 'OnFire Academy - SecciÃ³n Header',
            'url': '/certificaciones?mode=header',
            'description': 'Acceso directo a secciÃ³n especÃ­fica'
        },
        'onfireacademy_examinadores': {
            'name': 'OnFire Academy - Examinadores',
            'url': '/certificaciones?mode=examinadores',
            'description': 'InformaciÃ³n sobre examinadores'
        },
        'formacion_profesional': {
            'name': 'FormaciÃ³n Certificado Profesional',
            'url': '/certificaciones?mode=formacion',
            'description': 'Certificaciones profesionales oficiales'
        }
    }
    
    return render_template("certificaciones_selector.html", sites=sites)


@app.route("/debug-html")
@login_required
def debug_html():
    """Ver el HTML procesado del proxy"""
    try:
        import requests
        
        # Obtener HTML original
        response = requests.get("https://www.onfireacademy.es/", timeout=15)
        original_html = response.text
        
        # Procesarlo con tu funciÃ³n
        processed_html = _process_html_content(
            original_html, 
            "https://www.onfireacademy.es", 
            "www.onfireacademy.es", 
            "/onfire-academy/"
        )
        
        # Mostrar comparaciÃ³n
        debug_output = f"""
        <h1>ðŸ”§ Debug HTML Processing</h1>
        
        <h2>ðŸ“„ Original HTML (primeras 500 chars):</h2>
        <pre style="background:#f0f0f0;padding:10px;overflow:auto;max-height:200px;">
{original_html[:500]}...
        </pre>
        
        <h2>ðŸ”§ Processed HTML (primeras 500 chars):</h2>
        <pre style="background:#e0f0e0;padding:10px;overflow:auto;max-height:200px;">
{processed_html[:500]}...
        </pre>
        
        <h2>ðŸ”— Link tags encontrados en HTML original:</h2>
        """
        
        import re
        links = re.findall(r'<link[^>]*href=["\']([^"\']*)["\'][^>]*>', original_html)
        scripts = re.findall(r'<script[^>]*src=["\']([^"\']*)["\'][^>]*>', original_html)
        
        debug_output += "<ul>"
        for link in links[:10]:  # Primeros 10
            debug_output += f"<li>ðŸ“„ {link}</li>"
        debug_output += "</ul>"
        
        debug_output += "<h2>ðŸ”— Script tags encontrados:</h2><ul>"
        for script in scripts[:10]:  # Primeros 10
            debug_output += f"<li>ðŸ“„ {script}</li>"
        debug_output += "</ul>"
        
        return debug_output
        
    except Exception as e:
        return f"<h1>Error:</h1><p>{str(e)}</p>"


# ASSETS PROXY MEJORADO
@app.route("/onfire-academy-assets/<path:subpath>")
@app.route("/formacion-assets/<path:subpath>")
@login_required
def proxy_assets(subpath):
    """Proxy mejorado para assets"""
    import requests
    
    # Determinar origen basado en la ruta
    if request.path.startswith('/onfire-academy-assets/'):
        base_url = "https://www.onfireacademy.es"
    else:
        base_url = "https://www.formacioncertificadoprofesional.com"
    
    try:
        target_url = f"{base_url}/{subpath}"
        print(f"ðŸ”— Asset request: {target_url}")  # Debug
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'{base_url}/',
            'Accept': '*/*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        }
        
        response = requests.get(target_url, headers=headers, timeout=10)
        print(f"ðŸ“„ Asset response: {response.status_code}")  # Debug
        
        if response.status_code == 200:
            resp = make_response(response.content)
            if 'content-type' in response.headers:
                resp.headers['Content-Type'] = response.headers['content-type']
            
            # CORS headers para evitar bloqueos
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = '*'
            
            return resp
        else:
            print(f"âŒ Asset not found: {response.status_code}")
            return "Asset not found", 404
    except Exception as e:
        print(f"âš ï¸ Asset error: {e}")
        return "Asset error", 500


if __name__ == "__main__":
    _safe_print("ðŸš€ Frontend iniciando...")
    _safe_print(f"ðŸ”— API configurada en: {API_BASE_URL}")
    try:
        _safe_print("ðŸ”„ Verificando conexiÃ³n con API...")
        r = requests.get(f"{API_BASE_URL.replace('/api', '/api/health')}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            _safe_print("âœ… API disponible")
            _safe_print(f"ðŸ“Š Usuarios en BD: {data.get('users_count', 'N/A')}")
        else:
            _safe_print("âš ï¸ API responde pero con errores")
    except Exception as e:
        _safe_print(f"âš ï¸ API no disponible: {e}")
        _safe_print("ðŸ”„ Funcionando en modo fallback (local)")
    _safe_print("ðŸŒ Frontend corriendo en http://localhost:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
