import pandas as pd
from pymongo import MongoClient
import pycountry
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["recipe_chatbot"]

### ---------- 1. Load recipes.csv ---------- ###
recipes_df = pd.read_csv("sample_food_com_recipes.csv")

def parse_instructions(instr):
    try:
        return eval(instr.replace("c(", "[").replace(")", "]"))
    except:
        return []

def parse_ingredients(ingr):
    try:
        return eval(ingr.replace("c(", "[").replace(")", "]"))
    except:
        return []

recipes_data = []
for _, row in recipes_df.iterrows():
    recipes_data.append({
        "recipe_id": int(row["RecipeId"]),
        "name": row["Name"],
        "recipe_category": row["RecipeCategory"],
        "recipe_ingredient_parts": parse_ingredients(row["RecipeIngredientParts"]),
        "calories": row["Calories"],
        "fat_g": row["FatContent"],
        "carbohydrate_g": row["CarbohydrateContent"],
        "protein_g": row["ProteinContent"],
        "recipe_instructions": parse_instructions(row["RecipeInstructions"]),
        "aggregated_rating": row["AggregatedRating"],
        "review_count": row["ReviewCount"]
    })

db.recipes.insert_many(recipes_data)
print("✅ Recipes inserted.")

### ---------- 2. Load ingredient_nutrition.csv ---------- ###
nutrition_df = pd.read_csv("final_ingredient_sample_1000.csv")

def extract_nutrients(row):
    return {
        "calcium_mg": row.get("Calcium, Ca (MG)"),
        "carbohydrate_g": row.get("Carbohydrate, by difference (G)"),
        "energy_kcal": row.get("Energy (KCAL)"),
        "fiber_g": row.get("Fiber, total dietary (G)"),
        "iron_mg": row.get("Iron, Fe (MG)"),
        "magnesium_mg": row.get("Magnesium, Mg (MG)"),
        "potassium_mg": row.get("Potassium, K (MG)"),
        "protein_g": row.get("Protein (G)"),
        "sodium_mg": row.get("Sodium, Na (MG)"),
        "fat_g": row.get("Total lipid (fat) (G)"),
        "vitamin_a_rae_ug": row.get("Vitamin A, RAE (UG)"),
        "vitamin_b12_ug": row.get("Vitamin B-12 (UG)"),
        "vitamin_c_mg": row.get("Vitamin C, total ascorbic acid (MG)"),
        "vitamin_d_ug": row.get("Vitamin D (D2 + D3) (UG)"),
        "zinc_mg": row.get("Zinc, Zn (MG)")
    }

nutrition_data = []
for _, row in nutrition_df.iterrows():
    nutrition_data.append({
        "fdc_id": int(row["fdc_id"]),
        "ingredient_name": row["ingredient_name"],
        "food_category_id": row["food_category_id"],
        "category_name": row["category_name"],
        "portion_description": row["portion_description"],
        "gram_weight": row["gram_weight"],
        "nutrients": extract_nutrients(row)
    })

db.ingredient_nutrition.insert_many(nutrition_data)
print("✅ Ingredient nutrition inserted.")

### ---------- 3. Load food_prices.csv ---------- ###
prices_df = pd.read_csv("sample_global_food_prices.csv")
prices_df["date"] = pd.to_datetime(prices_df["date"])

prices_data = prices_df.rename(columns={"countryiso3": "countryiso3"}).to_dict(orient="records")
db.food_prices.insert_many(prices_data)
print("✅ Food prices inserted.")

### ---------- 4. Generate country_codes ---------- ###
country_codes = []
for country in pycountry.countries:
    country_codes.append({
        "name": country.name,
        "iso3": country.alpha_3
    })

db.country_codes.insert_many(country_codes)
print("✅ Country codes inserted.")

### ---------- 5. Insert placeholder aliases (optional) ---------- ###
db.ingredient_aliases.insert_many([
    { "alias": "garbanzo beans", "canonical_name": "chickpeas" },
    { "alias": "aubergine", "canonical_name": "eggplant" }
])
print("✅ Ingredient aliases inserted.")

### ---------- 6. Insert sample recipe_ingredients (optional) ---------- ###
db.recipe_ingredients.insert_many([
    { "recipe_id": 448158, "ingredient_name": "chickpeas", "fdc_id": 319874, "ingredient_id": 1 }
])
print("✅ Recipe ingredients inserted.")

### ---------- 7. Insert sample query_logs ---------- ###
db.query_logs.insert_one({
    "timestamp": datetime.utcnow(),
    "user_query": "What is the fat content of hummus?",
    "action_type": "FIND",
    "generated_query": {
        "collection": "ingredient_nutrition",
        "filter": { "ingredient_name": { "$regex": "hummus", "$options": "i" } }
    },
    "related_collection": "ingredient_nutrition",
    "matched_count": 1,
    "success": True
})
print("✅ Sample query log inserted.")
