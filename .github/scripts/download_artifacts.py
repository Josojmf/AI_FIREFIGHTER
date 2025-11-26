#!/usr/bin/env python3
import requests
import json
import os
from pathlib import Path

def get_workflow_data():
    """Obtiene datos de los últimos workflows"""
    api_url = f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs"
    
    headers = {
        'Authorization': f"token {os.environ['GITHUB_TOKEN']}",
        'Accept': 'application/vnd.github.v3+json'
    }
    
    workflows = ['CI Pipeline - Optimized', 'CD - Ultra Robust Deploy']
    data = {}
    
    for workflow in workflows:
        response = requests.get(f"{api_url}?per_page=5", headers=headers)
        if response.status_code == 200:
            data[workflow] = response.json()['workflow_runs']
    
    return data

def save_dashboard_data(data):
    """Guarda datos para el dashboard"""
    Path('artifacts').mkdir(exist_ok=True)
    
    with open('artifacts/workflow_data.json', 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    data = get_workflow_data()
    save_dashboard_data(data)