CREATE ROLE food_user WITH LOGIN ENCRYPTED PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE food_facts TO food_user;
ALTER ROLE food_user CREATEDB;  -- Optional if you want to allow creating new databases
