from pymongo import MongoClient
import json
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["recipe_chatbot"]

def connect_mongo():
    return db

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def fix_js_syntax(js_str):
    """
    Converts JS-style keys like $lookup: to JSON-safe "lookup":
    """
    js_str = re.sub(r'(?<!")(\$?\w+)\s*:', r'"\1":', js_str)
    return js_str

def execute_mongo_query(query_string):
    db = connect_mongo()

    # Match aggregate pipeline
    match = re.match(r'db\.(\w+)\.aggregate\((\[.*\])\)', query_string, re.DOTALL)
    if match:
        collection_name = match.group(1)
        pipeline_raw = match.group(2)
        try:
            fixed_pipeline = fix_js_syntax(pipeline_raw)
            pipeline = json.loads(fixed_pipeline)
            return list(db[collection_name].aggregate(pipeline))
        except Exception as e:
            raise ValueError(f"Aggregate parse error: {e}")

    # Match find with optional projection
    match = re.match(r'db\.(\w+)\.find\(\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)', query_string, re.DOTALL)
    if match:
        collection_name = match.group(1)
        filter_raw = match.group(2)
        projection_raw = match.group(3)
        try:
            filter_json = json.loads(fix_js_syntax(filter_raw))
            if projection_raw:
                projection_json = json.loads(fix_js_syntax(projection_raw))
                return list(db[collection_name].find(filter_json, projection_json))
            else:
                return list(db[collection_name].find(filter_json))
        except Exception as e:
            raise ValueError(f"Find parse error: {e}")

    # Raw JSON fallback (supports: query + optional projection, limit, sort)
    try:
        raw_dict = json.loads(fix_js_syntax(query_string))
        if isinstance(raw_dict, dict):
            # Check for structured query
            if "collection" in raw_dict and "query" in raw_dict:
                collection = db[raw_dict["collection"]]
                query = raw_dict["query"]
                projection = raw_dict.get("projection")
                sort = raw_dict.get("sort")
                limit = raw_dict.get("limit")

                cursor = collection.find(query, projection) if projection else collection.find(query)
                
                if sort:
                    # Convert {"calories": -1} to list of tuples
                    sort_fields = list(sort.items())
                    cursor = cursor.sort(sort_fields)
                if limit:
                    cursor = cursor.limit(limit)

                return list(cursor)

            # Fallback: infer collection by known key
            elif "ingredient_name" in raw_dict:
                return list(db.ingredient_nutrition.find(raw_dict))
            elif "commodity" in raw_dict:
                return list(db.food_prices.find(raw_dict))
            elif "name" in raw_dict:
                return list(db.recipes.find(raw_dict))

    except Exception as e:
        print(f"❌ Fallback parse error: {e}")

    raise ValueError("Unsupported Mongo query format.")
