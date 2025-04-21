# llm_agent_mongo.py
from mongo_utils import connect_mongo, execute_mongo_query
from log_utils_mongo import insert_log
from helper import get_country_iso3
from llm_wrapper import Custom_GenAI
from utils import clean_query
from mongo_utils import load_config
import re
import json
from datetime import datetime

# NLP field keyword mapping
FIELD_MAP = {
    "fat": "nutrients.fat_g",
    "protein": "nutrients.protein_g",
    "carbohydrate": "nutrients.carbohydrate_g",
    "fiber": "nutrients.fiber_g",
    "calories": "nutrients.energy_kcal",
    "energy": "nutrients.energy_kcal",
    "sodium": "nutrients.sodium_mg",
    "iron": "nutrients.iron_mg",
    "vitamin c": "nutrients.vitamin_c_mg",
    "vitamin d": "nutrients.vitamin_d_ug",
    "zinc": "nutrients.zinc_mg"
}

def preprocess_country_names(query):
    words = query.split()
    for word in words:
        iso = get_country_iso3(word)
        if iso:
            query = re.sub(rf"\b{word}\b", iso, query, flags=re.IGNORECASE)
    return query

def map_fields(query):
    for keyword, field in FIELD_MAP.items():
        if keyword in query.lower():
            query = query.replace(keyword, field)
    return query

def fuzzy_ingredient_match(ingredient):
    db = connect_mongo()
    match = db.ingredient_aliases.find_one({"alias": {"$regex": f"^{ingredient}$", "$options": "i"}})
    return match["canonical_name"] if match else ingredient

def validate_against_existing_ingredients(ingredient):
    db = connect_mongo()
    exists = db.ingredient_nutrition.find_one({"ingredient_name": {"$regex": f"{ingredient}", "$options": "i"}})
    return bool(exists)

#when user wants to add to the database
def collect_recipe_info():
    print("\nLet's add your recipe step-by-step:")
    name = input("🍽️ Recipe name: ")
    category = input("📂 Recipe category (e.g., Vegan, Dessert): ")

    print("📝 Enter ingredients one-by-one. Type 'done' to finish.")
    ingredients = []
    while True:
        ing = input("Ingredient: ")
        if ing.lower() == 'done':
            break
        canonical = fuzzy_ingredient_match(ing)
        status = validate_against_existing_ingredients(canonical)
        if not status:
            print(f"⚠️ Warning: '{canonical}' not found in known ingredients.")
        ingredients.append(canonical)

    instructions = input("📋 Instructions: ")
    calories = input("🔥 Calories (optional): ") or None
    fat = input("🥓 Fat content (optional): ") or None
    carbs = input("🍞 Carbohydrates (optional): ") or None
    protein = input("🍗 Protein (optional): ") or None

    doc = {
        "recipe_id": name.lower().replace(" ", "_"),
        "name": name,
        "recipe_category": category,
        "recipe_ingredient_parts": ingredients,
        "calories": float(calories) if calories else None,
        "fat_g": float(fat) if fat else None,
        "carbohydrate_g": float(carbs) if carbs else None,
        "protein_g": float(protein) if protein else None,
        "recipe_instructions": [instructions],
        "aggregated_rating": None,
        "review_count": 0
    }

    print("\n🔍 Review your recipe document:")
    print(json.dumps(doc, indent=2))
    confirm = input("✅ Save this to the database? (yes/no): ").lower()
    return doc if confirm == "yes" else None

def process_query(user_query, previous_query=None, original_question=None):
    user_query = preprocess_country_names(user_query)
    user_query = map_fields(user_query)

    with open("db_schema_context_mongo.txt", "r", encoding="utf-8") as schema_file:
        schema = schema_file.read()
    with open("llm_prompt_mongo.txt", "r", encoding="utf-8") as prompt_file:
        system_prompt = prompt_file.read()

    config = load_config()
    ai = Custom_GenAI(config["API_KEY"])

    if previous_query:
        combined = f"Original: {original_question}\nPrevious Mongo Query:\n{previous_query}\nClarification: {user_query}"
    else:
        combined = user_query

    prompt = system_prompt.replace("{SCHEMA}", schema).replace("{QUESTION}", combined)
    mongo_query = ai.ask_ai(prompt)
    cleaned_mongod_query = clean_query(mongo_query)

    print("\n Generated Mongo Query (LLM):\n", cleaned_mongod_query)
    decision = input("\nShould I run this query? (yes/no/rewrite): ").lower()

    if decision == "no":
        insert_log(user_query, "CANCEL", cleaned_mongod_query, success=False)
        return " Query cancelled."

    elif decision == "rewrite":
        clarification = input(" Please clarify: ")
        return process_query(clarification, previous_query=cleaned_mongod_query, original_question=user_query)

    try:
        result = execute_mongo_query(cleaned_mongod_query)
        success = bool(result)
        insert_log(user_query, "FIND", cleaned_mongod_query, success=success)

        if not success:
            add_data = input("No results found. Add to database? (yes/no): ").lower()
            if add_data == "yes":
                structured_doc = collect_recipe_info()
                if structured_doc:
                    try:
                        db = connect_mongo()
                        db.recipes.insert_one(structured_doc)
                        insert_log("manual insert", "INSERT", json.dumps(structured_doc), success=True)
                        return "\u2705 Data inserted."
                    except Exception as e:
                        insert_log("manual insert", "INSERT", json.dumps(structured_doc), success=False)
                        return f"\u274c Insert failed: {e}"
                else:
                    return "\u274c Insert cancelled by user."

        return result or "Query executed (no results)."

    except Exception as e:
        insert_log(user_query, "FIND", cleaned_mongod_query, success=False)
        return f" Mongo query error: {e}"

if __name__ == "__main__":
    question = input("Ask about recipes, nutrition or prices: ")
    print(process_query(question))
