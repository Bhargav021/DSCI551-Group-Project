# llm_agent_mongo.py
from mongo_utils import execute_mongo_query, connect_mongo, load_config
from llm_wrapper import Custom_GenAI
from log_utils_mongo import insert_log
from utils import clean_query, format_mongo_results
import json
import re

PRIMARY_LLM = Custom_GenAI(load_config()["API_KEY"])
SYNTAX_LLM = Custom_GenAI(load_config()["API_KEY"])

def process_query(user_query):
    db = connect_mongo()

    #add recipe
    if "add recipe" in user_query.lower().strip() or "insert recipe" in user_query.lower():
        print("\n🔧 Let's collect the information for your new recipe.")
        name = input("🍽️ Recipe name: ")
        category = input("📂 Category: ")
        ingredients = input("🧂 Ingredients (comma-separated): ").split(",")
        calories = float(input("🔥 Calories: "))
        fat = float(input("🥓 Fat: "))
        carbs = float(input("🍞 Carbs: "))
        protein = float(input("🍗 Protein: "))
        instructions = input("📋 Instructions: ")

        document = {
            "name": name,
            "recipe_category": category,
            "recipe_ingredient_parts": ingredients,
            "calories": calories,
            "fat_g": fat,
            "carbohydrate_g": carbs,
            "protein_g": protein,
            "recipe_instructions": instructions,
            "aggregated_rating": None,
            "review_count": 0
        }

        print("\n🧠 MongoDB Document to Insert:\n")
        print(json.dumps(document, indent=2))
        confirm = input("Run this insert? (yes/no): ").lower()
        if confirm == "yes":
            db.recipes.insert_one(document)
            insert_log(user_query, "INSERT", str(document), "recipes", success=True)
            return "✅ Recipe inserted successfully."
        return "Insert canceled."
    
    #add price
    elif "add price" in user_query.lower() or "insert price" in user_query.lower():
        print("\n🔧 Let's collect the price information.")
        doc = {
        "countryiso3": input("🌍 Country ISO3 code: "),
        "date": input("📅 Date (YYYY-MM-DD): "),
        "market": input("🏪 Market: "),
        "category": input("📂 Category: "),
        "commodity": input("🥦 Commodity: "),
        "unit": input("⚖️ Unit: "),
        "price": float(input("💰 Price: ")),
        "usdprice": float(input("💵 USD Price: "))
        }
        print(json.dumps(doc, indent=2))
        if input("Confirm insert? (yes/no): ").lower() == "yes":
            db.food_prices.insert_one(doc)
            insert_log(user_query, "INSERT", str(doc), "food_prices", success=True)
            return "✅ Price inserted successfully."
        
    #add nutrition
    elif "add nutrition" in user_query.lower() or "insert nutirtion" in user_query.lower():
        doc = {
        "ingredient_name": input("🥦 Ingredient name: "),
        "food_category_id": int(input("📂 Category ID: ")),
        "category_name": input("📂 Category name: "),
        "portion_description": input("🥄 Portion description: "),
        "gram_weight": float(input("⚖️ Gram weight: ")),
        "protein_g": float(input("🍗 Protein: ")),
        "fat_g": float(input("🥓 Fat: ")),
        "carbohydrate_g": float(input("🍞 Carbs: "))
    }
        print(json.dumps(doc, indent=2))
        if input("Confirm insert? (yes/no): ").lower() == "yes":
            db.ingredient_nutrition.insert_one(doc)
            insert_log(user_query, "INSERT", str(doc), "ingredient_nutrition", success=True)
            return "✅ Ingredient inserted."
    

    #modify recipe
    elif "modify recipe" in user_query.lower().strip() or "change recipe" in user_query.lower().strip():
        recipe_name = input("🧾 Enter the recipe name to update: ")
        field = input("✏️ Field to update: ")
        new_value = input("🔁 New value: ")
        if field in ["calories", "fat_g", "carbohydrate_g", "protein_g"]:
            try:
                new_value = float(new_value)
            except:
                pass
        update_result = db.recipes.update_one(
            {"name": recipe_name},
            {"$set": {field: new_value}}
        )
        if update_result.modified_count:
            insert_log(user_query, "UPDATE", f"{recipe_name} => {field} = {new_value}", "recipes", success=True)
            return f"✅ Updated {field} for {recipe_name}."
        else:
            return "❌ No update was made. Recipe not found or value unchanged."
        
    #modify nutrition
    elif "modify nutrition" in user_query.lower() or "change nutrition" in user_query.lower():
        name = input("🥦 Ingredient name: ")
        field = input("✏️ Field to update: ")
        value = float(input("🔁 New value: ")) if "g" in field else input("🔁 New value: ")
        result = db.ingredient_nutrition.update_one({"ingredient_name": name}, {"$set": {field: value}})
        return "✅ Updated." if result.modified_count else "❌ No match."
    
    #modify price
    elif "modify price" in user_query.lower() or "change price" in user_query.lower():
        print("\n🔧 Modifying a price entry in the food_prices collection.")
        commodity = input("🥦 Enter the commodity name to update: ")
        market = input("🏪 Enter the market name: ")
        field = input("✏️ Which field do you want to update (e.g., price, usdprice, unit): ")
        new_value = input("🔁 New value: ")

        # Convert to float if numeric field
        if field in ["price", "usdprice"]:
            try:
                new_value = float(new_value)
            except ValueError:
                return "❌ Price must be numeric."

        result = db.food_prices.update_one(
            {"commodity": commodity, "market": market},
            {"$set": {field: new_value}}
        )

        if result.modified_count:
            insert_log(user_query, "UPDATE", f"{commodity}@{market} => {field} = {new_value}", "food_prices", success=True)
            return f"✅ Updated {field} for {commodity} in {market}."
        else:
            return "❌ No update was made. Entry not found or value unchanged."



    
    #delete recipe
    elif "delelte recipe" in user_query.lower().strip() or "remove recipe" in user_query.lower():
        recipe_name = input("🧾 Enter the recipe name to delete: ")
        delete_result = db.recipes.delete_one({"name": recipe_name})
        if delete_result.deleted_count:
            insert_log(user_query, "DELETE", f"delete {recipe_name}", "recipes", success=True)
            return f"🗑️ Deleted recipe: {recipe_name}"
        else:
            return "❌ Recipe not found."
    
    #delete nutrition    
    elif "delete nutrition" in user_query.lower() or "remove nutrition" in user_query.lower():
        name = input("🥦 Ingredient name: ")
        result = db.ingredient_nutrition.delete_one({"ingredient_name": name})
        return "🗑️ Deleted." if result.deleted_count else "❌ Not found."
    
        
    # Delete food_prices
    elif "delete price" in user_query.lower() or "remove price"in user_query.lower():
        commodity = input("🧾 Commodity: ")
        market = input("🏪 Market: ")
        result = db.food_prices.delete_one({"commodity": commodity, "market": market})
        return "🗑️ Deleted." if result.deleted_count else "❌ Not found."
    
    
    

    # Otherwise, run LLM-based query
    with open("db_schema_context_mongo.txt", "r") as schema_file:
        schema = schema_file.read()
    with open("llm_prompt_mongo.txt", "r", encoding='utf-8') as prompt_file:
        base_prompt = prompt_file.read()

    final_prompt = base_prompt.replace("{SCHEMA}", schema).replace("{QUESTION}", user_query)
    raw_query = PRIMARY_LLM.ask_ai(final_prompt)
    cleaned_query = clean_query(raw_query)

    print("\n🧠 Generated Mongo Query (LLM):\n")
    print(cleaned_query)

    # Validate syntax
    # Load schema context for validation
    with open("db_schema_context_mongo.txt", "r", encoding="utf-8") as schema_file:
        mongo_schema = schema_file.read()

        # Enhanced syntax-checking prompt
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


    confirm = input("\n⚠️ Should I run this query? (yes/no/rewrite): ").lower()
    if confirm == "no":
        insert_log(user_query, "CANCEL", cleaned_query, success=False)
        return "❌ Canceled by user."
    elif confirm == "rewrite":
        clarification = input("🔁 Please clarify your question: ")
        return process_query(clarification)

    try:
        results = execute_mongo_query(cleaned_query)
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

