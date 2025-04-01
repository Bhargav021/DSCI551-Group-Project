-- Add the primary key constraint to the 'code' column
ALTER TABLE products
ADD CONSTRAINT products_pkey PRIMARY KEY (code);

-- Add a unique constraint to the 'url' column
ALTER TABLE products
ADD CONSTRAINT products_url_unique UNIQUE (url);

-- Add a NOT NULL constraint to the 'product_name' column (assuming it should never be NULL)
ALTER TABLE products
ALTER COLUMN product_name SET NOT NULL;

-- Add a check constraint for 'nutriscore_score' (values between 0 and 100 or NULL/UNKNOWN)
ALTER TABLE products
ADD CONSTRAINT products_nutriscore_score_check CHECK (nutriscore_score BETWEEN 0 AND 100 OR nutriscore_score IS NULL OR nutriscore_score = 'UNKNOWN');

-- Add a check constraint for 'nutriscore_grade' (values should be 'A', 'B', 'C', 'D', 'E', NULL, or 'UNKNOWN')
ALTER TABLE products
ADD CONSTRAINT products_nutriscore_grade_check CHECK (nutriscore_grade IN ('A', 'B', 'C', 'D', 'E', NULL, 'UNKNOWN'));

-- Add a check constraint for 'nova_group' (values between 1 and 4, or NULL/UNKNOWN)
ALTER TABLE products
ADD CONSTRAINT products_nova_group_check CHECK (nova_group BETWEEN 1 AND 4 OR nova_group IS NULL OR nova_group = 'UNKNOWN');

-- Add check constraints to ensure that all nutrition-related fields are non-negative or NULL/UNKNOWN
ALTER TABLE products
ADD CONSTRAINT products_energy_kj_100g_check CHECK (energy_kj_100g >= 0 OR energy_kj_100g IS NULL OR energy_kj_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_energy_kcal_100g_check CHECK (energy_kcal_100g >= 0 OR energy_kcal_100g IS NULL OR energy_kcal_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_energy_100g_check CHECK (energy_100g >= 0 OR energy_100g IS NULL OR energy_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_energy_from_fat_100g_check CHECK (energy_from_fat_100g >= 0 OR energy_from_fat_100g IS NULL OR energy_from_fat_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_fat_100g_check CHECK (fat_100g >= 0 OR fat_100g IS NULL OR fat_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_saturated_fat_100g_check CHECK (saturated_fat_100g >= 0 OR saturated_fat_100g IS NULL OR saturated_fat_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_cholesterol_100g_check CHECK (cholesterol_100g >= 0 OR cholesterol_100g IS NULL OR cholesterol_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_carbohydrates_100g_check CHECK (carbohydrates_100g >= 0 OR carbohydrates_100g IS NULL OR carbohydrates_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_sugars_100g_check CHECK (sugars_100g >= 0 OR sugars_100g IS NULL OR sugars_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_fiber_100g_check CHECK (fiber_100g >= 0 OR fiber_100g IS NULL OR fiber_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_proteins_100g_check CHECK (proteins_100g >= 0 OR proteins_100g IS NULL OR proteins_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_salt_100g_check CHECK (salt_100g >= 0 OR salt_100g IS NULL OR salt_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_sodium_100g_check CHECK (sodium_100g >= 0 OR sodium_100g IS NULL OR sodium_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_alcohol_100g_check CHECK (alcohol_100g >= 0 OR alcohol_100g IS NULL OR alcohol_100g = 'UNKNOWN');

ALTER TABLE products
ADD CONSTRAINT products_vitamin_a_100g_check CHECK (vitamin_a_100g >= 0 OR vitamin_a_100g IS NULL OR vitamin_a_100g = 'UNKNOWN');
