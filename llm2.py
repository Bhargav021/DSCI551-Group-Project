# %% [markdown]
# ## Set up the LLM for query translation

# %%
from google import genai
import json
import psycopg2

# %%
def load_config():
    with open("config.json", "r") as file:
        return json.load(file)

# %%
# Define Custom GenAI class for LLM interaction
class Custom_GenAI:
    def __init__(self, API_KEY):
        self.client = genai.Client(api_key=API_KEY)

    def ask_ai(self, question, schema):
        prompt = f"Here is the database schema:\n{schema}\nNow, please answer the following question using SQL:\n{question}"
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text

# %%
config = load_config()
API_KEY = config["API_KEY"]

# %%
database_schema = """
The database contains a table called 'products' with the following columns:

1. code (TEXT) - Unique identifier for each product.
2. url (TEXT) - URL for the product.
3. creator (TEXT) - Creator of the product data.
4. created_t (BIGINT) - Timestamp when the product data was created.
5. created_datetime (TIMESTAMP) - The exact creation date and time of the product.
6. last_modified_t (BIGINT) - Timestamp when the product data was last modified.
7. last_modified_datetime (TIMESTAMP) - The exact date and time of the last modification.
8. last_modified_by (TEXT) - The user who last modified the product data.
9. last_updated_t (BIGINT) - Timestamp for the last update.
10. last_updated_datetime (TIMESTAMP) - The exact date and time of the last update.
11. product_name (TEXT) - Name of the product.
    - Constraints: NOT NULL.
12. abbreviated_product_name (TEXT) - Shortened version of the product name.
13. generic_name (TEXT) - The generic name of the product.
14. quantity (TEXT) - Quantity of the product.
15. packaging (TEXT) - The packaging of the product.
16. packaging_tags (TEXT) - Tags related to the packaging.
17. packaging_en (TEXT) - English version of packaging description.
18. packaging_text (TEXT) - Text description of the packaging.
19. brands (TEXT) - Brands associated with the product.
20. brands_tags (TEXT) - Tags related to the brands.
21. brands_en (TEXT) - English version of brand names.
22. categories (TEXT) - Categories associated with the product.
23. categories_tags (TEXT) - Tags related to the product categories.
24. categories_en (TEXT) - English version of categories.
25. origins (TEXT) - Origins of the product.
26. origins_tags (TEXT) - Tags related to the product origins.
27. origins_en (TEXT) - English version of origins.
28. manufacturing_places (TEXT) - Locations where the product is manufactured.
29. manufacturing_places_tags (TEXT) - Tags related to manufacturing places.
30. labels (TEXT) - Labels associated with the product.
31. labels_tags (TEXT) - Tags related to the labels.
32. labels_en (TEXT) - English version of labels.
33. emb_codes (TEXT) - Emb codes for the product.
34. emb_codes_tags (TEXT) - Tags related to emb codes.
35. first_packaging_code_geo (TEXT) - First packaging code geo.
36. cities (TEXT) - Cities where the product is available.
37. cities_tags (TEXT) - Tags related to cities.
38. purchase_places (TEXT) - Locations where the product can be purchased.
39. stores (TEXT) - Stores selling the product.
40. countries (TEXT) - Countries where the product is available.
41. countries_tags (TEXT) - Tags related to countries.
42. countries_en (TEXT) - English version of countries.
43. ingredients_text (TEXT) - Ingredients list for the product.
44. ingredients_tags (TEXT) - Tags related to ingredients.
45. ingredients_analysis_tags (TEXT) - Tags related to ingredients analysis.
46. allergens (TEXT) - Allergens present in the product.
47. allergens_en (TEXT) - English version of allergens.
48. traces (TEXT) - Traces of other substances.
49. traces_tags (TEXT) - Tags related to traces.
50. traces_en (TEXT) - English version of traces.
51. serving_size (TEXT) - Serving size of the product.
52. serving_quantity (FLOAT) - Quantity per serving.
53. no_nutrition_data (TEXT) - Indicator for missing nutrition data.
54. additives_n (TEXT) - Additives in the product.
55. additives (TEXT) - Additives present in the product.
56. additives_tags (TEXT) - Tags related to additives.
57. additives_en (TEXT) - English version of additives.
58. nutriscore_score (INT) - Nutri-Score of the product.
    - Constraints: Check between 0 and 100, or NULL/UNKNOWN.
59. nutriscore_grade (TEXT) - Nutri-Score grade of the product.
    - Constraints: Values 'A', 'B', 'C', 'D', 'E', or NULL/UNKNOWN.
60. nova_group (INT) - NOVA group classification for the product.
    - Constraints: Check between 1 and 4, or NULL/UNKNOWN.
61. pnns_groups_1 (TEXT) - PNNS group 1 for the product.
62. pnns_groups_2 (TEXT) - PNNS group 2 for the product.
63. food_groups (TEXT) - Food groups the product belongs to.
64. food_groups_tags (TEXT) - Tags related to food groups.
65. food_groups_en (TEXT) - English version of food groups.
66. states (TEXT) - States where the product is available.
67. states_tags (TEXT) - Tags related to states.
68. states_en (TEXT) - English version of states.
69. brand_owner (TEXT) - Owner of the product brand.
70. environmental_score_score (INT) - Environmental score for the product.
71. environmental_score_grade (TEXT) - Environmental score grade for the product.
72. nutrient_levels_tags (TEXT) - Tags for nutrient levels.
73. product_quantity (TEXT) - Quantity of the product.
74. owner (TEXT) - Product owner.
75. data_quality_errors_tags (TEXT) - Tags for data quality errors.
76. unique_scans_n (INT) - Number of unique scans.
77. popularity_tags (TEXT) - Tags related to popularity.
78. completeness (TEXT) - Completeness of product data.
79. last_image_t (BIGINT) - Timestamp for the last product image.
80. last_image_datetime (TIMESTAMP) - Date and time for the last product image.
81. main_category (TEXT) - Main category of the product.
82. main_category_en (TEXT) - English version of the main category.
83. image_url (TEXT) - URL for the product image.
84. image_small_url (TEXT) - URL for a small-sized product image.
85. image_ingredients_url (TEXT) - URL for the image of ingredients.
86. image_ingredients_small_url (TEXT) - URL for the small image of ingredients.
87. image_nutrition_url (TEXT) - URL for the image showing nutrition details.
88. image_nutrition_small_url (TEXT) - URL for the small image showing nutrition details.

Nutritional Information Columns:
- energy_kj_100g (FLOAT) - Energy in kilojoules per 100g.
- energy_kcal_100g (FLOAT) - Energy in kilocalories per 100g.
- fat_100g (FLOAT) - Fat content per 100g.
- saturated_fat_100g (FLOAT) - Saturated fat content per 100g.
- cholesterol_100g (FLOAT) - Cholesterol content per 100g.
- carbohydrates_100g (FLOAT) - Carbohydrates content per 100g.
- proteins_100g (FLOAT) - Protein content per 100g.
- salt_100g (FLOAT) - Salt content per 100g.
- sodium_100g (FLOAT) - Sodium content per 100g.
- fiber_100g (FLOAT) - Fiber content per 100g.
- sugars_100g (FLOAT) - Sugars content per 100g.

Additional Nutritional Details:
- Several columns describe specific acids, fatty acids, vitamins, minerals, and other components, all measured per 100g, such as vitamin_a_100g, omega_3_fat_100g, potassium_100g, iron_100g, etc.
"""


# %%
# Function to clean and process the query generated by the LLM
def clean_sql_query(generated_sql_query):
    # Remove markdown formatting (strip backticks and extra spaces)
    cleaned_query = generated_sql_query.replace("```sql", "").replace("```", "").strip()
    return cleaned_query

# %%
def execute_sql_query(sql_query):
    # Connect to your PostgreSQL database
    conn = psycopg2.connect(
        dbname="food_facts", user="postgres", password="123", host="localhost", port="5432"
    )
    cursor = conn.cursor()

    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()  # Fetch all the rows from the query
        return results
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# %%
def format_results(results, column_names=None, query_type=""):
    if results:
        formatted_result = "Based on your query, here is the top result from the database:\n"
        
        # Logic to handle queries asking for one result (e.g., best recipe, highest protein food)
        if query_type == "single_result":
            # You could add more specific logic here to choose the "best" result based on some ranking or scoring system
            result = results[0]  # For simplicity, we assume the first result is the best. You could apply additional logic for filtering.
            formatted_result += f"Here is the top result: '{result[0]}'. It is the most relevant based on your query."
        else:
            formatted_result += f"Here are the results from the database:\n"
            for result in results:
                # Default case for multiple results
                formatted_result += f"Product: {result[0]}\n"
                for i, value in enumerate(result[1:], 1):  # Skip the product name column (index 0)
                    column_name = column_names[i] if column_names else f"Field {i + 1}"
                    formatted_result += f" - {column_name}: {value if value else 'Not available'}\n"
        
        return formatted_result
    else:
        return "Sorry, no results found. It seems like we couldn't find any relevant products matching your query."

# %%
# Main function to handle the user's query and response
def process_query(user_query):
    # Step 1: Convert user query to SQL using LLM model
    ai = Custom_GenAI(API_KEY)
    sql_query = ai.ask_ai(user_query, database_schema)
    
    # Clean the generated SQL query to remove markdown formatting
    cleaned_sql_query = clean_sql_query(sql_query)
    print(f"Cleaned SQL Query: {cleaned_sql_query}")

    # Step 2: Execute the cleaned SQL query on PostgreSQL database
    query_results = execute_sql_query(cleaned_sql_query)
    print(f"Query Results: {query_results}")

    # Step 3: Determine if the query expects a single result
    query_type = "single_result" if "one" in user_query.lower() or "top" in user_query.lower() else ""
    
    # Step 4: Format the results into a user-friendly response
    formatted_output = format_results(query_results, query_type=query_type)
    return formatted_output

# %%
# Example user query
user_query = input("Please enter your query for the database: ")

# %%
# Get the response
response = process_query(user_query)
print(response)