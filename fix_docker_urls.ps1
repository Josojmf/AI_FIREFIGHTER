Write-Host "🔧 Corrigiendo URLs hardcodeadas para Docker..." -ForegroundColor Green

# BACKEND
Write-Host "📦 Corrigiendo Backend..." -ForegroundColor Yellow
(Get-Content API/check_collections.py) -replace 'http://localhost:5000', 'http://firefighter_backend:5000' | Set-Content API/check_collections.py
(Get-Content API/api.py) -replace 'localhost:5000', 'firefighter_backend:5000' | Set-Content API/api.py

# FRONTEND  
Write-Host "📦 Corrigiendo Frontend..." -ForegroundColor Yellow
(Get-Content FO/main.py) -replace 'http://localhost:5000', 'http://firefighter_backend:5000' | Set-Content FO/main.py
(Get-Content FO/leitner.py) -replace 'http://localhost:5000', 'http://firefighter_backend:5000' | Set-Content FO/leitner.py
(Get-Content FO/leitner_sync.py) -replace 'http://localhost:5000', 'http://firefighter_backend:5000' | Set-Content FO/leitner_sync.py

# BACKOFFICE
Write-Host "📦 Corrigiendo BackOffice..." -ForegroundColor Yellow
(Get-Content BO/app/routes/auth.py) -replace 'api_url = "http://localhost:5000"', 'api_url = os.getenv("API_BASE_URL", "http://localhost:5000")' | Set-Content BO/app/routes/auth.py
(Get-Content BO/app.py) -replace 'http://localhost:5000', 'http://firefighter_backend:5000' | Set-Content BO/app.py
(Get-Content BO/serve_waitress.py) -replace 'http://localhost:5000', 'http://firefighter_backend:5000' | Set-Content BO/serve_waitress.py

Write-Host "✅ URLs corregidas. Hacer commit y push para deploy." -ForegroundColor Green