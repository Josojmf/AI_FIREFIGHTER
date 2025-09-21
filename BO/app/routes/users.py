from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
import requests
from config import Config

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/')
@login_required
def user_list():
    try:
        response = requests.get(f"{Config.API_BASE_URL}/api/users", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                return render_template('users/list.html', users=data['users'])
        
        flash('Error al obtener usuarios', 'error')
        return render_template('users/list.html', users=[])
    
    except requests.RequestException as e:
        flash('Error de conexión con la API', 'error')
        return render_template('users/list.html', users=[])

@bp.route('/<user_id>')
@login_required
def user_detail(user_id):
    try:
        response = requests.get(f"{Config.API_BASE_URL}/api/users/{user_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                return render_template('users/detail.html', user=data['user'])
        
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('users.user_list'))
    
    except requests.RequestException:
        flash('Error de conexión', 'error')
        return redirect(url_for('users.user_list'))

@bp.route('/<user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    try:
        # Primero obtener el usuario actual
        response = requests.get(f"{Config.API_BASE_URL}/api/users/{user_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                current_status = data['user'].get('status', 'active')
                new_status = 'inactive' if current_status == 'active' else 'active'
                
                # Actualizar estado
                update_response = requests.patch(
                    f"{Config.API_BASE_URL}/api/users/{user_id}",
                    json={"status": new_status},
                    timeout=5
                )
                
                if update_response.status_code == 200:
                    flash(f'Estado actualizado a {new_status}', 'success')
                else:
                    flash('Error al actualizar', 'error')
        
        return redirect(url_for('users.user_detail', user_id=user_id))
    
    except requests.RequestException:
        flash('Error de conexión', 'error')
        return redirect(url_for('users.user_list'))