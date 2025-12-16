"""
Memory Cards Routes - Leitner System endpoints
=============================================
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from uuid import uuid4

from models.card_models import (
    MemoryCardCreate,
    MemoryCardUpdate,
    MemoryCardResponse,
    MemoryCardReview,
    BulkMemoryCardCreate
)
from dependencies.auth import require_user, require_admin
from database import Database


router = APIRouter(tags=["memory-cards"])
db = Database()


@router.get("/memory-cards")
async def list_memory_cards(
    user_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    box: Optional[int] = Query(None),
    user_data: Dict = Depends(require_user)
):
    """Obtener memory cards con filtros"""
    try:
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
        
        cards_cursor = db.memory_cards.find(query)
        cards_list = await cards_cursor.to_list(length=1000)
        
        # Convert ObjectId to string
        for card in cards_list:
            card['id'] = str(card['_id']) if isinstance(card['_id'], ObjectId) else card['_id']
            card.pop('_id', None)
        
        return {"ok": True, "cards": cards_list}
        
    except Exception as e:
        print(f"❌ Error obteniendo cards: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo memory cards")


@router.post("/memory-cards")
async def create_memory_card(
    card: MemoryCardCreate,
    user_data: Dict = Depends(require_user)
):
    """Crear nueva memory card"""
    try:
        card_doc = {
            "_id": str(uuid4()),
            "question": card.question,
            "answer": card.answer,
            "category": card.category,
            "difficulty": card.difficulty,
            "tags": card.tags,
            "box": card.box,
            "times_reviewed": 0,
            "times_correct": 0,
            "times_incorrect": 0,
            "last_reviewed": None,
            "next_review": None,
            "created_by": user_data["username"],
            "created_at": datetime.utcnow(),
            "updated_at": None
        }
        
        await db.memory_cards.insert_one(card_doc)
        
        card_doc['id'] = card_doc.pop('_id')
        
        return {"ok": True, "card": card_doc}
        
    except Exception as e:
        print(f"❌ Error creando card: {e}")
        raise HTTPException(status_code=500, detail="Error creando memory card")


@router.post("/memory-cards/bulk")
async def create_bulk_memory_cards(
    bulk: BulkMemoryCardCreate,
    user_data: Dict = Depends(require_user)
):
    """Crear múltiples memory cards"""
    try:
        cards_docs = []
        
        for card in bulk.cards:
            card_doc = {
                "_id": str(uuid4()),
                "question": card.question,
                "answer": card.answer,
                "category": card.category,
                "difficulty": card.difficulty,
                "tags": card.tags,
                "box": card.box,
                "times_reviewed": 0,
                "times_correct": 0,
                "times_incorrect": 0,
                "last_reviewed": None,
                "next_review": None,
                "created_by": user_data["username"],
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
            cards_docs.append(card_doc)
        
        if cards_docs:
            result = await db.memory_cards.insert_many(cards_docs)
            
        return {
            "ok": True,
            "detail": f"{len(cards_docs)} cards creadas exitosamente",
            "count": len(cards_docs)
        }
        
    except Exception as e:
        print(f"❌ Error creando bulk cards: {e}")
        raise HTTPException(status_code=500, detail="Error creando memory cards")


@router.get("/memory-cards/{card_id}")
async def get_memory_card(card_id: str, user_data: Dict = Depends(require_user)):
    """Obtener detalle de un memory card"""
    try:
        try:
            object_id = ObjectId(card_id)
        except:
            object_id = card_id
        
        card = await db.memory_cards.find_one({"_id": object_id})
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
        raise HTTPException(status_code=500, detail="Error obteniendo memory card")


@router.put("/memory-cards/{card_id}")
async def update_memory_card(
    card_id: str, 
    updates: MemoryCardUpdate,
    user_data: Dict = Depends(require_user)
):
    """Actualizar memory card"""
    try:
        try:
            object_id = ObjectId(card_id)
        except:
            object_id = card_id
        
        # Buscar card
        card = await db.memory_cards.find_one({"_id": object_id})
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
        if updates.difficulty is not None:
            update_doc["$set"]["difficulty"] = updates.difficulty
        if updates.category is not None:
            update_doc["$set"]["category"] = updates.category
        if updates.tags is not None:
            update_doc["$set"]["tags"] = updates.tags
        
        # Actualizar
        result = await db.memory_cards.update_one(
            {"_id": object_id}, 
            update_doc
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No se pudo actualizar")
        
        return {"ok": True, "detail": "Memory card actualizado"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando card: {e}")
        raise HTTPException(status_code=500, detail="Error actualizando memory card")


@router.delete("/memory-cards/{card_id}")
async def delete_memory_card(card_id: str, user_data: Dict = Depends(require_user)):
    """Eliminar memory card"""
    try:
        try:
            object_id = ObjectId(card_id)
        except:
            object_id = card_id
        
        # Buscar card
        card = await db.memory_cards.find_one({"_id": object_id})
        if not card:
            raise HTTPException(status_code=404, detail="Card no encontrado")
        
        # Verificar permisos (propietario o admin)
        if user_data.get('role') != 'admin' and card.get("created_by") != user_data["username"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        result = await db.memory_cards.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Card no encontrado")
        
        return {"ok": True, "detail": "Memory card eliminado"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error eliminando card: {e}")
        raise HTTPException(status_code=500, detail="Error eliminando memory card")


@router.post("/memory-cards/{card_id}/review")
async def review_memory_card(
    card_id: str,
    review: MemoryCardReview,
    user_data: Dict = Depends(require_user)
):
    """Registrar review de una card"""
    try:
        try:
            object_id = ObjectId(card_id)
        except:
            object_id = card_id
        
        # Buscar card
        card = await db.memory_cards.find_one({"_id": object_id})
        if not card:
            raise HTTPException(status_code=404, detail="Card no encontrado")
        
        # Verificar permisos
        if user_data.get('role') != 'admin' and card.get("created_by") != user_data["username"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Actualizar estadísticas
        update_doc = {
            "$inc": {
                "times_reviewed": 1,
                "times_correct" if review.correct else "times_incorrect": 1
            },
            "$set": {
                "last_reviewed": datetime.utcnow()
            }
        }
        
        # Mover box según Leitner
        current_box = card.get("box", 1)
        if review.correct:
            new_box = min(current_box + 1, 5)  # Max box 5
        else:
            new_box = max(current_box - 1, 1)  # Min box 1
        
        update_doc["$set"]["box"] = new_box
        
        result = await db.memory_cards.update_one(
            {"_id": object_id},
            update_doc
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No se pudo registrar review")
        
        return {
            "ok": True,
            "detail": "Review registrada",
            "new_box": new_box,
            "correct": review.correct
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en review: {e}")
        raise HTTPException(status_code=500, detail="Error registrando review")


@router.get("/memory-cards/stats")
async def get_memory_cards_stats(user_data: Dict = Depends(require_user)):
    """Obtener estadísticas de memory cards"""
    try:
        query = {}
        if user_data.get('role') != 'admin':
            query["created_by"] = user_data["username"]
        
        cards = await db.memory_cards.find(query).to_list(length=10000)
        
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
        
    except Exception as e:
        print(f"❌ Error obteniendo stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")


@router.get("/memory-cards/due")
async def get_due_memory_cards(user_data: Dict = Depends(require_user)):
    """Obtener cards pendientes de review"""
    try:
        query = {
            "created_by": user_data["username"],
            "$or": [
                {"last_reviewed": None},
                {"next_review": {"$lte": datetime.utcnow()}}
            ]
        }
        
        cards_cursor = db.memory_cards.find(query).sort("box", 1).limit(50)
        cards_list = await cards_cursor.to_list(length=50)
        
        # Convert ObjectId to string
        for card in cards_list:
            card['id'] = str(card['_id']) if isinstance(card['_id'], ObjectId) else card['_id']
            card.pop('_id', None)
        
        return {
            "ok": True,
            "cards": cards_list,
            "count": len(cards_list)
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo cards due: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo cards pendientes")