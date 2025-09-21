# test_imports.py
print('Testing imports...')

try:
    from app.routes import auth
    print('✓ auth imported')
except Exception as e:
    print(' auth failed:', e)

try:
    from app.routes import dashboard  
    print(' dashboard imported')
except Exception as e:
    print(' dashboard failed:', e)

try:
    from app.routes import users
    print(' users imported')
except Exception as e:
    print(' users failed:', e)

try:
    from app.routes import memory_cards
    print(' memory_cards imported')
except Exception as e:
    print(' memory_cards failed:', e)
