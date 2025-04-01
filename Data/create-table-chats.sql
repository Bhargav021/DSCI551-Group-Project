-- Create chats table
CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    chat_name VARCHAR(255),
    messages TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);