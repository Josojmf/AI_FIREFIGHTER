#!/usr/bin/env python3
import json
import os
from datetime import datetime

def generate_dashboard_json():
    """Genera el JSON con todos los datos del dashboard"""
    
    dashboard_data = {
        "last_updated": datetime.now().isoformat(),
        "repository": os.environ.get('GITHUB_REPOSITORY', ''),
        "metrics": {
            "ci_success_rate": calculate_success_rate(),
            "deployment_frequency": get_deployment_frequency(),
            "test_coverage": get_test_coverage(),
            "security_issues": get_security_issues()
        },
        "workflows": get_workflow_status(),
        "deployments": get_deployment_history(),
        "alerts": get_alerts()
    }
    
    with open('dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)

def calculate_success_rate():
    """Calcula tasa de éxito de CI"""
    return 95  # Mock - implementar lógica real

def get_deployment_frequency():
    return "2-3/week"

def get_test_coverage():
    return "78%"

def get_security_issues():
    return {"critical": 0, "high": 2, "medium": 5}

def get_workflow_status():
    return [
        {"name": "CI Pipeline", "status": "success", "duration": "12m", "last_run": "2024-01-15T10:30:00Z"},
        {"name": "CD Deployment", "status": "success", "duration": "18m", "last_run": "2024-01-15T09:15:00Z"},
        {"name": "Quality Metrics", "status": "warning", "duration": "3m", "last_run": "2024-01-15T08:00:00Z"}
    ]

def get_deployment_history():
    return [
        {"environment": "production", "version": "v1.2.3", "status": "success", "timestamp": "2024-01-15T09:15:00Z"},
        {"environment": "staging", "version": "v1.2.2", "status": "success", "timestamp": "2024-01-14T14:20:00Z"}
    ]

def get_alerts():
    return [
        {"type": "warning", "message": "Test coverage below 80%", "component": "tests"},
        {"type": "info", "message": "Security scan completed", "component": "security"}
    ]

if __name__ == "__main__":
    generate_dashboard_json()