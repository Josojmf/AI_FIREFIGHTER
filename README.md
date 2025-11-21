# 🔥 FirefighterAI - Plataforma de Preparación para Oposiciones de Bombero

<div align="center">

![FirefighterAI Banner](https://via.placeholder.com/1200x300/0a0e27/ff6b35?text=FirefighterAI+%7C+Entrena+como+un+profesional)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248.svg)](https://www.mongodb.com/cloud/atlas)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Deploy](https://img.shields.io/badge/Deploy-Digital_Ocean-0080FF.svg)](https://www.digitalocean.com/)

**Una plataforma integral de preparación para oposiciones de bombero que combina IA, metodologías de aprendizaje científicas y acceso a contenido certificado.**

[🚀 Demo en Vivo](https://firefighterai.com) • [📚 Documentación](https://github.com/Josojmf/AI_Firefighter/wiki) • [🐛 Reportar Bug](https://github.com/Josojmf/AI_Firefighter/issues/new?template=bug-report.yml) • [💡 Proponer Feature](https://github.com/Josojmf/AI_Firefighter/issues/new?template=user-story.yml)

</div>

---

## 📋 Tabla de Contenidos

- [✨ Características](#-características)
- [🏗️ Arquitectura](#️-arquitectura)
- [🚀 Inicio Rápido](#-inicio-rápido)
  - [📦 Prerrequisitos](#-prerrequisitos)
  - [⚙️ Instalación Local](#️-instalación-local)
  - [🐳 Docker Setup](#-docker-setup)
- [📚 Stack Tecnológico](#-stack-tecnológico)
- [🗂️ Estructura del Proyecto](#️-estructura-del-proyecto)
- [🔧 Configuración](#-configuración)
- [🎯 Roadmap](#-roadmap)
- [🤝 Contribuir](#-contribuir)
- [📝 Licencia](#-licencia)
- [👥 Equipo](#-equipo)
- [🙏 Agradecimientos](#-agradecimientos)

---

## ✨ Características

### 🤖 **Chat AI Inteligente**
Asistente conversacional potenciado por **Claude AI** (Anthropic) que responde preguntas sobre normativa de bomberos, procedimientos de emergencia y temario de oposiciones.

- 💬 Respuestas contextuales y precisas
- 📚 Conocimiento específico del sector
- 🔄 Historial de conversaciones
- ⚡ Respuestas en tiempo real con streaming

### 🎴 **Sistema Leitner de Repetición Espaciada**
Metodología científicamente probada para maximizar la retención de conocimiento.

- 📊 5 niveles de dominio de contenido
- ⏰ Algoritmo de repetición óptima
- 📈 Tracking de progreso individual
- 🔄 Sincronización con MongoDB Atlas
- 📱 Disponible en todos los dispositivos

### 🌐 **Integración de Plataformas Certificadas**
Acceso embebido a las principales academias de preparación.

- 🎓 **OnFire Academy** - Contenido multimedia interactivo
- 📖 **FormacionCertificado.com** - Cursos homologados
- 🔓 Sistema de proxy avanzado para bypass de restricciones
- 🖼️ Procesamiento inteligente de assets y recursos

### 🔐 **Autenticación Robusta**
Sistema de seguridad multicapa para proteger datos de usuarios.

- 🔑 Autenticación con email/password (bcrypt hashing)
- 📱 MFA (Multi-Factor Authentication) con PyOTP
- 🎫 JWT tokens para sesiones
- 👥 Roles de usuario (User/Admin)
- 🛡️ Protección CSRF y rate limiting

### ⚙️ **BackOffice Administrativo**
Panel de administración completo construido con **React + Vite**.

- 📝 CRUD de tarjetas de estudio
- 👥 Gestión de usuarios
- 📊 Dashboard con estadísticas
- 🎨 UI moderna con Tailwind CSS
- 🔄 Integración en tiempo real con API

---

## 🏗️ Arquitectura

<div align="center">

```mermaid
graph TB
    subgraph "Client Layer"
        A[Browser/Mobile]
    end
    
    subgraph "Frontend Services"
        B[Flask Frontend<br/>Port 5001]
        C[React BackOffice<br/>Port 5173]
    end
    
    subgraph "Backend Services"
        D[Flask API<br/>Port 5000]
    end
    
    subgraph "External Services"
        E[Claude AI API<br/>Anthropic]
        F[OnFire Academy]
        G[FormacionCertificado]
    end
    
    subgraph "Data Layer"
        H[(MongoDB Atlas)]
    end
    
    subgraph "Infrastructure"
        I[Docker Containers]
        J[GitHub Actions CI/CD]
        K[Digital Ocean Droplet]
    end
    
    A -->|HTTPS| B
    A -->|HTTPS| C
    B -->|REST API| D
    C -->|REST API| D
    D -->|Queries| H
    D -->|AI Requests| E
    B -->|Proxy| F
    B -->|Proxy| G
    I -->|Hosts| B
    I -->|Hosts| C
    I -->|Hosts| D
    J -->|Deploys to| K
    K -->|Runs| I
```

</div>

### 🎯 **Principios de Diseño**

- **🔄 Microservicios**: Separación clara entre Frontend, API y BackOffice
- **📦 Containerización**: Docker para consistencia entre entornos
- **🚀 CI/CD**: Despliegues automatizados con GitHub Actions
- **☁️ Cloud-Native**: MongoDB Atlas + Digital Ocean
- **🔐 Security First**: MFA, JWT, bcrypt, HTTPS
- **📊 Data-Driven**: Analytics y tracking integrados

---

## 🚀 Inicio Rápido

### 📦 Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.11+** ([Descargar](https://www.python.org/downloads/))
- **Node.js 18+** y **npm** ([Descargar](https://nodejs.org/))
- **Docker** y **Docker Compose** ([Descargar](https://www.docker.com/))
- **Git** ([Descargar](https://git-scm.com/))
- **MongoDB Atlas Account** (Gratis: [Registrarse](https://www.mongodb.com/cloud/atlas/register))

### ⚙️ Instalación Local

#### 1️⃣ **Clonar el Repositorio**

```bash
git clone https://github.com/Josojmf/AI_Firefighter.git
cd AI_Firefighter
```

#### 2️⃣ **Configurar Variables de Entorno**

Crea un archivo `_env` en la raíz del proyecto:

```bash
# MongoDB Atlas
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/firefighter?retryWrites=true&w=majority

# Claude AI (Anthropic)
ANTHROPIC_API_KEY=tu_clave_api_de_anthropic

# Flask Configuration
SECRET_KEY=tu_secret_key_super_segura_aqui
FLASK_ENV=development

# Security
JWT_SECRET_KEY=otra_clave_segura_para_jwt

# Optional: Email notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_password
```

#### 3️⃣ **Instalar Dependencias del Backend**

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows)
.\venv\Scripts\activate

# Activar entorno virtual (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### 4️⃣ **Instalar Dependencias del BackOffice**

```bash
cd backoffice
npm install
cd ..
```

#### 5️⃣ **Inicializar Base de Datos**

```bash
# Crear usuario administrador inicial
python insert-adm.py

# Verificar colecciones
python check_collections.py
```

#### 6️⃣ **Ejecutar la Aplicación**

**Opción A: Desarrollo Local (múltiples terminales)**

```bash
# Terminal 1: Backend API
python api.py

# Terminal 2: Frontend
python app.py

# Terminal 3: BackOffice (opcional)
cd backoffice
npm run dev
```

**Opción B: Producción Local con Waitress**

```bash
python serve_waitress.py
```

#### 7️⃣ **Acceder a la Aplicación**

- 🌐 **Frontend**: [http://localhost:5001](http://localhost:5001)
- 🔌 **API**: [http://localhost:5000](http://localhost:5000)
- ⚙️ **BackOffice**: [http://localhost:5173](http://localhost:5173)

### 🐳 Docker Setup

#### **Opción 1: Docker Compose (Recomendado)**

```bash
# Construir y levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

#### **Opción 2: Docker Manual**

```bash
# Construir imagen
docker build -t firefighterai:latest .

# Ejecutar contenedor
docker run -d \
  --name firefighter-app \
  -p 5000:5000 \
  -p 5001:5001 \
  --env-file _env \
  firefighterai:latest

# Ver logs
docker logs -f firefighter-app

# Detener contenedor
docker stop firefighter-app
docker rm firefighter-app
```

#### **Docker Compose Configuration**

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: firefighter-api
    ports:
      - "5000:5000"
    env_file:
      - _env
    networks:
      - firefighter-network
    restart: unless-stopped

  frontend:
    build: .
    container_name: firefighter-frontend
    ports:
      - "5001:5001"
    env_file:
      - _env
    networks:
      - firefighter-network
    restart: unless-stopped
    depends_on:
      - api

networks:
  firefighter-network:
    driver: bridge
```

---

## 📚 Stack Tecnológico

### **Backend**

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | 3.11+ | Lenguaje principal |
| ![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white) | 3.0+ | Framework web |
| ![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=mongodb&logoColor=white) | Atlas | Base de datos NoSQL |
| ![PyMongo](https://img.shields.io/badge/PyMongo-47A248?style=flat&logo=mongodb&logoColor=white) | 4.6+ | MongoDB driver |
| ![JWT](https://img.shields.io/badge/JWT-000000?style=flat&logo=jsonwebtokens&logoColor=white) | - | Autenticación |
| ![bcrypt](https://img.shields.io/badge/bcrypt-338833?style=flat) | - | Password hashing |
| ![PyOTP](https://img.shields.io/badge/PyOTP-FF6B35?style=flat) | - | MFA/2FA |
| ![Waitress](https://img.shields.io/badge/Waitress-WSGI-orange?style=flat) | - | WSGI server |

### **Frontend**

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white) | - | Estructura |
| ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white) | - | Estilos |
| ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black) | ES6+ | Interactividad |
| ![Jinja2](https://img.shields.io/badge/Jinja2-B41717?style=flat&logo=jinja&logoColor=white) | - | Templates |

### **BackOffice**

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| ![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black) | 18.0+ | UI Library |
| ![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat&logo=vite&logoColor=white) | 5.0+ | Build tool |
| ![TailwindCSS](https://img.shields.io/badge/Tailwind-38B2AC?style=flat&logo=tailwind-css&logoColor=white) | 3.0+ | CSS Framework |

### **AI & External APIs**

| Servicio | Propósito |
|---------|-----------|
| ![Claude](https://img.shields.io/badge/Claude_AI-FF6B35?style=flat) | Chat conversacional |
| **OnFire Academy** | Contenido de formación |
| **FormacionCertificado** | Cursos homologados |

### **DevOps & Infrastructure**

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white) | 24+ | Containerización |
| ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white) | - | CI/CD |
| ![Digital Ocean](https://img.shields.io/badge/Digital_Ocean-0080FF?style=flat&logo=digitalocean&logoColor=white) | - | Hosting |
| ![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat&logo=nginx&logoColor=white) | - | Reverse proxy |

---

## 🗂️ Estructura del Proyecto

```
AI_Firefighter/
│
├── 📁 .github/                      # GitHub configurations
│   ├── workflows/                   # CI/CD pipelines
│   │   ├── cd.yml                  # Continuous Deployment
│   │   ├── ci.yml                  # Continuous Integration
│   │   ├── quality-gates.yml       # Code quality checks
│   │   └── security.yml            # Security scanning
│   └── ISSUE_TEMPLATE/             # Issue templates
│       ├── user-story.yml          # User story form
│       ├── bug-report.yml          # Bug report form
│       └── task.yml                # Technical task form
│
├── 📁 api/                          # Backend API (Flask)
│   ├── __init__.py
│   ├── database.py                 # MongoDB connection
│   ├── utils.py                    # Utility functions
│   └── routes/                     # API endpoints
│       ├── auth.py                 # Authentication routes
│       ├── users.py                # User management
│       ├── memory_cards.py         # Leitner cards API
│       └── dashboard.py            # Dashboard data
│
├── 📁 templates/                    # Frontend HTML templates
│   ├── layout.html                 # Base layout
│   ├── login.html                  # Login page
│   ├── dashboard.html              # Main dashboard
│   ├── chat.html                   # AI chat interface
│   ├── study.html                  # Leitner study mode
│   ├── modern-index.html           # Landing page
│   └── auth/                       # Auth templates
│       ├── setup_mfa.html
│       └── verify_mfa.html
│
├── 📁 static/                       # Static assets
│   ├── css/
│   │   ├── layout.css
│   │   ├── dashboard.css
│   │   ├── chat.css
│   │   ├── study.css
│   │   └── components.css
│   ├── js/
│   │   ├── app-init.js
│   │   ├── chat.js
│   │   ├── study.js
│   │   └── animations.js
│   └── assets/
│       ├── images/
│       ├── icons/
│       └── fonts/
│
├── 📁 backoffice/                   # React Admin Panel
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── UserList.jsx
│   │   │   └── CardEditor.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Users.jsx
│   │   │   └── Cards.jsx
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── 📁 scripts/                      # Utility scripts
│   ├── check_collections.py        # DB verification
│   ├── insert-adm.py               # Create admin user
│   ├── generate_questions.py       # Question generator
│   └── pdf_to_txt.py               # PDF processing
│
├── 📁 leitner/                      # Leitner system logic
│   ├── leitner.py                  # Core algorithm
│   └── leitner_sync.py             # DB synchronization
│
├── 📁 docs/                         # Documentation
│   ├── assets/                     # Firefighting materials
│   │   └── pdf/
│   └── README.md
│
├── 📁 config/                       # Configuration files
│   └── config.yml
│
├── 📄 app.py                        # Frontend Flask app
├── 📄 api.py                        # Backend Flask API
├── 📄 config.py                     # App configuration
├── 📄 serve_waitress.py            # Production WSGI server
├── 📄 requirements.txt             # Python dependencies
├── 📄 Dockerfile                   # Docker image config
├── 📄 docker-compose.yml           # Multi-container setup
├── 📄 _env                         # Environment variables (template)
├── 📄 .gitignore
├── 📄 LICENSE
└── 📄 README.md                    # This file
```

### 📊 **Estadísticas del Proyecto**

```
Total Files:       150+
Lines of Code:     ~12,000
Python Modules:    25
React Components:  30+
API Endpoints:     20+
Templates:         15
```

---

## 🔧 Configuración

### 🔑 **Variables de Entorno Esenciales**

Crea un archivo `_env` basado en esta plantilla:

```bash
# ======================
# MongoDB Configuration
# ======================
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/firefighter?retryWrites=true&w=majority
MONGO_DB_NAME=firefighter

# ======================
# Flask Configuration
# ======================
SECRET_KEY=genera_una_clave_super_segura_con_openssl
FLASK_ENV=production  # development | production
FLASK_DEBUG=False

# ======================
# Security
# ======================
JWT_SECRET_KEY=otra_clave_diferente_para_jwt
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour in seconds
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# ======================
# Claude AI (Anthropic)
# ======================
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
CLAUDE_MODEL=claude-3-sonnet-20240229
MAX_TOKENS=1000

# ======================
# Application Settings
# ======================
API_PORT=5000
FRONTEND_PORT=5001
BACKOFFICE_PORT=5173

# ======================
# Rate Limiting
# ======================
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# ======================
# CORS Settings
# ======================
CORS_ORIGINS=http://localhost:5001,https://firefighterai.com

# ======================
# Email Configuration (Optional)
# ======================
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=True
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_app_password

# ======================
# Logging
# ======================
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR | CRITICAL
LOG_FILE=logs/app.log

# ======================
# External Services
# ======================
ONFIRE_ACADEMY_URL=https://formacioncertificadoprofesional.com
FORMACION_CERT_URL=https://formacioncertificadoprofesional.com

# ======================
# Feature Flags
# ======================
ENABLE_MFA=True
ENABLE_EMAIL_VERIFICATION=False
ENABLE_ANALYTICS=True
MAINTENANCE_MODE=False
```

### 🔒 **Generar Claves Seguras**

```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"

# PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

### 🗄️ **Configuración de MongoDB Atlas**

1. **Crear Cluster Gratuito**
   - Ve a [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Crea un cluster M0 (gratis)
   - Región recomendada: la más cercana a tu servidor

2. **Configurar Acceso**
   - Database Access → Add New Database User
   - Network Access → Add IP Address (0.0.0.0/0 para dev)

3. **Obtener Connection String**
   - Clusters → Connect → Connect your application
   - Copia la URI y reemplaza `<password>` con tu contraseña

4. **Crear Base de Datos**
   ```javascript
   use firefighter;
   
   db.createCollection("users");
   db.createCollection("memory_cards");
   db.createCollection("chat_history");
   db.createCollection("leitner_progress");
   ```

### 🎨 **Personalización del Frontend**

Edita las variables CSS en `static/css/layout.css`:

```css
:root {
  /* Colores principales */
  --primary-color: #ff6b35;
  --secondary-color: #0a0e27;
  --accent-color: #ffd700;
  
  /* Colores de estado */
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
  --info-color: #3b82f6;
  
  /* Tipografía */
  --font-primary: 'Inter', sans-serif;
  --font-heading: 'Poppins', sans-serif;
  --font-mono: 'Fira Code', monospace;
  
  /* Espaciado */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Sombras */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  
  /* Bordes */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
  --radius-full: 9999px;
}
```

---

## 🎯 Roadmap

### ✅ **v1.0 - MVP (Completado)**
- [x] Sistema de autenticación con MFA
- [x] Chat AI con Claude
- [x] Sistema Leitner básico
- [x] Integración MongoDB Atlas
- [x] Deploy en Digital Ocean
- [x] CI/CD con GitHub Actions

### 🔄 **v1.1 - Embeddings Complete (En Progreso)**
- [ ] OnFire Academy completamente embebido
- [ ] FormacionCertificado integración completa
- [ ] Resolver iframe blocking en todos los navegadores
- [ ] Proxy optimizado para mejor performance
- [ ] Cache de contenido externo

### 🚀 **v1.2 - Enhanced Learning (Q1 2026)**
- [ ] Sistema de gamificación
- [ ] Badges y logros
- [ ] Leaderboards públicos
- [ ] Estadísticas avanzadas de progreso
- [ ] Modo competitivo

### 🎨 **v1.3 - UX Improvements (Q2 2026)**
- [ ] PWA (Progressive Web App)
- [ ] Modo offline
- [ ] Notificaciones push
- [ ] Tema dark/light personalizable
- [ ] Accesibilidad WCAG 2.1 AA

### 🧠 **v2.0 - AI Enhancements (Q3 2026)**
- [ ] Generación automática de preguntas desde PDFs
- [ ] Quiz adaptativos con IA
- [ ] Recomendaciones personalizadas de estudio
- [ ] Análisis de debilidades con IA
- [ ] Tutor virtual 24/7

### 📱 **v2.1 - Mobile Native (Q4 2026)**
- [ ] App iOS nativa
- [ ] App Android nativa
- [ ] Sincronización cross-platform
- [ ] Notificaciones nativas
- [ ] Widgets para home screen

### 🌍 **v3.0 - Multi-Region & Scale (2027)**
- [ ] Soporte multi-idioma (EN, FR, PT)
- [ ] CDN global
- [ ] Kubernetes deployment
- [ ] Microservicios completos
- [ ] API pública para terceros

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Sigue estos pasos para contribuir al proyecto:

### 🔀 **Workflow de Contribución**

```bash
# 1. Fork el repositorio en GitHub

# 2. Clonar tu fork
git clone https://github.com/TU_USUARIO/AI_Firefighter.git
cd AI_Firefighter

# 3. Crear una rama para tu feature
git checkout -b feature/mi-nueva-funcionalidad

# 4. Hacer cambios y commits
git add .
git commit -m "feat: añadir nueva funcionalidad increíble"

# 5. Push a tu fork
git push origin feature/mi-nueva-funcionalidad

# 6. Crear Pull Request en GitHub
```

### 📝 **Convención de Commits**

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: nueva funcionalidad
fix: corrección de bug
docs: cambios en documentación
style: formateo, punto y coma, etc
refactor: refactorización de código
test: añadir tests
chore: tareas de mantenimiento
```

**Ejemplos:**

```bash
git commit -m "feat(auth): añadir recuperación de contraseña"
git commit -m "fix(chat): corregir streaming de respuestas"
git commit -m "docs: actualizar README con nuevas instrucciones"
git commit -m "refactor(leitner): optimizar algoritmo de repetición"
```

### 🐛 **Reportar Bugs**

Usa nuestra [plantilla de bug report](https://github.com/Josojmf/AI_Firefighter/issues/new?template=bug-report.yml) e incluye:

- ✅ Descripción clara del problema
- ✅ Pasos para reproducir
- ✅ Comportamiento esperado vs actual
- ✅ Screenshots/logs si es posible
- ✅ Entorno (OS, navegador, versión)

### 💡 **Proponer Features**

Usa nuestra [plantilla de user story](https://github.com/Josojmf/AI_Firefighter/issues/new?template=user-story.yml) e incluye:

- ✅ Descripción de la funcionalidad
- ✅ Justificación del valor aportado
- ✅ Criterios de aceptación
- ✅ Mockups/wireframes si aplica

### ✅ **Checklist de Pull Request**

Antes de crear un PR, asegúrate de:

- [ ] El código sigue las convenciones del proyecto
- [ ] Todos los tests pasan (`pytest`)
- [ ] No hay errores de linting (`flake8`, `pylint`)
- [ ] La documentación está actualizada
- [ ] Los commits siguen Conventional Commits
- [ ] El PR tiene una descripción clara
- [ ] Screenshots para cambios visuales

### 🎨 **Guía de Estilo**

**Python:**
```python
# Usar Type Hints
def get_user(user_id: str) -> dict:
    """
    Obtener usuario por ID.
    
    Args:
        user_id: ID único del usuario
        
    Returns:
        dict con datos del usuario
    """
    return db.users.find_one({"_id": user_id})

# PEP 8 compliant
# Max line length: 100 chars
# Use docstrings for all functions
```

**JavaScript:**
```javascript
// Use ES6+ features
const getUserData = async (userId) => {
  try {
    const response = await fetch(`/api/users/${userId}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching user:', error);
    throw error;
  }
};

// JSDoc comments for functions
/**
 * Fetch user data from API
 * @param {string} userId - User ID
 * @returns {Promise<Object>} User data
 */
```

---

## 📝 Licencia

Este proyecto está bajo la licencia **MIT License** - ver el archivo [LICENSE](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2025 Jose Maria Fernandez (Josojmf)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👥 Equipo

<div align="center">

### 🔥 **Core Team**

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/Josojmf">
        <img src="https://github.com/Josojmf.png" width="100px;" alt="Jose Maria Fernandez"/>
        <br />
        <sub><b>Jose Maria Fernandez</b></sub>
      </a>
      <br />
      <sub>🎯 Founder & Lead Developer</sub>
      <br />
      <sub>Full-stack • DevOps • AI Integration</sub>
    </td>
  </tr>
</table>

### 🤝 **Contributors**

¡Este proyecto está abierto a contribuciones! Sé el primero en aparecer aquí.

[![Contributors](https://contrib.rocks/image?repo=Josojmf/AI_Firefighter)](https://github.com/Josojmf/AI_Firefighter/graphs/contributors)

</div>

---

## 🙏 Agradecimientos

Este proyecto no sería posible sin estas increíbles tecnologías y recursos:

### 🛠️ **Tecnologías y Frameworks**

- [**Flask**](https://flask.palletsprojects.com/) - Framework web Python ligero y poderoso
- [**React**](https://reactjs.org/) - Biblioteca UI para interfaces modernas
- [**MongoDB Atlas**](https://www.mongodb.com/cloud/atlas) - Base de datos NoSQL en la nube
- [**Claude AI**](https://www.anthropic.com/) - Modelo de lenguaje conversacional
- [**Docker**](https://www.docker.com/) - Plataforma de containerización
- [**Vite**](https://vitejs.dev/) - Build tool ultra-rápido
- [**Tailwind CSS**](https://tailwindcss.com/) - Framework CSS utility-first

### 📚 **Recursos y Comunidades**

- [**OnFire Academy**](https://formacioncertificadoprofesional.com) - Contenido educativo de calidad
- **Stack Overflow** - Por resolver millones de dudas
- **GitHub Community** - Por el apoyo y feedback
- **Bomberos de España** - Por su vocación y servicio

### 🎨 **Diseño y Assets**

- [**Font Awesome**](https://fontawesome.com/) - Iconos increíbles
- [**Google Fonts**](https://fonts.google.com/) - Tipografías hermosas
- [**Unsplash**](https://unsplash.com/) - Imágenes de stock
- [**Shields.io**](https://shields.io/) - Badges para README

### 🙌 **Menciones Especiales**

- A todos los **bomberos** que inspiran este proyecto
- A los **opositores** que luchan por su sueño
- A la **comunidad open source** por compartir conocimiento
- A **Anthropic** por democratizar el acceso a IA avanzada

---

## 📞 Contacto y Soporte

<div align="center">

### 💬 **¿Necesitas Ayuda?**

[![GitHub Issues](https://img.shields.io/badge/Issues-Report_Bug-red?style=for-the-badge&logo=github)](https://github.com/Josojmf/AI_Firefighter/issues)
[![GitHub Discussions](https://img.shields.io/badge/Discussions-Ask_Question-blue?style=for-the-badge&logo=github)](https://github.com/Josojmf/AI_Firefighter/discussions)
[![Email](https://img.shields.io/badge/Email-Contact-green?style=for-the-badge&logo=gmail)](mailto:josojmf@example.com)

### 🌐 **Síguenos**

[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?style=for-the-badge&logo=github)](https://github.com/Josojmf)
[![Twitter](https://img.shields.io/badge/Twitter-Follow-1DA1F2?style=for-the-badge&logo=twitter)](https://twitter.com/josojmf)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/josojmf)

---

### ⭐ **Si te gusta el proyecto, dale una estrella en GitHub**

[![Star History Chart](https://api.star-history.com/svg?repos=Josojmf/AI_Firefighter&type=Date)](https://star-history.com/#Josojmf/AI_Firefighter&Date)

---

<sub>Hecho con ❤️ y mucho ☕ por [Jose Maria Fernandez](https://github.com/Josojmf)</sub>

<sub>© 2025 FirefighterAI. Todos los derechos reservados.</sub>

</div>
# Force build
