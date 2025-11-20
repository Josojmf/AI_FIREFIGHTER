#!/usr/bin/env python3
# 🔥 SCRIPT PARA DISTRIBUIR MEMORY CARDS EN TODAS LAS CAJAS LEITNER
# Simula un historial de estudio realista con cards en todas las cajas

import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId

# 📡 CONFIGURACIÓN MONGODB
MONGO_USER = "joso"
MONGO_PASS = "XyGItdDKpWkfJfjT"  
MONGO_CLUSTER = "cluster0.yzzh9ig.mongodb.net"
DB_NAME = "FIREFIGHTER"

# URI de conexión
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/{DB_NAME}?retryWrites=true&w=majority"

# 📚 MEMORY CARDS DISTRIBUIDAS POR CATEGORÍAS Y DIFICULTADES
memory_cards_data = {
    # 🔥 EQUIPAMIENTO - 15 Cards
    "equipamiento": [
        {"title": "¿Qué tipos de mangueras de incendio existen?", "content": "Manguera de 25mm (jardín), 45mm (ataque rápido), 70mm (alimentación) y 100mm (alimentación principal)", "difficulty": "easy"},
        {"title": "¿Cuáles son los componentes básicos de una BIE?", "content": "Boca de Incendio Equipada: manguera semirígida de 25mm, lanza/boquilla, armario/soporte y válvula de corte", "difficulty": "medium"},
        {"title": "¿Qué es un monitor de incendios?", "content": "Dispositivo fijo o móvil que permite dirigir grandes volúmenes de agua o espuma desde una posición segura", "difficulty": "medium"},
        {"title": "¿Cuántos tipos de escalas manuales existen?", "content": "Escala simple, escala de ganchos, escala telescópica, escala de corredera y escala articulada", "difficulty": "easy"},
        {"title": "¿Qué herramientas de ventilación forzada se usan?", "content": "Ventiladores eléctricos, ventiladores de gasolina, extractores de humo y ventiladores de presión positiva", "difficulty": "medium"},
        {"title": "¿Qué elementos lleva un traje de aproximación?", "content": "Chaquetón y pantalón aluminizados, casco especial, guantes aluminizados, botas de seguridad y ERA", "difficulty": "hard"},
        {"title": "¿Qué es una bomba centrífuga?", "content": "Bomba que impulsa agua mediante fuerza centrífuga, usada en autobombas para crear presión en las líneas", "difficulty": "medium"},
        {"title": "¿Cuáles son los tipos de generadores en bomberos?", "content": "Generador eléctrico portátil (2-5kW), grupo electrógeno móvil (10-20kW) y generador de vehículo (5-15kW)", "difficulty": "medium"},
        {"title": "¿Qué herramientas de corte usan los bomberos?", "content": "Sierra circular, radial, motosierra, cizalla hidráulica, separador hidráulico y cortadora de plasma", "difficulty": "easy"},
        {"title": "¿Qué es un sistema de rescate vertical?", "content": "Equipo de cuerdas, poleas, anclajes y arneses para rescate en altura y espacios confinados", "difficulty": "hard"},
        {"title": "¿Cuál es la diferencia entre autobomba rural y urbana?", "content": "Rural: mayor capacidad de agua (4000-6000L), bombas de mayor caudal. Urbana: más equipo técnico, acceso estrecho", "difficulty": "medium"},
        {"title": "¿Qué es un sistema de espuma AFFF?", "content": "Aqueous Film Forming Foam - forma película acuosa sobre líquidos inflamables impidiendo evaporación", "difficulty": "hard"},
        {"title": "¿Cuándo se usa una manta ignífuga?", "content": "Para sofocar fuegos pequeños clase A y B, proteger personas en evacuación y aislar materiales inflamables", "difficulty": "easy"},
        {"title": "¿Qué es un sistema de presión constante?", "content": "Mantiene presión estable en red de mangueras independientemente del caudal usando reguladores automáticos", "difficulty": "hard"},
        {"title": "¿Cuáles son los tipos de boquillas contra incendios?", "content": "Boquilla recta, regulable, niebla, espuma, monitor fijo y lanza de penetración", "difficulty": "medium"}
    ],
    
    # 🚨 PROCEDIMIENTOS - 15 Cards  
    "procedimientos": [
        {"title": "¿Cuáles son las fases de un incendio estructural?", "content": "Iniciación, crecimiento, desarrollo pleno (flashover), decaimiento y extinción", "difficulty": "medium"},
        {"title": "¿Qué es el ataque directo en extinción?", "content": "Aplicación de agua directamente sobre la base de las llamas para enfriar el combustible", "difficulty": "easy"},
        {"title": "¿Cómo se realiza una ventilación horizontal?", "content": "Abrir puertas y ventanas en lado opuesto al viento para crear corriente de aire controlada", "difficulty": "medium"},
        {"title": "¿Qué es la regla del 2 dentro - 2 fuera?", "content": "Por cada 2 bomberos que entran al incendio, deben quedar 2 fuera listos para rescate inmediato", "difficulty": "medium"},
        {"title": "¿Cuándo se usa agua nebulizada?", "content": "Para incendios clase A en espacios cerrados, reduce temperatura y desplaza oxígeno", "difficulty": "hard"},
        {"title": "¿Qué es un ataque indirecto?", "content": "Aplicar agua en forma de niebla para generar vapor y desplazar oxígeno sin acercarse al fuego", "difficulty": "medium"},
        {"title": "¿Cómo se realiza una búsqueda primaria?", "content": "Búsqueda rápida de víctimas en áreas más probables: cerca de puertas, ventanas y pasillos principales", "difficulty": "medium"},
        {"title": "¿Qué es la ventilación vertical?", "content": "Crear aberturas en el techo para permitir que calor y humo escapen hacia arriba naturalmente", "difficulty": "medium"},
        {"title": "¿Cuándo se usa espuma AFFF?", "content": "Para incendios de líquidos inflamables (Clase B), forma película acuosa que sella vapores", "difficulty": "hard"},
        {"title": "¿Qué es el overhaul?", "content": "Revisión post-incendio para eliminar focos ocultos y evitar reignición", "difficulty": "easy"},
        {"title": "¿Cómo se establece un perímetro de seguridad?", "content": "Zona de exclusión basada en tipo de emergencia: 150m explosivos, 100m químicos, 50m estructural", "difficulty": "hard"},
        {"title": "¿Qué es el procedimiento de entrada forzada?", "content": "Técnicas para abrir puertas/ventanas: palanca, hacha, sierra, gato hidráulico respetando integridad estructural", "difficulty": "medium"},
        {"title": "¿Cuándo aplicar técnica de supresión por sofocación?", "content": "Fuegos clase B en espacios cerrados usando CO2, arena o mantas, eliminando oxígeno del triángulo del fuego", "difficulty": "medium"},
        {"title": "¿Cómo coordinar ataque desde múltiples frentes?", "content": "Asignar sectores, establecer comunicación directa, coordinar tiempos y evitar interferencias entre equipos", "difficulty": "hard"},
        {"title": "¿Qué es la técnica de ataque transitional?", "content": "Combinar ataque exterior (enfriamiento) seguido de interior (supresión) para reducir temperatura antes de entrada", "difficulty": "hard"}
    ],
    
    # ⚡ SEGURIDAD - 12 Cards
    "seguridad": [
        {"title": "¿Cuáles son las 18 situaciones de WATCH OUT?", "content": "Incluyen: fuego no cartografiado, clima extremo, sin comunicación, líneas de escape inseguras, etc.", "difficulty": "hard"},
        {"title": "¿Qué significa LUNAR en emergencias?", "content": "Localización, Unidad, Nombre, Asignación, Recursos - protocolo para MAYDAY", "difficulty": "medium"},
        {"title": "¿Cuándo usar detectores de gases?", "content": "En espacios confinados, fugas químicas, post-incendio y antes de entrar a sótanos", "difficulty": "medium"},
        {"title": "¿Qué es un punto de no retorno?", "content": "Momento en que el bombero debe retirarse para conservar aire suficiente para salir", "difficulty": "hard"},
        {"title": "¿Cuáles son los EPI básicos estructurales?", "content": "Casco, chaquetón, pantalón, botas, guantes, capucha, cinturón y ERA", "difficulty": "easy"},
        {"title": "¿Qué es la regla de los 2/3 de aire?", "content": "Usar máximo 2/3 del aire para entrar, reservar 1/3 para salida de emergencia", "difficulty": "medium"},
        {"title": "¿Qué indica una alarma de evacuación general?", "content": "Señal continua que indica retirada inmediata de todos los bomberos del área de peligro", "difficulty": "easy"},
        {"title": "¿Cuándo es obligatorio el uso de cuerdas de vida?", "content": "En edificios >2 plantas, visibilidad <1m, trabajos en altura y espacios confinados", "difficulty": "medium"},
        {"title": "¿Qué es el protocolo PAR (Personnel Accountability Report)?", "content": "Sistema de control de personal que verifica ubicación y estado de todos los bomberos en emergencia", "difficulty": "hard"},
        {"title": "¿Cuándo activar el protocolo de bombero perdido?", "content": "Falta de comunicación >2min, no responde a llamadas, desviación de asignación sin avisar", "difficulty": "hard"},
        {"title": "¿Qué distancias de seguridad mantener con tendidos eléctricos?", "content": "Baja tensión: 3m, Media tensión: 5m, Alta tensión: 8m, Extra alta: 15m", "difficulty": "medium"},
        {"title": "¿Cómo actuar ante colapso estructural inminente?", "content": "Evacuación inmediata, señal de alarma general, establecer perímetro amplio, no reentrada hasta evaluación", "difficulty": "hard"}
    ],
    
    # 🧯 QUÍMICA DEL FUEGO - 10 Cards
    "quimica": [
        {"title": "¿Cuáles son los productos de la combustión?", "content": "Calor, luz, gases (CO, CO2, HCN), vapores tóxicos y partículas en suspensión", "difficulty": "medium"},
        {"title": "¿Qué es la temperatura de autoignición?", "content": "Temperatura mínima a la que una sustancia se inflama espontáneamente sin fuente de ignición", "difficulty": "hard"},
        {"title": "¿Qué diferencia hay entre punto de inflamación y combustión?", "content": "Inflamación: vapores arden momentáneamente. Combustión: arden de forma continua", "difficulty": "medium"},
        {"title": "¿Qué es un backdraft?", "content": "Explosión causada por entrada súbita de oxígeno en espacio con combustión incompleta", "difficulty": "hard"},
        {"title": "¿Cuáles son los métodos de transmisión del calor?", "content": "Conducción (contacto directo), convección (fluidos) y radiación (ondas electromagnéticas)", "difficulty": "medium"},
        {"title": "¿Qué es el flashover?", "content": "Ignición súbita y simultánea de todos los materiales combustibles de una habitación", "difficulty": "hard"},
        {"title": "¿Cuáles son las clases de fuego según combustible?", "content": "Clase A: sólidos, Clase B: líquidos, Clase C: gases, Clase D: metales, Clase K: aceites cocina", "difficulty": "easy"},
        {"title": "¿Qué es la pirolisis en combustión?", "content": "Descomposición química de materiales orgánicos por calor sin oxígeno, generando gases inflamables", "difficulty": "hard"},
        {"title": "¿Cuándo ocurre un rollover?", "content": "Ignición de gases acumulados en techo antes del flashover, indicador de condiciones peligrosas", "difficulty": "medium"},
        {"title": "¿Qué factores afectan la velocidad de combustión?", "content": "Superficie expuesta, ventilación, humedad, temperatura ambiente, tipo de combustible", "difficulty": "medium"}
    ],
    
    # 🏥 RESCATE - 12 Cards
    "rescate": [
        {"title": "¿Cuáles son las fases de un rescate vehicular?", "content": "Reconocimiento, estabilización, acceso, desencarcelación, atención médica y evacuación", "difficulty": "medium"},
        {"title": "¿Qué es el método SALT en triaje?", "content": "Sort, Assess, Lifesaving interventions, Treatment/Transport - clasificación de múltiples víctimas", "difficulty": "hard"},
        {"title": "¿Cómo se realiza un rescate en altura?", "content": "Evaluación, anclajes seguros, descenso controlado con cuerdas y sistemas de poleas", "difficulty": "medium"},
        {"title": "¿Qué es la técnica START?", "content": "Simple Triage And Rapid Treatment - triaje rápido basado en respiración, pulso y nivel conciencia", "difficulty": "medium"},
        {"title": "¿Cuándo se usa el método de carga y arrastre?", "content": "Para evacuar víctimas inconscientes de espacios reducidos o cuando no hay camilla", "difficulty": "easy"},
        {"title": "¿Qué elementos necesita un rescate acuático?", "content": "Trajes de neopreno, cuerdas flotantes, salvavidas, bote neumático y equipo de buceo", "difficulty": "medium"},
        {"title": "¿Qué es el rescate en espacios confinados?", "content": "Operación en espacios con entrada limitada, atmósfera peligrosa o riesgo de asfixia", "difficulty": "hard"},
        {"title": "¿Cómo se estabiliza un vehículo accidentado?", "content": "Calzos en ruedas, puntales telescópicos, cadenas/eslingas y corte de batería", "difficulty": "medium"},
        {"title": "¿Cuáles son las técnicas de apertura de vehículos?", "content": "Separación de puertas, corte de montantes, desplazamiento de techo, creación de accesos", "difficulty": "hard"},
        {"title": "¿Qué protocolo seguir en rescate de montaña?", "content": "Evaluación meteorológica, establecer CB, equipos especializados, evacuación por helicóptero si precisa", "difficulty": "hard"},
        {"title": "¿Cómo realizar RCP en víctima de incendio?", "content": "Vía aérea con hiperextensión cervical, ventilación con O2 alto flujo, compresiones profundas", "difficulty": "medium"},
        {"title": "¿Qué es el síndrome de aplastamiento?", "content": "Liberación de toxinas musculares tras compresión prolongada, requiere fluidoterapia antes de liberar", "difficulty": "hard"}
    ]
}

def calculate_leitner_distribution():
    """Calcular distribución realista en cajas Leitner"""
    # Distribución basada en curva de aprendizaje real:
    # Más cards en cajas bajas (material reciente/difícil)
    # Menos cards en cajas altas (material dominado)
    
    distribution = {
        1: 0.35,  # 35% - Material nuevo o fallado
        2: 0.25,  # 25% - Primera repetición exitosa  
        3: 0.20,  # 20% - Material en consolidación
        4: 0.12,  # 12% - Material conocido
        5: 0.05,  # 5% - Material bien dominado
        6: 0.03   # 3% - Material perfectamente aprendido
    }
    return distribution

def get_due_date(box):
    """Calcular fecha de vencimiento según caja"""
    intervals = {
        1: 0,     # Hoy (vencidas)
        2: 1,     # 1 día
        3: 3,     # 3 días  
        4: 7,     # 7 días
        5: 14,    # 14 días
        6: 30     # 30 días
    }
    
    base_date = datetime.utcnow()
    
    # Para crear variación realista
    if box == 1:
        # Algunas vencidas hoy, otras hace 1-2 días
        days_offset = random.choice([-2, -1, 0, 0, 0])  # Mayor probabilidad de hoy
    else:
        # Fechas futuras con ligera variación
        days_offset = intervals[box] + random.randint(-1, 2)
        
    return base_date + timedelta(days=days_offset)

def create_memory_cards():
    """Crear e insertar memory cards con distribución Leitner realista"""
    
    print("🔥 FIREFIGHTER AI - LEITNER DISTRIBUTION SETUP")
    print("=" * 60)
    
    try:
        # Conectar a MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        client.server_info()
        print("✅ Conectado a MongoDB Atlas exitosamente")
        
        db = client[DB_NAME]
        leitner_cards = db["leitner_cards"]
        
        # Limpiar cards existentes del admin (opcional)
        print("\n🧹 Limpiando cards existentes...")
        deleted = leitner_cards.delete_many({"user": "admin"})
        print(f"   🗑️ Eliminadas: {deleted.deleted_count} cards anteriores")
        
        # Preparar todas las cards
        all_cards = []
        category_counts = {}
        
        for category, cards in memory_cards_data.items():
            category_counts[category] = len(cards)
            for card_data in cards:
                all_cards.append({
                    "category": category,
                    "title": card_data["title"],
                    "content": card_data["content"], 
                    "difficulty": card_data["difficulty"]
                })
        
        # Mostrar resumen
        total_cards = len(all_cards)
        print(f"\n📊 RESUMEN DE CARDS A CREAR:")
        for cat, count in category_counts.items():
            print(f"   🔸 {cat}: {count} cards")
        print(f"   📋 TOTAL: {total_cards} cards")
        
        # Calcular distribución por cajas
        distribution = calculate_leitner_distribution()
        print(f"\n📈 DISTRIBUCIÓN LEITNER:")
        for box, percentage in distribution.items():
            count = int(total_cards * percentage)
            interval = ["Hoy", "1 día", "3 días", "7 días", "14 días", "30 días"][box-1]
            print(f"   📦 Caja {box} ({interval}): {count} cards ({percentage*100:.0f}%)")
        
        # Barajar cards para distribución aleatoria
        random.shuffle(all_cards)
        
        # Asignar cajas según distribución
        cards_with_boxes = []
        start_idx = 0
        
        for box, percentage in distribution.items():
            count = int(total_cards * percentage)
            end_idx = start_idx + count
            
            for i in range(start_idx, min(end_idx, total_cards)):
                card = all_cards[i]
                
                # Crear documento Leitner
                doc = {
                    "_id": ObjectId(),
                    "user": "admin",
                    "deck": card["category"], 
                    "front": card["title"],
                    "back": card["content"],
                    "box": box,
                    "due": get_due_date(box),
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    "history": [
                        {
                            "date": datetime.utcnow() - timedelta(days=random.randint(1, 15)),
                            "correct": random.choice([True, False]),
                            "response_time": random.randint(3, 45)
                        }
                    ] if box > 1 else []  # Solo historial si no es caja 1
                }
                
                cards_with_boxes.append(doc)
            
            start_idx = end_idx
        
        # Manejar cards restantes (por redondeo)
        for i in range(start_idx, total_cards):
            card = all_cards[i]
            doc = {
                "_id": ObjectId(),
                "user": "admin", 
                "deck": card["category"],
                "front": card["title"],
                "back": card["content"],
                "box": 1,  # Caja por defecto
                "due": get_due_date(1),
                "created_at": datetime.utcnow(),
                "history": []
            }
            cards_with_boxes.append(doc)
        
        # Insertar en MongoDB
        print(f"\n📝 Insertando {len(cards_with_boxes)} memory cards...")
        result = leitner_cards.insert_many(cards_with_boxes)
        
        if result.inserted_ids:
            print(f"✅ {len(result.inserted_ids)} cards insertadas exitosamente")
            
            # Mostrar estadísticas finales por caja
            print(f"\n📊 ESTADÍSTICAS FINALES POR CAJA:")
            for box in range(1, 7):
                count = leitner_cards.count_documents({"user": "admin", "box": box})
                vencidas = leitner_cards.count_documents({
                    "user": "admin", 
                    "box": box, 
                    "due": {"$lte": datetime.utcnow()}
                })
                interval = ["Hoy", "1 día", "3 días", "7 días", "14 días", "30 días"][box-1]
                print(f"   📦 Caja {box} ({interval}): {count} total, {vencidas} vencidas")
            
            print(f"\n🎉 ¡DISTRIBUCIÓN LEITNER COMPLETADA!")
            print(f"🔥 Ahora tienes un sistema realista con cards en todas las cajas")
            print(f"📚 {total_cards} cards distribuidas en 5 categorías")
            
        else:
            print("❌ Error al insertar cards")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    create_memory_cards()