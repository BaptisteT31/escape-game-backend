from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import datetime

app = Flask(__name__)
CORS(app)

# --- Configuration PostgreSQL ---
DB_HOST = os.getenv("DB_HOST", "your_db_host")
DB_NAME = os.getenv("DB_NAME", "your_db_name")
DB_USER = os.getenv("DB_USER", "your_db_user")
DB_PASS = os.getenv("DB_PASS", "your_db_password")
DB_PORT = os.getenv("DB_PORT", "5432")

# --- Fonction pour se connecter à la base ---
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    return conn

# --- Initialisation de la base de données ---
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            current_step INTEGER DEFAULT 1,
            start_time TIMESTAMP,
            completed BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# --- Route pour créer une équipe ---
@app.route('/create_team', methods=['POST'])
def create_team():
    data = request.get_json()
    team_name = data.get('name')

    if not team_name:
        return jsonify({'error': 'Le nom de l\'équipe est requis.'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    start_time = datetime.datetime.now()
    cur.execute('INSERT INTO teams (name, start_time) VALUES (%s, %s) RETURNING id', (team_name, start_time))
    team_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': f'Équipe {team_name} créée avec succès!', 'team_id': team_id}), 201

# --- Route pour obtenir le statut d'une équipe ---
@app.route('/get_team_status', methods=['GET'])
def get_team_status():
    team_id = request.args.get('team_id')

    if not team_id:
        return jsonify({'error': 'L\'ID de l\'équipe est requis.'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT current_step, start_time, completed FROM teams WHERE id = %s', (team_id,))
    team = cur.fetchone()
    cur.close()
    conn.close()

    if not team:
        return jsonify({'error': 'Équipe non trouvée.'}), 404

    current_step, start_time, completed = team
    elapsed_time = (datetime.datetime.now() - start_time).total_seconds()

    return jsonify({'team_id': team_id, 'current_step': current_step, 'elapsed_time': elapsed_time, 'completed': completed})

# --- Route pour valider une étape ---
@app.route('/validate_step', methods=['POST'])
def validate_step():
    data = request.get_json()
    team_id = data.get('team_id')

    if not team_id:
        return jsonify({'error': 'L\'ID de l\'équipe est requis.'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT current_step FROM teams WHERE id = %s', (team_id,))
    team = cur.fetchone()

    if not team:
        cur.close()
        conn.close()
        return jsonify({'error': 'Équipe non trouvée.'}), 404

    current_step = team[0]

    if current_step >= 7:
        cur.execute('UPDATE teams SET completed = TRUE WHERE id = %s', (team_id,))
    else:
        cur.execute('UPDATE teams SET current_step = current_step + 1 WHERE id = %s', (team_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': 'Étape validée.', 'next_step': current_step + 1})

# --- Route pour récupérer les scores et progression des équipes (Page Spectateur) ---
@app.route('/get_spectator_data', methods=['GET'])
def get_spectator_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, current_step, start_time, completed FROM teams ORDER BY completed DESC, current_step DESC, start_time ASC')
    teams = cur.fetchall()
    cur.close()
    conn.close()

    teams_data = []
    for team in teams:
        team_id, name, current_step, start_time, completed = team
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
        teams_data.append({'id': team_id, 'name': name, 'current_step': current_step, 'elapsed_time': elapsed_time, 'completed': completed})

    return jsonify({'teams': teams_data})

if __name__ == '__main__':
    app.run(debug=True)
