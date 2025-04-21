# llm_agent_mongo.py (Full CRUD with Flexible Matching & Input Validation)
#create table script addition
#create app.py for the script
from mongo_utils import execute_mongo_query, connect_mongo, load_config
from llm_wrapper import Custom_GenAI
from pymongo import MongoClient
from log_utils_mongo import insert_log
from utils import clean_query, format_mongo_results, extract_json_block
import json
from datetime import datetime
import re

PRIMARY_LLM = Custom_GenAI(load_config()["API_KEY"])
SYNTAX_LLM = Custom_GenAI(load_config()["API_KEY"])

field_defaults = {
    "recipes": [
        "name", "recipecategory", "recipeingredientparts", "calories",
        "fatcontent", "carbohydratecontent", "proteincontent", "recipeinstructions",
        "aggregatedrating", "reviewcount"
    ],
    "ingredient_nutrition": [
        "fdc_id", "ingredient_name", "food_category_id", "category_name",
        "portion_description", "gram_weight", "calcium_mg", "carbohydrate_g",
        "energy_kcal", "energy_kj", "fiber_g", "folate_ug", "iron_mg",
        "magnesium_mg", "potassium_mg", "protein_g", "sodium_mg", "fat_g",
        "vitamin_a_rae_ug", "vitamin_b12_ug", "vitamin_c_ascorbic_ug",
        "vitamin_d_ug", "zinc_mg"
    ],
    "food_prices": [
        "countryiso3", "date", "market", "category", "commodity",
        "unit", "price", "usdprice"
    ]
}


def get_valid_fields(collection_name):
    db = MongoClient("mongodb://localhost:27017/")["recipe_chatbot"]
    sample_doc = db[collection_name].find_one()
    default_fields = set(field_defaults.get(collection_name, []))
    if sample_doc:
        # Combine actual keys + backup defaults to avoid missing anything
        actual_fields = set(sample_doc.keys())
        return actual_fields | default_fields  # union
    
    else:
        return default_fields
   

def match_intent(uq, keywords):
    return all(k in uq for k in keywords)

def safe_preview(doc):
    """Cleans a MongoDB document for safe JSON printing."""
    if doc is None:
        return {}

    cleaned = {}
    for k, v in doc.items():
        if isinstance(v, datetime):
            cleaned[k] = v.strftime("%Y-%m-%d")
        elif k == "_id":
            cleaned[k] = str(v)
        else:
            cleaned[k] = v
    return cleaned


def safe_float(prompt):
    while True:
        val = input(prompt)
        if val == "":
            return None
        try:
            return float(val)
        except ValueError:
            print("❗ Please enter a valid number.")

def safe_date(prompt):
    val = input(prompt)
    if val == "":
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d")
    except ValueError:
        print("❗ Please enter a valid date in YYYY-MM-DD format.")
        return safe_date(prompt)

def preview_doc(doc):
    return {
        k: (v.strftime("%Y-%m-%d") if isinstance(v, datetime) else v)
        for k, v in doc.items()
    }



def process_query(user_query):
    db = connect_mongo()
    uq = user_query.lower().strip()
    
    introspect_keywords = ["table", "tables", "collection", "collections"]
    list_keywords = ["what", "list", "show", "see", "available"]

    print(f"🔍 Interpreted user query: '{uq}'")
    print(f"🔍 Trigger introspection? {any(k1 in uq for k1 in introspect_keywords)} and {any(k2 in uq for k2 in list_keywords)}")

    if any(k1 in uq for k1 in introspect_keywords) and any(k2 in uq for k2 in list_keywords):
        collections = db.list_collection_names()

        # Check if user mentions a specific table name (like recipe/recipes)
        uq_clean = uq.replace("table", "").replace("collection", "").strip()
        for coll in collections:
            if coll in uq_clean or coll.rstrip("s") in uq_clean or uq_clean.rstrip("s") == coll:
                sample = db[coll].find_one()
                if sample:
                    fields = list(sample.keys())
                    return f"📘 Collection: `{coll}`\nFields: {', '.join(fields)}"
                else:
                    return f"📘 Collection: `{coll}` (no sample found)"
        
        # If no specific table mentioned, show all collections
        result = []
        for coll in collections:
            sample = db[coll].find_one()
            if sample:
                fields = list(sample.keys())
                result.append(f"📘 Collection: `{coll}`\nFields: {', '.join(fields)}")
            else:
                result.append(f"📘 Collection: `{coll}` (no sample found)")
        return "\n\n".join(result)




    # # ---------------------- schema of db ----------------------
    # if match_intent(uq, ["tables"]) or match_intent(uq, ["list", "collections"]):
    #     collections = db.list_collection_names()
    #     result = []

    #     for coll in collections:
    #         sample = db[coll].find_one()
    #         if sample:
    #             fields = list(sample.keys())
    #             result.append(f"📘 Collection: `{coll}`\nFields: {', '.join(fields)}")
    #         else:
    #             result.append(f"📘 Collection: `{coll}` (no sample found)")

    #     return "\n\n".join(result)

     # ---------------------- INSERT ----------------------
    elif match_intent(uq, ["add", "recipe"]) or match_intent(uq, ["insert", "recipe"]):
        print("\n🔧 Let's collect the information for your new recipe.")
        doc = {
            "name": input("🍽️ Recipe name: ") or None,
            "recipe_category": input("📂 Category: ") or None,
            "recipe_ingredient_parts": [i.strip() for i in input("🧂 Ingredients (comma-separated): ").split(",") if i.strip()],
            "calories": safe_float("🔥 Calories: "),
            "fat_g": safe_float("🥓 Fat: "),
            "carbohydrate_g": safe_float("🍞 Carbs: "),
            "protein_g": safe_float("🍗 Protein: "),
            "recipe_instructions": input("📋 Instructions: ") or "",
            "aggregated_rating": None,
            "review_count": 0
        }

        print("\n🧠 MongoDB Document to Insert:\n")
        print(json.dumps(preview_doc(doc), indent=2))

        if not doc["name"]:
            return "❌ 'name' is required to insert a recipe."

        if input("Run this insert? (yes/no): ").lower() == "yes":
            try:
                result = db.recipes.insert_one(doc)
                inserted = db.recipes.find_one({"_id": result.inserted_id})
                print(json.dumps(safe_preview(inserted), indent=2))
                insert_log(user_query, "INSERT", str(doc), success=True)
                return "✅ Recipe inserted successfully."
            except Exception as e:
                return f"❌ Insert failed: {e}"
        return "Insert canceled."

    elif match_intent(uq, ["add", "price"]) or match_intent(uq, ["insert", "price"]):
        print("\n🔧 Let's collect the price information.")
        doc = {
            "countryiso3": input("🌍 Country ISO3 code: ") or None,
            "date": safe_date("📅 Date (YYYY-MM-DD): "),
            "market": input("🏪 Market: ") or None,
            "category": input("📂 Category: ") or None,
            "commodity": input("🥦 Commodity: ") or None,
            "unit": input("⚖️ Unit: ") or None,
            "price": safe_float("💰 Price: "),
            "usdprice": safe_float("💵 USD Price: ")
        }

        print("\n🧠 MongoDB Document to Insert:\n")
        print(json.dumps(preview_doc(doc), indent=2))

        if not doc["countryiso3"] or not doc["commodity"]:
            return "❌ 'countryiso3' and 'commodity' are required to insert a price entry."

        if input("Confirm insert? (yes/no): ").lower() == "yes":
            try:
                result = db.food_prices.insert_one(doc)
                inserted = db.food_prices.find_one({"_id": result.inserted_id})
                print(json.dumps(safe_preview(inserted), indent=2))
                insert_log(user_query, "INSERT", str(doc), success=True)
                return "✅ Price inserted successfully."
            except Exception as e:
                return f"❌ Insert failed: {e}"
        return "Insert canceled."

    elif match_intent(uq, ["add", "nutrition"]) or match_intent(uq, ["insert", "nutrition"]):
        print("\n🔧 Let's collect the nutrition information.")
        doc = {
            "ingredient_name": input("🥦 Ingredient name: ") or None,
            "food_category_id": int(input("📂 Category ID: ") or 0),
            "category_name": input("📂 Category name: ") or None,
            "portion_description": input("🥄 Portion description: ") or None,
            "gram_weight": safe_float("⚖️ Gram weight: "),
            "protein_g": safe_float("🍗 Protein: "),
            "fat_g": safe_float("🥓 Fat: "),
            "carbohydrate_g": safe_float("🍞 Carbs: ")
        }

        print("\n🧠 MongoDB Document to Insert:\n")
        print(json.dumps(preview_doc(doc), indent=2))

        if not doc["ingredient_name"]:
            return "❌ 'ingredient_name' is required to insert nutrition data."

        if input("Confirm insert? (yes/no): ").lower() == "yes":
            try:
                result = db.ingredient_nutrition.insert_one(doc)
                inserted = db.ingredient_nutrition.find_one({"_id": result.inserted_id})
                print(json.dumps(safe_preview(inserted), indent=2))
                insert_log(user_query, "INSERT", str(doc), success=True)
                return "✅ Ingredient inserted."
            except Exception as e:
                return f"❌ Insert failed: {e}"
        return "Insert canceled."


    # ---------------------- UPDATE ----------------------
    elif match_intent(uq, ["modify", "recipe"]) or match_intent(uq, ["change", "recipe"]) or match_intent(uq, ["update", "recipe"]) or match_intent(uq, ["Update", "recipe"]):
        name = input("🧾 Recipe name to update: ")
        field = input("✏️ Field to update: ")
        value = input("🔁 New value: ")
        try:
            result = db.recipes.update_one({"name": name}, {"$set": {field: float(value) if value.replace('.', '', 1).isdigit() else value}})
            if result.modified_count:
                insert_log(user_query=user_query, action_type="UPDATE", generated_query=f"{name} => {field} = {value}", success=True)
                return f"✅ Updated {field} for recipe {name}."
        except Exception as e:
            return f"❌ Update failed: {e}"
        return "❌ No update made."

    elif match_intent(uq, ["modify", "price"]) or match_intent(uq, ["change", "price"]) or match_intent(uq, ["update", "price"]) or match_intent(uq, ["Update", "price"]):
        commodity = input("🥦 Commodity: ")
        market = input("🏪 Market: ")
        field = input("✏️ Field to update: ")
        value = input("🔁 New value: ")
        try:
            result = db.food_prices.update_one({"commodity": commodity, "market": market}, {"$set": {field: float(value) if value.replace('.', '', 1).isdigit() else value}})
            if result.modified_count:
                insert_log(user_query=user_query, action_type="UPDATE", generated_query=f"{commodity}@{market} => {field} = {value}", success=True)
                return f"✅ Updated {field} for {commodity} in {market}."
        except Exception as e:
            return f"❌ Update failed: {e}"
        return "❌ No update made."

    elif match_intent(uq, ["modify", "nutrition"]) or match_intent(uq, ["change", "nutrition"]) or match_intent(uq, ["update", "nutrition"]) or match_intent(uq, ["Update", "nutrition"]):
        name = input("🥦 Ingredient name: ")
        field = input("✏️ Field to update: ")
        value = input("🔁 New value: ")
        try:
            result = db.ingredient_nutrition.update_one({"ingredient_name": name}, {"$set": {field: float(value) if value.replace('.', '', 1).isdigit() else value}})
            if result.modified_count:
                insert_log(user_query=user_query, action_type="UPDATE", generated_query=f"{name} => {field} = {value}", success=True)
                return f"✅ Updated {field} for {name}."
        except Exception as e:
            return f"❌ Update failed: {e}"
        return "❌ No update made."

    # ---------------------- DELETE ----------------------
    elif match_intent(uq, ["delete", "recipe"]) or match_intent(uq, ["remove", "recipe"]) :
        name = input("🍽️ Recipe name to delete: ")
        result = db.recipes.delete_one({"name": name})
        if result.deleted_count:
            insert_log(user_query=user_query, action_type="DELETE", generated_query=f"delete {name}", success=True)
            return f"🗑️ Deleted recipe: {name}."
        return "❌ Entry not found."

    elif match_intent(uq, ["delete", "price"]) or match_intent(uq, ["remove", "price"]):
        commodity = input("🧾 Commodity: ")
        market = input("🏪 Market: ")
        result = db.food_prices.delete_one({"commodity": commodity, "market": market})
        if result.deleted_count:
            insert_log(user_query=user_query, action_type="DELETE", generated_query=f"delete {commodity}@{market}", success=True)
            return f"🗑️ Deleted price for {commodity} at {market}."
        return "❌ Entry not found."

    elif match_intent(uq, ["delete", "nutrition"]) or match_intent(uq, ["remove", "nutrition"]):
        name = input("🥦 Ingredient name to delete: ")
        result = db.ingredient_nutrition.delete_one({"ingredient_name": name})
        if result.deleted_count:
            insert_log(user_query=user_query, action_type="DELETE", generated_query=f"delete {name}", success=True)
            return f"🗑️ Deleted nutrition info for {name}."
        return "❌ Entry not found."

    # LLM-based Search
    with open("db_schema_context_mongo.txt", "r") as schema_file:
        schema = schema_file.read()
    with open("llm_prompt_mongo.txt", "r", encoding='utf-8') as prompt_file:
        base_prompt = prompt_file.read()

    # user_query = user_query.replace("food_category_id", "").replace("category_name", "")
    final_prompt = base_prompt.replace("{SCHEMA}", schema).replace("{QUESTION}", user_query)
    raw_query = PRIMARY_LLM.ask_ai(final_prompt)

    # Clean and extract the output
    raw_cleaned = clean_query(raw_query)
    if raw_cleaned.strip().startswith("{"):
        cleaned_query = extract_json_block(raw_cleaned)
    else:
        cleaned_query = raw_cleaned 

    print("\n🧠 Generated Mongo Query (LLM):\n")
    print(cleaned_query)   

    if cleaned_query.strip().startswith("db.") or cleaned_query.strip().startswith("show"):
        try:
            if "list_collection_names" in cleaned_query:
                collections = db.list_collection_names()
                return "\n".join([f"📘 {c}" for c in collections])
            elif cleaned_query.startswith("show collections"):
                collections = db.list_collection_names()
                return "\n".join([f"📘 {c}" for c in collections])
            elif "find_one().keys()" in cleaned_query:
                coll_name = re.findall(r"db\.(\w+)\.find_one", cleaned_query)
                if coll_name:
                    sample = db[coll_name[0]].find_one()
                    if sample:
                        return f"🧾 Fields in `{coll_name[0]}`:\n" + ", ".join(sample.keys())
                    else:
                        return f"⚠️ No sample found in `{coll_name[0]}`"
        except Exception as e:
            return f"❌ Failed to run client command: {e}"
    raw_cleaned = clean_query(raw_query)
    if raw_cleaned.strip().startswith("{"):
        cleaned_query = extract_json_block(raw_cleaned)
    else:
        cleaned_query = raw_cleaned  

    print("\n🧠 Generated Mongo Query (LLM):\n")
    print(cleaned_query)

    with open("db_schema_context_mongo.txt", "r", encoding="utf-8") as schema_file:
        mongo_schema = schema_file.read()

    syntax_prompt = f"""You are an expert MongoDB syntax and schema validator.
    Below is the database schema:
    {mongo_schema}

    And here is the generated query:
    {cleaned_query}

    Please check if:
    - The syntax is valid
    - All field and collection names match the schema
    - The structure (e.g., pipeline stages) is correct

    If something is wrong, suggest the corrected version. Otherwise, reply 'Valid ✅'.
    """
    syntax_feedback = SYNTAX_LLM.ask_ai(syntax_prompt)
    print("\n🧪 Syntax LLM feedback:\n", syntax_feedback)

    # Check if the feedback includes a corrected query
    if "{" in syntax_feedback and "collection" in syntax_feedback and "query" in syntax_feedback:
        matches = re.findall(r'{[\s\S]+}', syntax_feedback)
        if matches:
            try:
                corrected_query = json.loads(matches[0])
                print("⚠️ Detected corrected query. Overriding previous query with this one:")
                print(json.dumps(corrected_query, indent=2))
                wrapped_query = corrected_query  # Update actual query structure
            except json.JSONDecodeError as e:
                print(f"❌ Could not parse corrected JSON: {e}")
        else:
            print("❌ No valid JSON query found in LLM feedback.")

    confirm = input("\n⚠️ Should I run this query? (yes/no/rewrite): ").lower()

    if confirm == "no":
        insert_log(user_query, "CANCEL", cleaned_query, success=False)
        return "❌ Canceled by user."
    elif confirm == "rewrite":
        clarification = input("🔁 Please clarify your question: ")
        return process_query(clarification)

    try:

        try:
            # if cleaned_query.strip().startswith("db.") or cleaned_query.strip().startswith("show "):
            #     try:
            #         if "list_collection_names" in cleaned_query:
            #             collections = db.list_collection_names()
            #             return "\n".join([f"📘 {c}" for c in collections])
            #         elif "find_one().keys()" in cleaned_query:
            #             match = re.search(r"db\.(\w+)\.find_one", cleaned_query)
            #             if match:
            #                 coll = match.group(1)
            #                 sample = db[coll].find_one()
            #                 if sample:
            #                     return f"🧾 Fields in `{coll}`:\n" + ", ".join(sample.keys())
            #                 else:
            #                     return f"⚠️ No sample found in `{coll}`"
            #         else:
            #             return f"⚠️ Unrecognized client command: `{cleaned_query}`"
            #     except Exception as e:
            #         return f"❌ Failed to run client command: {e}"
                
            if not cleaned_query.strip().startswith("{"):
                print("⚠️ Skipping JSON parsing for non-JSON client command.")
                try:
                    if "list_collection_names" in cleaned_query:
                        collections = db.list_collection_names()
                        return "\n".join([f"📘 {c}" for c in collections])
                    elif cleaned_query.startswith("show collections"):
                        collections = db.list_collection_names()
                        return "\n".join([f"📘 {c}" for c in collections])
                    elif "find_one().keys()" in cleaned_query:
                        coll_name = re.findall(r"db\.(\w+)\.find_one", cleaned_query)
                        if coll_name:
                            sample = db[coll_name[0]].find_one()
                            if sample:
                                return f"🧾 Fields in `{coll_name[0]}`:\n" + ", ".join(sample.keys())
                            else:
                                return f"⚠️ No sample found in `{coll_name[0]}`"
                    return f"⚠️ Unrecognized client command: {cleaned_query}"
                except Exception as e:
                    return f"❌ Failed to run client command: {e}"

            raw_query_dict = json.loads(cleaned_query)
        except json.JSONDecodeError as e:
            print("❌ Could not parse LLM output as valid JSON.")
            print("🧠 LLM returned:\n", cleaned_query)
            insert_log(user_query, "FAIL", cleaned_query, success=False)
            return f"❌ LLM output was not valid JSON: {e}"

        if "ingredient_name" in raw_query_dict:
            wrapped_query = {
                "collection": "ingredient_nutrition",
                "query": raw_query_dict
            }
        elif "commodity" in raw_query_dict:
            wrapped_query = {
                "collection": "food_prices",
                "query": raw_query_dict
            }
        elif "name" in raw_query_dict:
            wrapped_query = {
                "collection": "recipes",
                "query": raw_query_dict
            }
        else:
            wrapped_query = raw_query_dict

        query_dict = wrapped_query.get("query", {})
        query_dict = {k: v for k, v in query_dict.items() if v not in [None, "", {}]}
        wrapped_query["query"] = query_dict

        # CLEAN QUERY BEFORE EXECUTION
        if isinstance(wrapped_query, dict) and "collection" in wrapped_query and "query" in wrapped_query:
            collection = wrapped_query["collection"]
            valid_fields = get_valid_fields(collection)

            def is_valid_field(key):
                return key in valid_fields or any(key.startswith(f"{v}.") for v in valid_fields)

            removed = [k for k in wrapped_query["query"] if not is_valid_field(k)]
            if removed:
                print(f"⚠️ Removing invalid fields: {removed}")

            filtered_query = {
                k: v for k, v in wrapped_query["query"].items()
                if is_valid_field(k)
            }

            # ⚠️ If empty, regenerate using second LLM
            if not filtered_query:
                print("⚠️ Query is empty after filtering. Attempting regeneration via second LLM...")

                clarification_prompt = f"""
                    The original query became empty after removing invalid or non-existent fields.

                    The schema is:
                    {schema}

                    Original user question:
                    {user_query}

                    The previous query was:
                    {wrapped_query}

                    Please regenerate a valid MongoDB query wrapped in:
                    {{
                    "collection": "<collection_name>",
                    "query": {{ ... }}
                    }}

                    Use only valid fields from the schema.
                    """

                regenerated_query = SYNTAX_LLM.ask_ai(clarification_prompt)

                # Parse JSON from LLM response
                matches = re.findall(r'{[\s\S]+}', regenerated_query)
                if matches:
                    try:
                        new_query = json.loads(matches[0])
                        print("🔁 Recovered query after regeneration:")
                        print(json.dumps(new_query, indent=2))
                        wrapped_query = new_query
                    except Exception as e:
                        return f"<b>Failed to parse regenerated query: {e}</b>"
                else:
                    return "<b>Query could not be regenerated. Try rephrasing.</b>"

            else:
                wrapped_query["query"] = filtered_query


        results = execute_mongo_query(json.dumps(wrapped_query))
        if not results:
            print("!! Query was valid but found no matching documents.")
        insert_log(user_query, "QUERY", cleaned_query, success=bool(results))
        return format_mongo_results(results)
    
    except Exception as e:
        return f"❌ Mongo query error: {e}"

if __name__ == "__main__":
    print("🧠 Welcome to your LLM-powered Recipe Database Assistant.")
    print("Type 'exit' or 'quit' to leave.\n")

    while True:
        try:
            user_input = input("🧑‍🍳 Ask your database a question: ")
            if user_input.strip().lower() in {"exit", "quit"}:
                print("👋 Goodbye!")
                break
            response = process_query(user_input)
            print("\n📋 Response:\n", response)
            print("\n" + "=" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n👋 Exiting via keyboard interrupt.")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
