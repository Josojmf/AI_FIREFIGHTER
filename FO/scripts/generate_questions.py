import json

# Aquí se escriben directamente las preguntas, puedes automatizarlo luego con IA
preguntas = [
    {
        "pregunta": "¿Cuál es la presión mínima en cuerpo de bomba según el procedimiento ofensivo?",
        "opciones": ["15 bar", "19 bar", "25 bar"],
        "correcta": "19 bar"
    },
    {
        "pregunta": "¿Qué equipo permanece como SOS durante la exploración con cuerda guía?",
        "opciones": ["Equ1", "Equ2", "Operador ascensor"],
        "correcta": "Equ2"
    },
    # ...
]

with open("data/questions.json", "w", encoding="utf-8") as f:
    json.dump(preguntas, f, indent=2, ensure_ascii=False)
