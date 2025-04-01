from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
from llm import process_query
import hashlib
import datetime

app = Flask(__name__)
app.secret_key = '123'

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        dbname='food_facts', 
        user='postgres', 
        password='123', 
        host='localhost'
    )
    return conn

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hashing password
        
        conn = get_db_connection()
        cur = conn.cursor()
        # Check if username already exists
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        if existing_user:
            return 'Username already exists. Please choose another one.'
        
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        cur.close()
        conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session['user_id'] = user[0]  # Store user ID in session
            return redirect(url_for('index'))  # Redirect to chat
        else:
            return 'Invalid username or password!'

    return render_template('login.html')

# Index (Chat) page
@app.route('/', methods=['GET'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect users who are not logged in
    
    user_id = session['user_id']
    chat_id = request.args.get('chat_id')
    conn = get_db_connection()
    cur = conn.cursor()

    # If a chat_id is provided, load that specific chat
    if chat_id:
        cur.execute("SELECT * FROM chats WHERE user_id = %s AND id = %s", (user_id, chat_id))
        user_chats = cur.fetchall()  # Retrieve the specific chat
    else:
        cur.execute("SELECT * FROM chats WHERE user_id = %s", (user_id,))
        user_chats = cur.fetchall()  # Retrieve all chats if no chat_id is provided

    cur.close()
    conn.close()

    return render_template('index.html', chats=user_chats, current_chat_id=chat_id)

# New route to handle chat queries asynchronously
@app.route('/ask', methods=['POST'])
def ask():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_query = request.form.get('query', '').strip()
    
    if not user_query:
        return jsonify({'error': 'No Query Provided'}), 400

    try:
        query_result = process_query(user_query)  # Get result from LLM
        return {'query_result': query_result}
    except Exception as e:
        return {'error': f"Error processing query: {str(e)}"}, 500

    return jsonify({'query_result': query_result})

# Fetch chat history
@app.route('/get_chats', methods=['GET'])
def get_chats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, chat_name, messages FROM chats WHERE user_id = %s", (user_id,))
    chats = cur.fetchall()
    cur.close()
    conn.close()

    chat_list = [{'id': chat[0], 'name': chat[2]} for chat in chats]  # Corrected index to 2 for chat_name
    return jsonify({'chats': chat_list})


# Route to handle new chat creation via button
@app.route('/start_new_chat')
def start_new_chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    chat_name = 'Chat on ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create a new chat entry in the database
    cur.execute("INSERT INTO chats (user_id, chat_name, messages) VALUES (%s, %s, %s) RETURNING id", 
                (user_id, chat_name, ''))
    chat_id = cur.fetchone()[0]  
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('index', chat_id=chat_id))

if __name__ == '__main__':
    app.run(debug=True)
