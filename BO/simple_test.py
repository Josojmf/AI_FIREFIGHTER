# simple_test.py
print('Testing simple import...')
try:
    import requests
    print('requests OK')
except Exception as e:
    print(f'requests failed: {e}')

try:
    from config import Config
    print('config OK') 
except Exception as e:
    print(f'config failed: {e}')

try:
    from flask import Blueprint
    print('flask Blueprint OK')
except Exception as e:
    print(f'flask Blueprint failed: {e}')
