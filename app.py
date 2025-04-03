from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT UNIQUE,
            email TEXT,
            mobile TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER,
            session_id INTEGER,
            score INTEGER,
            FOREIGN KEY(team_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def serve_registration():
    return render_template('registration.html')

@app.route('/game')
def serve_game():
    return render_template('run.html')

@app.route('/register', methods=['POST'])
def register():
    team_name = request.json.get('team_name')
    email = request.json.get('email')
    mobile = request.json.get('mobile')
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (team_name) VALUES (?)", (team_name,))
        conn.commit()
        return jsonify({"message": "Registered"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"message": "Team already exists"}), 400

@app.route('/submit_score', methods=['POST'])
def submit_score():
    data = request.json
    team_name = data['team_name']
    score = data['score']
    session_id = data['session_id']
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE team_name = ?", (team_name,))
    team = c.fetchone()
    if not team:
        return jsonify({"message": "Team not registered"}), 404
    team_id = team[0]
    
    c.execute("INSERT INTO scores (team_id, session_id, score) VALUES (?, ?, ?)",
              (team_id, session_id, score))
    conn.commit()
    return jsonify({"message": "Score saved"}), 200

@app.route('/leaderboard/<int:session_id>', methods=['GET'])
def leaderboard(session_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''
        SELECT u.team_name, SUM(s.score) AS total_score
        FROM scores s
        JOIN users u ON s.team_id = u.id
        WHERE s.session_id = ?
        GROUP BY s.team_id
        ORDER BY total_score DESC
    ''', (session_id,))
    leaderboard = [{"team": row[0], "score": row[1]} for row in c.fetchall()]
    return jsonify(leaderboard)

if __name__ == '__main__':
    app.run(debug=True)
