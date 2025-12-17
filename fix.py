# fix.py
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

# REEMPLAZA ESTO CON TU CONNECTION STRING REAL DE MONGODB ATLAS
MONGODB_URI = "mongodb+srv://joso:XyGItdDKpWkfJfjT@cluster0.yzzh9ig.mongodb.net/FIREFIGHTER"

async def migrate_memory_cards():
    try:
        print("🔌 Conectando a MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client["FIREFIGHTER"]
        collection = db["memory_cards"]
        
        # Verificar conexión
        await client.admin.command('ping')
        print("✅ Conexión exitosa a MongoDB")
        
        # Obtener todas las cards
        cards = await collection.find({}).to_list(length=1000)
        
        print(f"🔄 Encontradas {len(cards)} memory cards para migrar...")
        
        migrated = 0
        skipped = 0
        
        for card in cards:
            # Si tiene 'title' pero no 'question', migrar
            if 'title' in card and 'question' not in card:
                update = {
                    '$set': {
                        'question': card.get('title', 'Sin pregunta'),
                        'answer': card.get('content', 'Sin respuesta'),
                        'box': card.get('box', 1),
                        'times_reviewed': card.get('times_reviewed', 0),
                        'times_correct': card.get('times_correct', 0),
                        'times_incorrect': card.get('times_incorrect', 0),
                        'tags': card.get('tags', [])
                    },
                    '$unset': {
                        'title': "",
                        'content': ""
                    }
                }
                
                await collection.update_one(
                    {'_id': card['_id']},
                    update
                )
                migrated += 1
                print(f"✅ Migrada card: {card['_id']} - {card.get('title', '')[:50]}")
            else:
                skipped += 1
                print(f"⏭️  Card ya migrada o sin campos antiguos: {card['_id']}")
        
        print(f"\n{'='*60}")
        print(f"✅ Migración completada!")
        print(f"📊 Cards migradas: {migrated}")
        print(f"⏭️  Cards omitidas: {skipped}")
        print(f"{'='*60}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(migrate_memory_cards())
