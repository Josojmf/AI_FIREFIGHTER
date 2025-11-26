#!/usr/bin/env python3
from jinja2 import Template
import json
import os

# Template HTML para el dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Dashboard - {{ repository }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-800">
                <i class="fas fa-rocket mr-3 text-blue-500"></i>
                DevOps Dashboard - {{ repository }}
            </h1>
            <p class="text-gray-600">Last updated: {{ last_updated }}</p>
        </header>

        <!-- Metrics Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <!-- CI Success Rate -->
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-500 text-sm">CI Success Rate</p>
                        <p class="text-2xl font-bold text-green-600">{{ metrics.ci_success_rate }}%</p>
                    </div>
                    <i class="fas fa-check-circle text-green-500 text-2xl"></i>
                </div>
            </div>

            <!-- Deployment Frequency -->
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-500 text-sm">Deployment Frequency</p>
                        <p class="text-2xl font-bold text-blue-600">{{ metrics.deployment_frequency }}</p>
                    </div>
                    <i class="fas fa-ship text-blue-500 text-2xl"></i>
                </div>
            </div>

            <!-- Test Coverage -->
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-500 text-sm">Test Coverage</p>
                        <p class="text-2xl font-bold text-orange-600">{{ metrics.test_coverage }}</p>
                    </div>
                    <i class="fas fa-vial text-orange-500 text-2xl"></i>
                </div>
            </div>

            <!-- Security Issues -->
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-500 text-sm">Security Issues</p>
                        <p class="text-2xl font-bold text-red-600">{{ metrics.security_issues.critical }} Critical</p>
                    </div>
                    <i class="fas fa-shield-alt text-red-500 text-2xl"></i>
                </div>
            </div>
        </div>

        <!-- Workflow Status -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Workflows Section -->
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-bold mb-4 text-gray-800">
                    <i class="fas fa-play-circle mr-2 text-blue-500"></i>
                    Workflow Status
                </h2>
                <div class="space-y-4">
                    {% for workflow in workflows %}
                    <div class="flex items-center justify-between p-3 border rounded-lg {% if workflow.status == 'success' %}bg-green-50 border-green-200{% elif workflow.status == 'warning' %}bg-yellow-50 border-yellow-200{% else %}bg-red-50 border-red-200{% endif %}">
                        <div>
                            <p class="font-semibold">{{ workflow.name }}</p>
                            <p class="text-sm text-gray-500">{{ workflow.duration }} • {{ workflow.last_run[:10] }}</p>
                        </div>
                        <span class="px-3 py-1 rounded-full text-xs font-semibold {% if workflow.status == 'success' %}bg-green-100 text-green-800{% elif workflow.status == 'warning' %}bg-yellow-100 text-yellow-800{% else %}bg-red-100 text-red-800{% endif %}">
                            {{ workflow.status }}
                        </span>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Deployments Section -->
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-bold mb-4 text-gray-800">
                    <i class="fas fa-cloud-upload-alt mr-2 text-green-500"></i>
                    Deployment History
                </h2>
                <div class="space-y-4">
                    {% for deployment in deployments %}
                    <div class="flex items-center justify-between p-3 border rounded-lg {% if deployment.status == 'success' %}bg-green-50 border-green-200{% else %}bg-red-50 border-red-200{% endif %}">
                        <div>
                            <p class="font-semibold">{{ deployment.environment|title }}</p>
                            <p class="text-sm text-gray-500">{{ deployment.version }} • {{ deployment.timestamp[:10] }}</p>
                        </div>
                        <span class="px-3 py-1 rounded-full text-xs font-semibold {% if deployment.status == 'success' %}bg-green-100 text-green-800{% else %}bg-red-100 text-red-800{% endif %}">
                            {{ deployment.status }}
                        </span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Alerts Section -->
        <div class="mt-8 bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-bold mb-4 text-gray-800">
                <i class="fas fa-bell mr-2 text-yellow-500"></i>
                Recent Alerts
            </h2>
            <div class="space-y-3">
                {% for alert in alerts %}
                <div class="flex items-center p-3 border rounded-lg {% if alert.type == 'warning' %}bg-yellow-50 border-yellow-200{% else %}bg-blue-50 border-blue-200{% endif %}">
                    <i class="fas {% if alert.type == 'warning' %}fa-exclamation-triangle text-yellow-500{% else %}fa-info-circle text-blue-500{% endif %} mr-3"></i>
                    <div>
                        <p class="font-semibold">{{ alert.message }}</p>
                        <p class="text-sm text-gray-500">{{ alert.component }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Charts Section -->
        <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-bold mb-4 text-gray-800">CI Success Over Time</h2>
                <canvas id="ciChart" width="400" height="200"></canvas>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-bold mb-4 text-gray-800">Deployment Frequency</h2>
                <canvas id="deploymentChart" width="400" height="200"></canvas>
            </div>
        </div>
    </div>

    <script>
        // Charts configuration
        const ciCtx = document.getElementById('ciChart').getContext('2d');
        const deploymentCtx = document.getElementById('deploymentChart').getContext('2d');
        
        new Chart(ciCtx, {
            type: 'line',
            data: {
                labels: ['Jan 10', 'Jan 11', 'Jan 12', 'Jan 13', 'Jan 14', 'Jan 15'],
                datasets: [{
                    label: 'Success Rate %',
                    data: [92, 95, 98, 96, 97, 95],
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    tension: 0.4
                }]
            }
        });

        new Chart(deploymentCtx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                datasets: [{
                    label: 'Deployments',
                    data: [2, 3, 1, 4, 2],
                    backgroundColor: 'rgb(59, 130, 246)'
                }]
            }
        });
    </script>
</body>
</html>
"""

def build_html():
    """Construye el HTML del dashboard"""
    with open('dashboard_data.json', 'r') as f:
        data = json.load(f)
    
    template = Template(DASHBOARD_TEMPLATE)
    html_content = template.render(**data)
    
    os.makedirs('_site', exist_ok=True)
    with open('_site/index.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    build_html()