# verify_structure.py
import os
import sys

def verify_structure():
    print("🔍 Verificando estructura del Backoffice...")
    
    required_paths = [
        "app/__init__.py",
        "app/models/__init__.py", 
        "app/models/user.py",
        "serve_waitress.py",
        "requirements.txt"
    ]
    
    all_ok = True
    
    for path in required_paths:
        if os.path.exists(path):
            print(f"✅ {path}")
        else:
            print(f"❌ {path} - NO ENCONTRADO")
            all_ok = False
    
    # Verificar contenido de user.py
    if os.path.exists("app/models/user.py"):
        with open("app/models/user.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "BackofficeUser" in content:
                print("✅ BackofficeUser class encontrada en user.py")
            else:
                print("❌ BackofficeUser class NO encontrada en user.py")
                all_ok = False
    
    print(f"\n{'✅ VERIFICACIÓN EXITOSA' if all_ok else '❌ VERIFICACIÓN FALLIDA'}")
    return all_ok

if __name__ == "__main__":
    success = verify_structure()
    sys.exit(0 if success else 1)