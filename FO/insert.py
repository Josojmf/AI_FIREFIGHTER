import os
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
import random

# Configuración de MongoDB
client = MongoClient("mongodb+srv://joso:XyGItdDKpWkfJfjT@cluster0.yzzh9ig.mongodb.net/?retryWrites=true&w=majority&appName=Firefighter")
db = client["FIREFIGHTER"]
cards_col = db["leitner_cards"]

# Datos de tarjetas CORREGIDOS (todas con 'front' y 'back')
tarjetas_fuego = [
    {"front": "Punto de inflamación", "back": "Temperatura mínima donde un líquido emite vapores que se inflaman con chispa"},
    {"front": "Tetraedro del fuego", "back": "Combustible + Oxígeno + Calor + Reacción en cadena"},
    {"front": "Clase A fuego", "back": "Materiales sólidos combustibles (madera, papel, tela)"},
    {"front": "Clase B fuego", "back": "Líquidos inflamables (gasolina, aceite, pintura)"},
    {"front": "Clase C fuego", "back": "Equipos eléctricos energizados"},
    {"front": "Clase D fuego", "back": "Metales combustibles (magnesio, titanio, sodio)"},
    {"front": "Clase K fuego", "back": "Aceites y grasas de cocina"},
    {"front": "EXTINTOR ABC", "back": "Polvo químico seco para Clases A, B, C"},
    {"front": "EXTINTOR CO2", "back": "Dióxido de carbono para Clases B y C"},
    {"front": "EXTINTOR AGUA", "back": "Solo para Clase A, nunca para eléctricos"},
    {"front": "PROTOCOLO RACE", "back": "Rescue, Alarm, Contain, Extinguish/Evacuate"},
    {"front": "PROTOCOLO PASS", "back": "Pull, Aim, Squeeze, Sweep (uso extintor)"},
    {"front": "Presión manguera", "back": "3-5 bar para ataque, 7-10 bar para suministro"},
    {"front": "Diámetro manguera", "back": "45mm abastecimiento, 25mm/70mm ataque"},
    {"front": "Boquilla niebla", "back": "Protección térmica, enfriamiento, control gases"},
    {"front": "Boquilla chorro", "back": "Alcance máximo, penetración en materiales"},
    {"front": "Flashover", "back": "Ignición súbita de todos los combustibles en ambiente"},
    {"front": "Backdraft", "back": "Explosión por entrada de oxígeno en espacio confinado"},
    {"front": "BLEVE", "back": "Explosión de recipiente por calentamiento líquido"},
    {"front": "LUNAR protocolo", "back": "Location, Unit, Name, Assignment, Resources"},
    {"front": "MAYDAY protocolo", "back": "Emergencia personal, repetir 3 veces"},
    {"front": "UTM coordenadas", "back": "Sistema coordenadas para ubicación emergencias"},
    {"front": "Triage colores", "back": "Rojo: urgente, Amarillo: espera, Verde: leve, Negro: fallecido"},
    {"front": "RCP ratio", "back": "30 compresiones : 2 ventilaciones"},
    {"front": "DEA uso", "back": "Analizar, Desfibrilar, RCP inmediato después"},
    {"front": "Hidrante clases", "back": "Clase A: ≥1000 L/min, Clase B: 500-1000 L/min, Clase C: <500 L/min"},
    {"front": "Bomba centrífuga", "back": "Principio: fuerza centrífuga, cebado necesario"},
    {"front": "Nivel EPI", "back": "Nivel 1: riesgo bajo, Nivel 2: riesgo medio, Nivel 3: riesgo alto"},
    {"front": "SCBA presión", "back": "200-300 bar presión carga, 50 bar presión alarma"},
    {"front": "SCBA autonomía", "back": "30-60 minutos según consumo y presión"},
    {"front": "Radial patrón", "back": "Comunicación entre bomberos mismo grupo"},
    {"front": "TAC patrón", "back": "Comunicación oficial entre grupos y mando"},
    {"front": "IC mando", "back": "Incident Commander, responsable operación"},
    {"front": "Sectorización", "back": "Dividir incendio en sectores manejables"},
    {"front": "Ventilación vertical", "back": "Aberturas en techo para escape calor/gases"},
    {"front": "Ventilación horizontal", "back": "Aberturas en paredes para control flujos"},
    {"front": "PPV ventilación", "back": "Presión positiva ventiladores, empuja humo"},
    {"front": "NPV ventilación", "back": "Presión negativa, extrae humo"},
    {"front": "Forzamiento puertas", "back": "Irving, Halligan, ariete hidráulico"},
    {"front": "Forzamiento ventanas", "back": "Martillo vidrio, cinta seguridad, gancho"},
    {"front": "Búsqueda primaria", "back": "Rápida, vocal, visual, sistemática"},
    {"front": "Búsqueda secundaria", "back": "Exhaustiva, metódica, marcaje puertas"},
    {"front": "Marcaje puertas", "back": "X: buscada, /: sector, →: dirección, #: víctimas"},
    {"front": "Linea vida", "back": "Cuerda guía para orientación humo cero visibilidad"},
    {"front": "Cuerda nudos", "back": "As de guía, ballestrinque, ocho, pescador"},
    {"front": "Rappel técnicas", "back": "Dülfersitz, descensor ocho, ASAP bloqueador"},
    {"front": "Escalera tipos", "back": "Extension, gancho, tejado, transformable"},
    {"front": "Escalera ángulo", "back": "75° inclinación óptima, 4:1 ratio base-altura"},
    {"front": "Andamio colapsado", "back": "Triángulo vida, no mover, apuntalar"},
    {"front": "VEHÍCULO rescate", "back": "Estabilizar, desconectar batería, acceso víctimas"},
    {"front": "Herramientas hidráulicas", "back": "Cizalla, expansor, ram, combinada"},
    {"front": "Corte vehicular", "back": "Postes A-B-C, techo, panel pies, volante"},
    {"front": "Desencarcelamiento", "back": "Acceso, espacio, liberación, extracción"},
    {"front": "Material peligroso", "back": "Clases 1-9, UN number, placas colores"},
    {"front": "Fórmula caudal", "back": "Q = A × V (Caudal = Área × Velocidad)"},
    {"front": "Fórmula presión", "back": "P = ρ × g × h (Presión = densidad × gravedad × altura)"},
    {"front": "Fórmula potencia", "back": "P = Q × H × ρ × g (Potencia = Caudal × Altura × densidad × gravedad)"},
    {"front": "NRB mascarilla", "back": "Negativa, Regular, Bloqueo - tipos sellado"},
    {"front": "APR respirador", "back": "Air Purifying Respirator, filtros partículas"},
    {"front": "SCBA autonomía", "back": "30-45 min trabajo intenso, 60+ min reposo"},
    {"front": "Check SCBA", "back": "Presión, alarmas, fugas, válvulas, comunicación"},
    {"front": "Donning SCBA", "back": "60 segundos máximo, técnica over-the-head"},
    {"front": "Doffing SCBA", "back": "Controlado, evitar contaminación, revisión"},
    {"front": "Buddy breathing", "back": "Compartir SCBA en emergencia, protocolo estricto"},
    {"front": "Emergency procedures", "back": "Fallo SCBA: retreat, shelter, MAYDAY"}
]

# Usuarios objetivo
usuarios = ["test", "admin", "submit", "joso", "bombero1", "bombero2", "instructor"]

print("🚀 Insertando tarjetas masivas...")

insertadas = 0
errores = 0
now = datetime.now(timezone.utc)

for usuario in usuarios:
    for i in range(150):  # 150 tarjetas por usuario
        # Seleccionar tarjeta aleatoria
        tarjeta_data = random.choice(tarjetas_fuego)
        
        # Box aleatorio entre 1-6
        box = random.randint(1, 6)
        
        # Fecha due aleatoria en los próximos 60 días
        dias_aleatorios = random.randint(0, 60)
        due_date = now + timedelta(days=dias_aleatorios)
        
        # Deck aleatorio
        decks = ["general", "incendios", "rescate", "materiales", "protocolos", "primeros_auxilios", "equipos", "formulas"]
        deck = random.choice(decks)
        
        # Insertar tarjeta
        try:
            cards_col.insert_one({
                "user": usuario,
                "deck": deck,
                "front": f"{tarjeta_data['front']} #{i+1:03d}",
                "back": tarjeta_data['back'],
                "box": box,
                "due": due_date,
                "created_at": now,
                "history": [],
                "last_reviewed": now if random.random() > 0.7 else None
            })
            insertadas += 1
            if insertadas % 100 == 0:
                print(f"📦 {insertadas} tarjetas insertadas...")
                
        except Exception as e:
            errores += 1
            # Ignorar duplicados
            if "duplicate" not in str(e).lower():
                print(f"⚠️ Error en tarjeta {i+1}: {e}")

print(f"\n✅ COMPLETADO: {insertadas} tarjetas insertadas, {errores} errores")
print("📊 Distribución por usuario:")
for usuario in usuarios:
    count = cards_col.count_documents({"user": usuario})
    print(f"   {usuario}: {count} tarjetas")

# Estadísticas adicionales
total_tarjetas = cards_col.count_documents({})
print(f"\n📈 Total en base de datos: {total_tarjetas} tarjetas")