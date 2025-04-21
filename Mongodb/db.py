from pymongo import MongoClient
from datetime import datetime

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["recipe_chatbot"]

# 1. country_codes
db.country_codes.insert_one({
    "name": "Kenya",
    "iso3": "KEN"
})

# 2. food_prices
db.food_prices.insert_one({
    "countryiso3": "KEN",
    "date": datetime(2023, 7, 1),
    "market": "Nairobi",
    "category": "Vegetables",
    "commodity": "Garlic",
    "unit": "kg",
    "price": 220.5,
    "usdprice": 2.15
})

# 3. ingredient_aliases
db.ingredient_aliases.insert_one({
    "alias": "garbanzo beans",
    "canonical_name": "chickpeas"
})

# 4. ingredient_nutrition
db.ingredient_nutrition.insert_one({
    "fdc_id": 319874,
    "ingredient_name": "HUMMUS, SABRA CLASSIC",
    "food_category_id": 16,
    "category_name": "Legume-based spreads",
    "portion_description": "1/4 cup",
    "gram_weight": 61.0,
    "nutrients": {
        "calcium_mg": 40,
        "carbohydrate_g": 10.0,
        "energy_kcal": 150,
        "fiber_g": 2.0,
        "iron_mg": 1.2,
        "potassium_mg": 210,
        "protein_g": 4.0,
        "sodium_mg": 180,
        "fat_g": 9.0,
        "vitamin_c_mg": 0.5
    }
})

# 5. query_logs
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

# 6. recipes
db.recipes.insert_one({
    "recipe_id": 448158,
    "name": "Chipotle Hummus",
    "recipe_category": "Appetizers",
    "recipe_ingredient_parts": [
        "chickpeas", "garlic", "lemon juice", "olive oil", "chipotle peppers"
    ],
    "calories": 250,
    "fat_g": 15.0,
    "carbohydrate_g": 20.0,
    "protein_g": 8.0,
    "recipe_instructions": [
        "Blend chickpeas, garlic, lemon juice, and chipotle.",
        "Add olive oil gradually until smooth."
    ],
    "aggregated_rating": 4.7,
    "review_count": 150
})

# 7. recipe_ingredients (mapping collection, like SQL join)
db.recipe_ingredients.insert_one({
    "recipe_id": 448158,
    "ingredient_name": "chickpeas",
    "fdc_id": 319874,
    "ingredient_id": 1  # Assuming this maps to _id of ingredient_nutrition
})

# 🧠 Optional Indexes
db.ingredient_nutrition.create_index("fdc_id", unique=False)
db.ingredient_nutrition.create_index("ingredient_name", unique=False)
db.recipes.create_index("recipe_id", unique=True)
db.food_prices.create_index("countryiso3")
db.country_codes.create_index("iso3", unique=True)
db.recipe_ingredients.create_index("recipe_id")
db.query_logs.create_index("timestamp")

print("All MongoDB collections created and sample docs inserted.")
