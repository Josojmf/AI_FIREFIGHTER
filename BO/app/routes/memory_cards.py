# app/routes/memory_cards.py - VERSIÓN CORREGIDA

from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
import requests

from config import Config

bp = Blueprint('memory_cards', __name__, url_prefix='/memory-cards')


def get_auth_headers():
    """Obtener headers de autenticación con token JWT"""
    token = session.get('api_token')
    if token:
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    return {'Content-Type': 'application/json'}


@bp.route('/')
@login_required
def card_list():
    """Listado de memory cards usando solo /api/memory-cards"""
    try:
        headers = get_auth_headers()
        print(f"🔍 Obteniendo memory cards con headers: {headers}")

        response = requests.get(
            f"{Config.API_BASE_URL}/api/memory-cards",
            headers=headers,
            timeout=10
        )

        print(f"📡 Respuesta API /api/memory-cards: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                cards = data.get('cards', [])
                print(f"✅ Memory cards obtenidas: {len(cards)}")
                return render_template('memory_cards/list.html', cards=cards)
            else:
                print(f"❌ API error: {data.get('detail', 'Unknown error')}")
                flash(f"Error en la API: {data.get('detail', 'Error desconocido')}", 'error')
        elif response.status_code == 401:
            print("❌ Error 401: Token inválido o expirado")
            flash('❌ Sesión expirada. Por favor inicia sesión nuevamente.', 'error')
            return redirect(url_for('auth.login'))
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            flash(f"Error al obtener memory cards: {response.status_code}", 'error')

        return render_template('memory_cards/list.html', cards=[])

    except requests.RequestException as e:
        print(f"❌ Error de conexión con la API: {e}")
        flash('Error de conexión con la API', 'error')
        return render_template('memory_cards/list.html', cards=[])


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_card():
    """Crear una nueva memory card"""
    if request.method == 'POST':
        try:
            headers = get_auth_headers()
            
            # Procesar tags si existen
            tags_str = request.form.get('tags', '')
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            data = {
                'question': request.form.get('question'),
                'answer': request.form.get('answer'),
                'category': request.form.get('category', 'General'),
                'difficulty': request.form.get('difficulty', 'medium'),
                'tags': tags,
                'box': 1  # Siempre empieza en box 1
            }
            
            print(f"📤 Enviando a API: {data}")

            response = requests.post(
                f"{Config.API_BASE_URL}/api/memory-cards",
                headers=headers,
                json=data,
                timeout=10
            )

            if response.status_code in (200, 201):
                flash('✅ Memory card creada correctamente', 'success')
                return redirect(url_for('memory_cards.card_list'))
            else:
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", "Error desconocido")
                except Exception:
                    detail = response.text or "Error desconocido"
                flash(f"❌ Error al crear memory card: {detail}", 'error')

        except requests.RequestException as e:
            print(f"❌ Error de conexión con la API: {e}")
            flash('❌ Error de conexión con la API', 'error')

    return render_template('memory_cards/create.html')


@bp.route('/<card_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_card(card_id):
    """Editar una memory card existente"""
    if request.method == 'POST':
        try:
            headers = get_auth_headers()
            data = {
                'question': request.form.get('title'),
                'answer': request.form.get('content'),
                'category': request.form.get('category'),
                'difficulty': request.form.get('difficulty', 'medium'),
                # Aquí también podrías mandar box/tags si los editas en el formulario
            }

            response = requests.put(
                f"{Config.API_BASE_URL}/api/memory-cards/{card_id}",
                headers=headers,
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                flash('✅ Memory card actualizada correctamente', 'success')
                return redirect(url_for('memory_cards.card_list'))
            else:
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", "Error desconocido")
                except Exception:
                    detail = response.text or "Error desconocido"
                flash(f"❌ Error al actualizar memory card: {detail}", 'error')

        except requests.RequestException as e:
            print(f"❌ Error de conexión con la API: {e}")
            flash('❌ Error de conexión con la API', 'error')

    # GET: obtener datos actuales de la card
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{Config.API_BASE_URL}/api/memory-cards/{card_id}",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                card = data.get('card', {})
                return render_template('memory_cards/edit.html', card=card)

        flash('Memory card no encontrada', 'error')
        return redirect(url_for('memory_cards.card_list'))

    except requests.RequestException as e:
        print(f"❌ Error de conexión con la API: {e}")
        flash('Error de conexión', 'error')
        return redirect(url_for('memory_cards.card_list'))


@bp.route('/<card_id>/delete', methods=['POST'])
@login_required
def delete_card(card_id):
    """Eliminar una memory card"""
    try:
        headers = get_auth_headers()
        response = requests.delete(
            f"{Config.API_BASE_URL}/api/memory-cards/{card_id}",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            flash('✅ Memory card eliminada correctamente', 'success')
        else:
            try:
                error_data = response.json()
                detail = error_data.get("detail", "Error desconocido")
            except Exception:
                detail = response.text or "Error desconocido"
            flash(f"❌ Error al eliminar memory card: {detail}", 'error')

    except requests.RequestException as e:
        print(f"❌ Error de conexión con la API: {e}")
        flash('❌ Error de conexión con la API', 'error')

    return redirect(url_for('memory_cards.card_list'))
