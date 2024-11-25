# app.py
from flask import Flask, request
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO user (name) VALUES ('Alice')")
    cursor.execute("INSERT INTO user (name) VALUES ('Bob')")
    conn.commit()
    return conn

conn = init_db()

@app.route('/user')
def get_user():
    user_id = request.args.get('id')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM user WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        return f"User: {user[0]}"
    else:
        return "User not found", 404

if __name__ == '__main__':
    app.run(debug=True)
