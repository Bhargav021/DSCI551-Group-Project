import psycopg2
import csv
import os

def is_valid_integer(value):
    """Check if the value is a valid integer."""
    try:
        int(value)
        return True
    except ValueError:
        return False

def is_valid_float(value):
    """Check if the value is a valid float (for nutrition-related columns)."""
    try:
        float(value)
        return True
    except ValueError:
        return False

try:
    # Establish connection to PostgreSQL
    conn = psycopg2.connect(
        dbname="food_facts",
        user="postgres",
        password="123",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()

    # Check if the file exists
    file_path = 'Data\\sql_openfoodfacts_products.csv'
    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} does not exist.")
    else:
        # Open the CSV file with correct encoding
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader)  # Skip the header row

            for row in reader:
                # Validate the nutriscore_score and other numeric fields
                nutriscore_score_index = 62  # Adjust to the correct index for the column
                if not is_valid_integer(row[nutriscore_score_index]):
                    row[nutriscore_score_index] = None  # Replace invalid value with NULL

                # Validate any other numeric fields (example: energy_kcal_100g)
                energy_kcal_index = 72  # Adjust to correct index
                if not is_valid_float(row[energy_kcal_index]):
                    row[energy_kcal_index] = None  # Replace invalid value with NULL

                # You can add similar validation checks for other columns as needed

                # Now, copy the row into the database
                cursor.copy_from(f, 'products', sep='\t', null='')

        # Commit the transaction
        conn.commit()
        print("Data inserted successfully.")

except Exception as e:
    print(f"Error: {str(e)}")

finally:
    # Close the connection
    cursor.close()
    conn.close()
