from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # Autorise les requêtes cross-origin

# --- Initialisation de la base de données ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            time_elapsed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Route pour créer une équipe ---
@app.route('/create_team', methods=['POST'])
def create_team():
    data = request.get_json()
    team_name = data.get('name')

    if not team_name:
        return jsonify({'error': 'Le nom de l\'équipe est requis.'}), 400

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO teams (name) VALUES (?)', (team_name,))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Équipe {team_name} créée avec succès!'}), 201

# --- Route pour mettre à jour le score ---
@app.route('/update_score', methods=['POST'])
def update_score():
    data = request.get_json()
    team_id = data.get('team_id')
    score = data.get('score')
    time_elapsed = data.get('time_elapsed')

    if not team_id or score is None or time_elapsed is None:
        return jsonify({'error': 'Paramètres manquants.'}), 400

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        UPDATE teams SET score = ?, time_elapsed = ? WHERE id = ?
    ''', (score, time_elapsed, team_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Score mis à jour avec succès.'}), 200

# --- Route pour récupérer les scores ---
@app.route('/get_scores', methods=['GET'])
def get_scores():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, name, score, time_elapsed FROM teams ORDER BY score DESC, time_elapsed ASC')
    teams = c.fetchall()
    conn.close()

    team_list = [
        {'id': team[0], 'name': team[1], 'score': team[2], 'time_elapsed': team[3]}
        for team in teams
    ]

    return jsonify({'teams': team_list}), 200

if __name__ == '__main__':
    app.run(debug=True)
