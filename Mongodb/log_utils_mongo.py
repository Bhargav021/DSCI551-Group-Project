from mongo_utils import connect_mongo
from datetime import datetime
from bson import json_util


def insert_log(user_query, action_type, generated_query, success=True):
    db = connect_mongo()

    # Safely stringify any Mongo document or query with ObjectId, datetime, etc.
    if isinstance(generated_query, (dict, list)):
        generated_query = json_util.dumps(generated_query)

    db.query_logs.insert_one({
        "timestamp": datetime.utcnow(),
        "user_query": user_query,
        "action_type": action_type,
        "generated_query": generated_query,
        "related_collection": infer_collection(str(generated_query)),
        "success": success
    })


def infer_collection(query):
    for coll in ["recipes", "ingredient_nutrition", "food_prices"]:
        if f"db.{coll}" in query:
            return coll
    return None
