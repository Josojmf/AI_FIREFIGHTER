from bson import ObjectId

def serialize_mongo(doc: dict) -> dict:
    if not doc:
        return doc

    doc = dict(doc)

    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]

    return doc
