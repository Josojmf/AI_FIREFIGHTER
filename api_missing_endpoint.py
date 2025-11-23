@app.get("/api/users/<user_id>")
def api_get_user(user_id):
    """Obtener un usuario específico por ID - Solo admin"""
    try:
        authorized, auth_result = require_auth(required_role="admin")
        if not authorized:
            return auth_result

        user_doc = users.find_one({"_id": user_id})
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404

        return jsonify({
            "ok": True,
            "user": {
                "id": user_doc["_id"],
                "username": user_doc["username"],
                "email": user_doc["email"],
                "role": user_doc.get("role", "user"),
                "status": user_doc.get("status", "active"),
                "created_at": user_doc.get("created_at", "").isoformat() if user_doc.get("created_at") else "",
                "mfa_enabled": user_doc.get("mfa_enabled", False),
                "has_leitner_progress": "leitner_progress" in user_doc,
                "has_backoffice_cards": "backoffice_cards" in user_doc
            }
        })

    except Exception as e:
        app.logger.error(f"Error obteniendo usuario {user_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500