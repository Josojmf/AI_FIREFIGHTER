from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required
import requests
from config import Config

bp = Blueprint('memory_cards', __name__, url_prefix='/memory-cards')

@bp.route('/')
@login_required
def card_list():
    # TODO: Implementar cuando la API de memory cards esté disponible
    return render_template('memory_cards/list.html', cards=[])

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_card():
    if request.method == 'POST':
        # TODO: Implementar creación de memory cards
        flash('Memory card creada correctamente', 'success')
        return redirect(url_for('memory_cards.card_list'))
    
    return render_template('memory_cards/create.html')

@bp.route('/<card_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_card(card_id):
    # TODO: Implementar edición de memory cards
    return render_template('memory_cards/edit.html')

@bp.route('/<card_id>/delete', methods=['POST'])
@login_required
def delete_card(card_id):
    # TODO: Implementar eliminación de memory cards
    flash('Memory card eliminada', 'success')
    return redirect(url_for('memory_cards.card_list'))