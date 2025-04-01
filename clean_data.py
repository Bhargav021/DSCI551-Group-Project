import pandas as pd
import numpy as np

# File paths
INPUT_FILE = "Data/sql_openfoodfacts_products.csv"
OUTPUT_FILE = "Data/sql_openfoodfacts_products_cleaned.csv"

# Step 1: Read a small sample to detect column types
sample_size = 1000
df_sample = pd.read_csv(INPUT_FILE, delimiter='\t', encoding='utf-8', nrows=sample_size, low_memory=False)

# Automatically detect column data types
detected_dtypes = {}
for col in df_sample.columns:
    # Try converting to numeric to see if it's a number
    if pd.to_numeric(df_sample[col], errors='coerce').notna().sum() > (0.9 * sample_size):  
        detected_dtypes[col] = "float32"  # If >90% are numbers, treat as float
    else:
        detected_dtypes[col] = "string"  # Otherwise, treat as string

# Log detected data types
print("Detected Data Types:\n", detected_dtypes)

# Step 2: Process the full dataset in chunks with detected types
chunksize = 100000
bad_rows_count = 0

with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f_out:
    header_written = False

    for chunk in pd.read_csv(INPUT_FILE, delimiter='\t', encoding='utf-8', 
                             dtype=str, chunksize=chunksize, 
                             usecols=df_sample.columns, on_bad_lines='skip', 
                             low_memory=False):

        # Step 3: Convert columns based on detected types
        for col, dtype in detected_dtypes.items():
            if col in chunk.columns:
                if dtype == "float32":
                    chunk[col] = pd.to_numeric(chunk[col], errors='coerce')  # Convert bad values to NaN
                elif dtype == "string":
                    chunk[col] = chunk[col].fillna("Unknown")  # Fill missing strings

        # Track invalid numeric values
        invalid_rows = chunk.isnull().sum().sum()
        bad_rows_count += invalid_rows

        # Drop duplicates based on 'code'
        if "code" in chunk.columns:
            chunk.drop_duplicates(subset=["code"], keep="first", inplace=True)

        # Write cleaned data (header only once)
        chunk.to_csv(f_out, sep='\t', index=False, header=not header_written, mode='a')
        header_written = True

print(f"Data cleaning complete! Cleaned file saved as: {OUTPUT_FILE}")
print(f"{bad_rows_count} bad numeric values were found and replaced with NaN.")
