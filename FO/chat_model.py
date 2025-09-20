class FirefighterChatModel:
    def __init__(self):
        print("🚒 Iniciando modelo de chat para bomberos...")
        
        self.knowledge_base = {
            "extintor": "Protocolo PASO: Pull (quitar seguro), Aim (apuntar base del fuego), Squeeze (apretar palanca), Sweep (barrer de lado a lado). Tipos: ABC (sólidos/líquidos/eléctricos), CO2 (eléctricos), Agua (sólidos).",
            "incendio": "Procedimiento: Activar alarma, evacuar área, usar extintor si es seguro, llamar al 112. No usar ascensores. Punto de encuentro exterior.",
            "rcp": "Reanimación Cardiopulmonar: 30 compresiones torácicas + 2 ventilaciones. Frecuencia: 100-120/min. Profundidad: 5-6 cm adultos. Usar DEA si disponible.",
            "temperatura fuego": "Temperaturas fuego: Incendio vivienda 600-1000°C, flashover 500-600°C, backdraft 800-1200°C. Equipo protección: hasta 1000°C breve exposición.",
            "fuego electrico": "Fuego eléctrico: Cortar corriente primero. Usar extintor CO2 o polvo ABC. Nunca usar agua. Mantener distancia 1m de equipos energizados.",
            "evacuacion": "Evacuación: Salida ordenada, punto de encuentro designado, no volver atrás, cuenta de personas. Ayudar a personas con movilidad reducida.",
            "material peligroso": "Protocolo: Identificar placas de peligro, mantener distancia, establecer zonas caliente/limpia, esperar especialistas hazmat. No tocar.",
            "protocolo mayday": "MAYDAY 3 veces + LUNAR: Ubicación exacta, Unidad, Nombre, Asignación, Recursos. Repetir cada 30 segundos si no hay respuesta."
        }
        print("✅ Modelo cargado con conocimiento de bomberos")

    def generate_response(self, question):
        """Genera respuesta basada en palabras clave"""
        if not question or len(question.strip()) < 2:
            return "Por favor, haz una pregunta sobre bomberos."
        
        question_lower = question.lower()
        
        # Búsqueda por keywords
        if any(word in question_lower for word in ['extintor', 'fuego', 'incendio']):
            if 'electric' in question_lower:
                return self.knowledge_base['fuego electrico']
            elif 'temperatura' in question_lower or 'grados' in question_lower or 'calor' in question_lower:
                return self.knowledge_base['temperatura fuego']
            else:
                return self.knowledge_base['incendio']
        
        elif any(word in question_lower for word in ['rcp', 'reanimacion', 'corazon', 'paro']):
            return self.knowledge_base['rcp']
        
        elif any(word in question_lower for word in ['evacuar', 'salida', 'emergencia']):
            return self.knowledge_base['evacuacion']
        
        elif any(word in question_lower for word in ['material', 'peligroso', 'quimico']):
            return self.knowledge_base['material peligroso']
        
        elif any(word in question_lower for word in ['mayday', 'ayuda', 'emergencia']):
            return self.knowledge_base['protocolo mayday']
        
        # Respuesta por defecto
        return "Pregunta sobre: extintores, RCP, temperatura de fuego, evacuación o materiales peligrosos."

# Instancia global
chat_model = FirefighterChatModel()