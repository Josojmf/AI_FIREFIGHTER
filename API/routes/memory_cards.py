"""
Memory Cards Routes - Leitner System endpoints
=============================================
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from uuid import uuid4

from models.card_models import (
    MemoryCardCreate,
    MemoryCardUpdate,
    MemoryCardResponse,
    MemoryCardReview,
    BulkMemoryCardCreate
)
# Importar las dependencias de auth de api.py
from api import require_user, require_admin
# Importar Database
from database import Database

router = APIRouter(tags=["memory-cards"])

def get_memory_cards_collection():
    """Obtener la colección de memory cards con verificación de conexión"""
    if not Database.is_connected():
        raise HTTPException(
            status_code=503, 
            detail="Servicio de base de datos no disponible. Por favor, intente más tarde."
        )
    
    if Database.memory_cards is None:
        # Intentar inicializar la colección
        if Database.db:
            Database.memory_cards = Database.db["memory_cards"]
        else:
            raise HTTPException(
                status_code=503, 
                detail="Colección de memory cards no disponible"
            )
    
    return Database.memory_cards


@router.get("/memory-cards")
async def list_memory_cards(
    user_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    box: Optional[int] = Query(None),
    user_data: Dict = Depends(require_user)
):
    """Obtener memory cards con filtros"""
    try:
        # Asegurar conexión
        await Database.ensure_connection()
        
        memory_cards = get_memory_cards_collection()
        
        query = {}
        
        # Si no es admin, solo sus cartas
        if user_data.get('role') != 'admin':
            query["created_by"] = user_data["username"]
        elif user_id:
            query["created_by"] = user_id
            
        if category:
            query["category"] = category
        if box:
            query["box"] = box
        
        print(f"🔍 Buscando cards con query: {query}")
        
        cards_cursor = memory_cards.find(query)
        cards_list = await cards_cursor.to_list(length=1000)
        
        # Convert ObjectId to string
        for card in cards_list:
            card['id'] = str(card['_id']) if isinstance(card['_id'], ObjectId) else card['_id']
            card.pop('_id', None)
        
        print(f"✅ Encontradas {len(cards_list)} cards para usuario: {user_data['username']}")
        
        return {"ok": True, "cards": cards_list}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo cards: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error obteniendo memory cards: {str(e)}"
        )


@router.post("/memory-cards")
async def create_memory_card(
    card: MemoryCardCreate,
    user_data: Dict = Depends(require_user)
):
    """Crear nueva memory card"""
    try:
        # Asegurar conexión
        await Database.ensure_connection()
        
        memory_cards = get_memory_cards_collection()
        
        # Calcular next_review basado en el box (sistema Leitner)
        review_intervals = {
            1: timedelta(hours=4),   # Box 1: 4 horas
            2: timedelta(days=1),    # Box 2: 1 día
            3: timedelta(days=3),    # Box 3: 3 días
            4: timedelta(days=7),    # Box 4: 1 semana
            5: timedelta(days=14)    # Box 5: 2 semanas
        }
        
        next_review = datetime.utcnow() + review_intervals.get(card.box, timedelta(days=1))
        
        card_doc = {
            "_id": str(uuid4()),
            "question": card.question,
            "answer": card.answer,
            "category": card.category,
            "difficulty": card.difficulty,
            "tags": card.tags if card.tags else [],
            "box": card.box,
            "times_reviewed": 0,
            "times_correct": 0,
            "times_incorrect": 0,
            "last_reviewed": None,
            "next_review": next_review,
            "created_by": user_data["username"],
            "created_at": datetime.utcnow(),
            "updated_at": None
        }
        
        result = await memory_cards.insert_one(card_doc)
        
        card_doc['id'] = card_doc.pop('_id')
        
        print(f"✅ Card creada: {card_doc['id']} para usuario: {user_data['username']}")
        
        return {"ok": True, "card": card_doc}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creando card: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error creando memory card: {str(e)}"
        )

# ... [Mantener el resto de las funciones exactamente igual que en la versión anterior] ...
# Solo asegúrate de importar las dependencias de auth desde api.py

@router.post("/memory-cards/bulk")
async def create_bulk_memory_cards(
    bulk: BulkMemoryCardCreate,
    user_data: Dict = Depends(require_user)
):
    """Crear múltiples memory cards"""
    try:
        # Asegurar conexión
        await Database.ensure_connection()
        
        memory_cards = get_memory_cards_collection()
        
        cards_docs = []
        
        # Calcular next_review basado en el box (sistema Leitner)
        review_intervals = {
            1: timedelta(hours=4),   # Box 1: 4 horas
            2: timedelta(days=1),    # Box 2: 1 día
            3: timedelta(days=3),    # Box 3: 3 días
            4: timedelta(days=7),    # Box 4: 1 semana
            5: timedelta(days=14)    # Box 5: 2 semanas
        }
        
        for card in bulk.cards:
            next_review = datetime.utcnow() + review_intervals.get(card.box, timedelta(days=1))
            
            card_doc = {
                "_id": str(uuid4()),
                "question": card.question,
                "answer": card.answer,
                "category": card.category,
                "difficulty": card.difficulty,
                "tags": card.tags if card.tags else [],
                "box": card.box,
                "times_reviewed": 0,
                "times_correct": 0,
                "times_incorrect": 0,
                "last_reviewed": None,
                "next_review": next_review,
                "created_by": user_data["username"],
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
            cards_docs.append(card_doc)
        
        if cards_docs:
            result = await memory_cards.insert_many(cards_docs)
            print(f"✅ {len(cards_docs)} cards creadas para usuario: {user_data['username']}")
            
        return {
            "ok": True,
            "detail": f"{len(cards_docs)} cards creadas exitosamente",
            "count": len(cards_docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creando bulk cards: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error creando memory cards: {str(e)}"
        )


@router.get("/memory-cards/{card_id}")
async def get_memory_card(card_id: str, user_data: Dict = Depends(require_user)):
    """Obtener detalle de un memory card"""
    try:
        # Asegurar conexión
        await Database.ensure_connection()
        
        memory_cards = get_memory_cards_collection()
        
        # Intentar convertir a ObjectId o usar como string
        try:
            object_id = ObjectId(card_id)
        except:
            object_id = card_id
        
        card = await memory_cards.find_one({"_id": object_id})
        if not card:
            raise HTTPException(status_code=404, detail="Card no encontrado")
        
        # Verificar permisos
        if user_data.get('role') != 'admin' and card.get("created_by") != user_data["username"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        card['id'] = str(card['_id']) if isinstance(card['_id'], ObjectId) else card['_id']
        card.pop('_id', None)
        
        return {"ok": True, "card": card}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo card: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error obteniendo memory card: {str(e)}"
        )


@router.put("/memory-cards/{card_id}")
async def update_memory_card(
    card_id: str, 
    updates: MemoryCardUpdate,
    user_data: Dict = Depends(require_user)
):
    """Actualizar memory card"""
    try:
        # Asegurar conexión
        await Database.ensure_connection()
        
        memory_cards = get_memory_cards_collection()
        
        # Intentar convertir a ObjectId o usar como string
        try:
            object_id = ObjectId(card_id)
        except:
            object_id = card_id
        
        # Buscar card
        card = await memory_cards.find_one({"_id": object_id})
        if not card:
            raise HTTPException(status_code=404, detail="Card no encontrado")
        
        # Verificar permisos
        if user_data.get('role') != 'admin' and card.get("created_by") != user_data["username"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Preparar updates
        update_doc = {"$set": {"updated_at": datetime.utcnow()}}
        
        if updates.question is not None:
            update_doc["$set"]["question"] = updates.question
        if updates.answer is not None:
            update_doc["$set"]["answer"] = updates.answer
        if updates.box is not None:
            update_doc["$set"]["box"] = updates.box
            # Actualizar next_review según el nuevo box
            review_intervals = {
                1: timedelta(hours=4),
                2: timedelta(days=1),
                3: timedelta(days=3),
                4: timedelta(days=7),
                5: timedelta(days=14)
            }
            next_review = datetime.utcnow() + review_intervals.get(updates.box, timedelta(days=1))
            update_doc["$set"]["next_review"] = next_review
        if updates.difficulty is not None:
            update_doc["$set"]["difficulty"] = updates.difficulty
        if updates.category is not None:
            update_doc["$set"]["category"] = updates.category
        if updates.tags is not None:
            update_doc["$set"]["tags"] = updates.tags
        
        # Actualizar
        result = await memory_cards.update_one(
            {"_id": object_id}, 
            update_doc
        )
        
        if result.modified_count == 0:
            print(f"⚠️  No se modificó ningún documento para card_id: {card_id}")
        
        print(f"✅ Card actualizada: {card_id} por usuario: {user_data['username']}")
        
        return {"ok": True, "detail": "Memory card actualizado"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando card: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error actualizando memory card: {str(e)}"
        )


@router.delete("/memory-cards/{card_id}")
async def delete_memory_card(card_id: str, user_data: Dict = Depends(require_user)):
    """Eliminar memory card"""
    try:
        # Asegurar conexión
        await Database.ensure_connection()
        
        memory_cards = get_memory_cards_collection()
        
        # Intentar convertir a ObjectId o usar como string
        try:
            object_id = ObjectId(card_id)
        except:
            object_id = card_id
        
        # Buscar card
        card = await memory_cards.find_one({"_id": object_id})
        if not card:
            raise HTTPException(status_code=404, detail="Card no encontrado")
        
        # Verificar permisos (propietario o admin)
        if user_data.get('role') != 'admin' and card.get("created_by") != user_data["username"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        result = await memory_cards.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Card no encontrado")
        
        print(f"✅ Card eliminada: {card_id} por usuario: {user_data['username']}")
        
        return {"ok": True, "detail": "Memory card eliminado"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error eliminando card: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error eliminando memory card: {str(e)}"
        )


@router.post("/memory-cards/{card_id}/review")
async def review_memory_card(
    card_id: str,
    review: MemoryCardReview,
    user_data: Dict = Depends(require_user)
):
    """Registrar review de una card"""
    try:
        # Asegurar conexión
        await Database.ensure_connection()
        
        memory_cards = get_memory_cards_collection()
        
        # Intentar convertir a ObjectId o usar como string
        try:
            object_id = ObjectId(card_id)
        except:
            object_id = card_id
        
        # Buscar card
        card = await memory_cards.find_one({"_id": object_id})
        if not card:
            raise HTTPException(status_code=404, detail="Card no encontrado")
        
        # Verificar permisos
        if user_data.get('role') != 'admin' and card.get("created_by") != user_data["username"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Actualizar estadísticas
        update_doc = {
            "$inc": {
                "times_reviewed": 1
            },
            "$set": {
                "last_reviewed": datetime.utcnow()
            }
        }
        
        # Añadir incremento para correct/incorrect
        if review.correct:
            update_doc["$inc"]["times_correct"] = 1
        else:
            update_doc["$inc"]["times_incorrect"] = 1
        
        # Mover box según Leitner y calcular nuevo next_review
        current_box = card.get("box", 1)
        if review.correct:
            new_box = min(current_box + 1, 5)  # Max box 5
        else:
            new_box = max(current_box - 1, 1)  # Min box 1
        
        # Calcular nuevo next_review basado en el nuevo box
        review_intervals = {
            1: timedelta(hours=4),
            2: timedelta(days=1),
            3: timedelta(days=3),
            4: timedelta(days=7),
            5: timedelta(days=14)
        }
        next_review = datetime.utcnow() + review_intervals.get(new_box, timedelta(days=1))
        
        update_doc["$set"]["box"] = new_box
        update_doc["$set"]["next_review"] = next_review
        
        result = await memory_cards.update_one(
            {"_id": object_id},
            update_doc
        )
        
        if result.modified_count == 0:
            print(f"⚠️  No se pudo actualizar review para card_id: {card_id}")
        
        print(f"✅ Review registrada para card: {card_id}, nuevo box: {new_box}, correcto: {review.correct}")
        
        return {
            "ok": True,
            "detail": "Review registrada",
            "new_box": new_box,
            "correct": review.correct,
            "next_review": next_review
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en review: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error registrando review: {str(e)}"
        )


@router.get("/memory-cards/stats")
async def get_memory_cards_stats(user_data: Dict = Depends(require_user)):
    """Obtener estadísticas de memory cards"""
    try:
        # Asegurar conexión
        await Database.ensure_connection()
        
        memory_cards = get_memory_cards_collection()
        
        query = {}
        if user_data.get('role') != 'admin':
            query["created_by"] = user_data["username"]
        
        cards_cursor = memory_cards.find(query)
        cards = await cards_cursor.to_list(length=10000)
        
        total_cards = len(cards)
        by_box = {}
        by_category = {}
        by_difficulty = {}
        total_reviews = 0
        total_correct = 0
        
        for card in cards:
            # By box
            box = str(card.get("box", 1))
            by_box[box] = by_box.get(box, 0) + 1
            
            # By category
            category = card.get("category", "General")
            by_category[category] = by_category.get(category, 0) + 1
            
            # By difficulty
            difficulty = card.get("difficulty", "medium")
            by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1
            
            # Reviews
            total_reviews += card.get("times_reviewed", 0)
            total_correct += card.get("times_correct", 0)
        
        accuracy_rate = (total_correct / total_reviews * 100) if total_reviews > 0 else 0
        
        print(f"📊 Stats para {user_data['username']}: {total_cards} cards, {total_reviews} reviews")
        
        return {
            "ok": True,
            "stats": {
                "total_cards": total_cards,
                "by_box": by_box,
                "by_category": by_category,
                "by_difficulty": by_difficulty,
                "total_reviews": total_reviews,
                "accuracy_rate": round(accuracy_rate, 2)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo stats: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.get("/memory-cards/due")
async def get_due_memory_cards(user_data: Dict = Depends(require_user)):
    """Obtener cards pendientes de review"""
    try:
        # Asegurar conexión
        await Database.ensure_connection()
        
        memory_cards = get_memory_cards_collection()
        
        query = {
            "created_by": user_data["username"],
            "$or": [
                {"last_reviewed": None},
                {"next_review": {"$lte": datetime.utcnow()}}
            ]
        }
        
        cards_cursor = memory_cards.find(query).sort("box", 1).limit(50)
        cards_list = await cards_cursor.to_list(length=50)
        
        # Convert ObjectId to string
        for card in cards_list:
            card['id'] = str(card['_id']) if isinstance(card['_id'], ObjectId) else card['_id']
            card.pop('_id', None)
        
        print(f"📅 Cards pendientes para {user_data['username']}: {len(cards_list)}")
        
        return {
            "ok": True,
            "cards": cards_list,
            "count": len(cards_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo cards due: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error obteniendo cards pendientes: {str(e)}"
        )