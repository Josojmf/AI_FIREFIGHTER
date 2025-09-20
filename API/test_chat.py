# test_chat.py
from chat_model import FirefighterChatModel

model = FirefighterChatModel()

test_questions = [
    "¿Cómo se usa un extintor?",
    "Qué hacer en caso de incendio",
    "protocolo RCP",
    "materiales peligrosos",
    "ventilación táctica"
]

for question in test_questions:
    response = model.generate_response(question)
    print(f"❓ {question}")
    print(f"✅ {response}")
    print("---")