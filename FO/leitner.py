# leitner.py
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

leitner_bp = Blueprint("leitner", __name__)

# ========= Config & helpers =========
DEFAULT_INTERVALS_DAYS = [0, 1, 3, 7, 14, 30]  # Cajas 1..6
BOX_LABELS = {
    1: ("Caja 1", "Repaso hoy / recién falladas"),
    2: ("Caja 2", "Repaso en 1 día"),
    3: ("Caja 3", "Repaso cada 3 días"),
    4: ("Caja 4", "Repaso semanal"),
    5: ("Caja 5", "Repaso quincenal"),
    6: ("Caja 6", "Repaso mensual"),
}
# Para la plantilla: {box: {days:int, label:str}}
INTERVALS_MAP = {
    i + 1: {"days": d, "label": ("hoy" if d == 0 else "1 día" if d == 1 else f"{d} días")}
    for i, d in enumerate(DEFAULT_INTERVALS_DAYS)
}

def _safe_print(*a, **k):
    try:
        print(*a, **k)
    except OSError:
        pass

def login_required_bp(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Debes iniciar sesión para acceder a esta página.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def _now_utc():
    return datetime.now(timezone.utc)

def _due_for_box(box: int) -> datetime:
    days = DEFAULT_INTERVALS_DAYS[max(0, min(box - 1, len(DEFAULT_INTERVALS_DAYS) - 1))]
    return _now_utc() + timedelta(days=days)

def _empty_board():
    board = {}
    for b in range(1, 7):
        title, desc = BOX_LABELS[b]
        board[b] = {"title": f"{title} • {DEFAULT_INTERVALS_DAYS[b-1]}d", "description": desc, "cards": []}
    return board

# ========= Mongo (perezoso + tolerante) =========
_client = None
_db = None
_cards = None

def _build_mongo_uri():
    # USAR ESTAS CREDENCIALES DIRECTAMENTE (igual que la API)
    user = "joso"
    pwd = "XyGItdDKpWkfJfjT"
    cluster = "cluster0.yzzh9ig.mongodb.net"
    if user and pwd:
        return f"mongodb+srv://{user}:{pwd}@{cluster}/?retryWrites=true&w=majority&appName=Firefighter"
    return os.getenv("MONGO_URI", "mongodb://localhost:27017")

def get_cards_collection():
    """Devuelve la colección de cartas o None si no hay DB disponible (no revienta la app)."""
    global _client, _db, _cards
    if _cards is not None:
        return _cards
    try:
        uri = _build_mongo_uri()
        _client = MongoClient(uri, serverSelectionTimeoutMS=6000, connectTimeoutMS=6000)
        _client.server_info()  # smoke test
        db_name = os.getenv("DB_NAME", "FIREFIGHTER")
        _db = _client[db_name]
        _cards = _db["leitner_cards"]

        # Índices idempotentes
        _cards.create_index([("user", ASCENDING), ("deck", ASCENDING), ("front", ASCENDING)], unique=True)
        _cards.create_index([("user", ASCENDING), ("due", ASCENDING), ("box", ASCENDING)])
        _cards.create_index([("box", ASCENDING)])
        _safe_print("✅ Conectado a MongoDB para Leitner")
        return _cards
    except Exception as e:
        _safe_print(f"⚠️ Leitner en modo sin DB (fallback): {e}")
        return None

# ========= Fallback en memoria (si no hay Mongo) =========
_memory_store = {}  # username -> list[card dict]

def _mem_user_list(username):
    return _memory_store.setdefault(username, [])

# ========= Vistas HTML =========
@leitner_bp.route("/study")
@login_required_bp
def study_view():
    """
    Render inicial: muestra contadores por caja ya calculados en servidor
    y pasa intervals amigables para la UI.
    """
    username = session.get("user")
    cards_col = get_cards_collection()
    board = _empty_board()
    now = _now_utc()

    # Estructuras para la plantilla
    box_counts = {}  # {box: {'total': n, 'due': m}}
    due_total = 0

    if cards_col is None:
        # Fallback memoria
        for c in _mem_user_list(username):
            b = int(c.get("box", 1))
            board[b]["cards"].append(c.get("front") or c.get("question") or "")
            box_counts.setdefault(b, {"total": 0, "due": 0})
            box_counts[b]["total"] += 1
            if c.get("due", now) <= now:
                box_counts[b]["due"] += 1
                due_total += 1
        return render_template(
            "study.html",
            leitner=board,
            max_box=6,
            intervals=INTERVALS_MAP,
            box_counts=box_counts,
            due_total=due_total
        )

    # Con DB: usar agregación para contadores
    try:
        pipeline = [
            {"$match": {"user": username}},
            {"$group": {
                "_id": "$box",
                "total": {"$sum": 1},
                "due": {"$sum": {"$cond": [{"$lte": ["$due", now]}, 1, 0]}}
            }},
        ]
        for row in cards_col.aggregate(pipeline):
            b = int(row["_id"] or 1)
            box_counts[b] = {"total": int(row.get("total", 0)), "due": int(row.get("due", 0))}
            due_total += box_counts[b]["due"]

        # (Opcional) Cargar algunos fronts para dar sensación de contenido en tarjetas
        for doc in cards_col.find({"user": username}, {"front": 1, "box": 1}).limit(60):
            b = int(doc.get("box", 1))
            if b not in board:
                b = 1
            board[b]["cards"].append(doc.get("front", ""))

    except PyMongoError as e:
        _safe_print("⚠️ Error leyendo contadores Leitner:", e)

    return render_template(
        "study.html",
        leitner=board,
        max_box=6,
        intervals=INTERVALS_MAP,
        box_counts=box_counts,
        due_total=due_total
    )

# ========= API JSON =========
def _normalize_card_out(doc):
    """Convierte un documento DB a la forma que espera el front (question/answer)."""
    return {
        "id": str(doc.get("_id") or doc.get("id")),
        "question": doc.get("front") or "",  # Cambiado de doc.get("question")
        "answer": doc.get("back") or "",     # Cambiado de doc.get("answer")
        "box": int(doc.get("box", 1)),
        "deck": doc.get("deck", "general"),
    }

def _ensure_user_has_cards(username, cards_col):
    """Si el usuario no tiene tarjetas, sembrar automáticamente tarjetas de demo"""
    try:
        count = cards_col.count_documents({"user": username})
        if count == 0:
            print(f"🔍 Usuario '{username}' no tiene tarjetas, sembrando demo...")
            demo_cards = [
                {"front": "Presión mínima en línea de ataque", "back": "3-5 bar según manguera/boquilla"},
                {"front": "Código MAYDAY", "back": "MAYDAY MAYDAY MAYDAY + LUNAR"},
                {"front": "Triángulo del fuego", "back": "Combustible + Oxígeno + Calor"},
                {"front": "Ventilación táctica", "back": "Control de flujos, evitar flashover, coordinación con ataque"},
            ]
            
            now = _now_utc()
            inserted = 0
            for card in demo_cards:
                try:
                    cards_col.insert_one({
                        "user": username,
                        "deck": "general",
                        "front": card["front"],
                        "back": card["back"],
                        "box": 1,
                        "due": _due_for_box(1),
                        "created_at": now,
                        "history": []
                    })
                    inserted += 1
                except Exception as e:
                    # Ignorar errores de duplicados
                    if "duplicate" not in str(e).lower():
                        print(f"⚠️ Error sembrando carta: {e}")
            
            print(f"✅ Sembradas {inserted} tarjetas de demo para '{username}'")
            return True
    except Exception as e:
        print(f"⚠️ Error verificando/sembrando tarjetas: {e}")
    return False

@leitner_bp.route("/api/leitner/next", methods=["GET"])
def api_next_card():
    """
    Devuelve la siguiente tarjeta vencida priorizando la caja más baja y 'due' más antiguo.
    """
    username = session.get("user")
    deck = (request.args.get("deck") or "").strip().lower()
    now = _now_utc()
    cards_col = get_cards_collection()
    
    print(f"🔍 DEBUG api_next_card - Usuario: {username}, Deck: '{deck}'")
    print(f"🔍 DEBUG - Colección: {cards_col is not None}, Time: {now}")

    if cards_col is None:
        # Memoria
        print("🔍 DEBUG - Modo memoria")
        user_cards = _mem_user_list(username)
        pool = [c for c in user_cards if c.get("due", now) <= now]
        if deck:
            pool = [c for c in pool if (c.get("deck") or "general").lower() == deck]
        pool.sort(key=lambda c: (c.get("box", 1), c.get("due", now)))
        
        print(f"🔍 DEBUG - Pool memoria: {len(pool)} tarjetas")
        if not pool:
            print("🔍 DEBUG - No hay tarjetas en memoria")
            return jsonify({"ok": True, "card": None})
        
        c = pool[0]
        card = _normalize_card_out(c)
        state = {"box": card["box"], "next_review_at": c.get("due", now).isoformat()}
        print(f"🔍 DEBUG - Tarjeta encontrada (memoria): {card['question'][:50]}...")
        return jsonify({"ok": True, "card": card, "state": state})

    # Con DB
    try:
        print("🔍 DEBUG - Modo MongoDB")
        
        # Verificar y sembrar tarjetas si el usuario no tiene ninguna
        _ensure_user_has_cards(username, cards_col)
        
        query = {'user': username, 'due': {'$lte': now}}

        if deck:
            query["deck"] = deck
            
        print(f"🔍 DEBUG - Query: {query}")
        
        doc = cards_col.find_one(query, sort=[("box", ASCENDING), ("due", ASCENDING)])
        
        if not doc:
            print("🔍 DEBUG - No hay tarjetas en MongoDB que cumplan query")
            # Debug: ver qué tarjetas hay en la DB
            all_cards = list(cards_col.find({"user": username}))
            print(f"🔍 DEBUG - Total tarjetas usuario: {len(all_cards)}")
            for c in all_cards:
                print(f"  - {c.get('front')} | Due: {c.get('due')} | Box: {c.get('box')}")
            return jsonify({"ok": True, "card": None})
        
        card = _normalize_card_out(doc)
        state = {"box": card["box"], "next_review_at": (doc.get("due") or now).isoformat()}
        print(f"🔍 DEBUG - Tarjeta encontrada (DB): {card['question'][:50]}...")
        return jsonify({"ok": True, "card": card, "state": state})
        
    except PyMongoError as e:
        print(f"❌ ERROR en api_next_card: {e}")
        return jsonify({"ok": False, "detail": str(e)}), 500

@leitner_bp.route("/api/leitner/answer", methods=["POST"])
@login_required_bp
def api_answer():
    """
    Acepta tanto:
      { "card_id": "...", "correct": true/false }
    como:
      { "cardId": "...", "result": "good"|"fail" }

    Actualiza box y due, y devuelve la siguiente tarjeta.
    """
    data = request.get_json(force=True, silent=True) or {}
    username = session.get("user")
    now = _now_utc()

    # Normalización payload
    card_id = data.get("card_id") or data.get("cardId")
    if card_id is None:
        return jsonify({"ok": False, "detail": "card_id requerido"}), 400
    if "correct" in data:
        correct = bool(data.get("correct"))
    else:
        correct = (data.get("result") == "good")

    cards_col = get_cards_collection()

    if cards_col is None:
        # Memoria
        user_cards = _mem_user_list(username)
        c = next((x for x in user_cards if str(x.get("id")) == str(card_id)), None)
        if not c:
            return jsonify({"ok": False, "detail": "Carta no encontrada"}), 404

        old_box = int(c.get("box", 1))
        new_box = 1 if not correct else min(old_box + 1, 6)
        c["box"] = new_box
        c["due"] = _due_for_box(new_box)
        c.setdefault("history", []).append({"ts": now.isoformat(), "result": "good" if correct else "fail"})

        # Prepara la siguiente
        next_resp = api_next_card().get_json()
        return jsonify({
            "ok": True,
            "box": new_box,
            "due": c["due"].isoformat(),
            "next": next_resp if isinstance(next_resp, dict) else None
        })

    # Con DB
    from bson import ObjectId
    try:
        doc = cards_col.find_one({"_id": ObjectId(card_id), "user": username}, {"box": 1, "deck": 1})
        if not doc:
            return jsonify({"ok": False, "detail": "Carta no encontrada"}), 404

        old_box = int(doc.get("box", 1))
        new_box = 1 if not correct else min(old_box + 1, 6)
        new_due = _due_for_box(new_box)

        cards_col.update_one(
            {"_id": ObjectId(card_id)},
            {
                "$set": {"box": new_box, "due": new_due, "last_reviewed": now},
                "$push": {"history": {"ts": now, "result": "good" if correct else "fail"}}
            }
        )

        # Siguiente tarjeta (mismo deck si lo tenía) - CORRECCIÓN AQUÍ
        deck = (doc.get("deck") or "").lower()
        
        # Llamar directamente a la función con los parámetros necesarios
        next_card_doc = cards_col.find_one(
            {'user': username, 'due': {'$lte': now}, **({'deck': deck} if deck else {})},
            sort=[("box", ASCENDING), ("due", ASCENDING)]
        )
        
        if next_card_doc:
            next_card = _normalize_card_out(next_card_doc)
            next_state = {"box": next_card["box"], "next_review_at": (next_card_doc.get("due") or now).isoformat()}
            next_response = {"ok": True, "card": next_card, "state": next_state}
        else:
            next_response = {"ok": True, "card": None}
        
        return jsonify({
            "ok": True,
            "box": new_box,
            "due": new_due.isoformat(),
            "next": next_response
        })
        
    except PyMongoError as e:
        return jsonify({"ok": False, "detail": str(e)}), 500


@leitner_bp.route("/api/leitner/summary", methods=["GET"])
@login_required_bp
def api_summary():
    """
    Devuelve contadores por caja:
    { ok, boxes: [ { _id: <box>, total: n, due: m }, ... ], due_total: X }
    Soporta ?deck=
    """
    username = session.get("user")
    deck = (request.args.get("deck") or "").strip().lower()
    now = _now_utc()
    cards_col = get_cards_collection()

    if cards_col is None:
        rows = {}
        for c in _mem_user_list(username):
            if deck and (c.get("deck") or "general").lower() != deck:
                continue
            b = int(c.get("box", 1))
            rows.setdefault(b, {"_id": b, "total": 0, "due": 0})
            rows[b]["total"] += 1
            if c.get("due", now) <= now:
                rows[b]["due"] += 1
        boxes = sorted(rows.values(), key=lambda r: r["_id"])
        due_total = sum(r["due"] for r in boxes)
        return jsonify({"ok": True, "boxes": boxes, "due_total": due_total})

    try:
        # Asegurar que el usuario tenga tarjetas
        _ensure_user_has_cards(username, cards_col)
        
        match = {"user": username}
        if deck:
            match["deck"] = deck
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": "$box",
                "total": {"$sum": 1},
                "due": {"$sum": {"$cond": [{"$lte": ["$due", now]}, 1, 0]}}
            }},
            {"$sort": {"_id": 1}}
        ]
        boxes = list(cards_col.aggregate(pipeline))
        due_total = sum(int(b.get("due", 0)) for b in boxes)
        return jsonify({"ok": True, "boxes": boxes, "due_total": int(due_total)})
    except PyMongoError as e:
        return jsonify({"ok": False, "detail": str(e)}), 500

@leitner_bp.route("/api/leitner/seed", methods=["POST"])
@login_required_bp
def api_seed():
    """
    Siembra cartas de demo para el usuario logueado (idempotente por 'front').
    body opcional: { deck: "general", cards: [{front, back}, ...] }
    """
    username = session.get("user")
    body = request.get_json(silent=True) or {}
    deck = (body.get("deck") or "general").strip().lower()
    cards_in = body.get("cards") or [
        {"front": "Presión mínima en línea de ataque", "back": "3-5 bar según manguera/boquilla"},
        {"front": "Código MAYDAY", "back": "MAYDAY MAYDAY MAYDAY + LUNAR"},
        {"front": "Triángulo del fuego", "back": "Combustible + Oxígeno + Calor"},
        {"front": "Ventilación táctica", "back": "Control de flujos, evitar flashover, coordinación con ataque"},
    ]

    cards_col = get_cards_collection()
    now = _now_utc()

    if cards_col is None:
        user_cards = _mem_user_list(username)
        existing_fronts = {c.get("front") for c in user_cards}
        inserted = 0
        for c in cards_in:
            if c["front"] in existing_fronts:
                continue
            user_cards.append({
                "id": f"mem-{len(user_cards)+1}",
                "user": username,
                "deck": deck,
                "front": c["front"],
                "back": c["back"],
                "box": 1,
                "due": _due_for_box(1),
                "created_at": now,
                "history": []
            })
            inserted += 1
        return jsonify({"ok": True, "inserted": inserted})

    try:
        inserted = 0
        for c in cards_in:
            exists = cards_col.find_one({"user": username, "deck": deck, "front": c["front"]})
            if exists:
                continue
            cards_col.insert_one({
                "user": username,
                "deck": deck,
                "front": c["front"],
                "back": c["back"],
                "box": 1,
                "due": _due_for_box(1),
                "created_at": now,
                "history": []
            })
            inserted += 1
        return jsonify({"ok": True, "inserted": inserted})
    except PyMongoError as e:
        return jsonify({"ok": False, "detail": str(e)}), 500