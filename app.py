from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import datetime

app = Flask(__name__)
CORS(app)

# --- Configuration PostgreSQL ---
DB_HOST = os.getenv("DB_HOST", "dpg-cutkc1d6l47c73a6kntg-a.oregon-postgres.render.com")
DB_NAME = os.getenv("DB_NAME", "escape_game_db")
DB_USER = os.getenv("DB_USER", "escape_game_db_user")
DB_PASS = os.getenv("DB_PASS", "0mPOqxzc51tk0GCtyJH2kAx7dDugHbEp")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    """Ouvre une connexion à PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        print("✅ Connexion à PostgreSQL réussie !")
        return conn
    except psycopg2.OperationalError as e:
        print("❌ Erreur de connexion à PostgreSQL :", e)
        return None

def init_db():
    """Initialisation de la base de données."""
    conn = get_db_connection()
    if conn is None:
        print("❌ Impossible d'initialiser la base : connexion échouée.")
        return

    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            current_step INTEGER DEFAULT 1,
            start_time TIMESTAMP DEFAULT NOW(),
            completed BOOLEAN DEFAULT FALSE,
            score INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Base de données initialisée.")

# --- ROUTES FLASK ---
@app.route('/create_team', methods=['POST'])
def create_team():
    """Création d'une équipe."""
    data = request.get_json()
    team_name = data.get('name')

    if not team_name:
        return jsonify({'error': "Le nom de l'équipe est requis."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': "Impossible de se connecter à la base de données."}), 500

    cur = conn.cursor()
    start_time = datetime.datetime.now()
    cur.execute('INSERT INTO teams (name, start_time) VALUES (%s, %s) RETURNING id', (team_name, start_time))
    team_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': f"Équipe {team_name} créée avec succès!", 'team_id': team_id}), 201

@app.route('/update_score', methods=['POST'])
def update_score():
    """Mise à jour du score d'une équipe."""
    data = request.get_json()
    team_id = data.get('team_id')
    score = data.get('score')

    if not team_id or score is None:
        return jsonify({'error': "L'ID de l'équipe et le score sont requis."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': "Impossible de se connecter à la base de données."}), 500

    cur = conn.cursor()
    cur.execute('UPDATE teams SET score = score + %s WHERE id = %s', (score, team_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': f"Score mis à jour de {score} points pour l'équipe {team_id}."}), 200

@app.route('/get_team_status', methods=['GET'])
def get_team_status():
    """Récupération du statut d'une équipe."""
    team_id = request.args.get('team_id')

    if not team_id:
        return jsonify({'error': "L'ID de l'équipe est requis."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': "Impossible de se connecter à la base de données."}), 500

    cur = conn.cursor()
    cur.execute('SELECT current_step, start_time, completed, score FROM teams WHERE id = %s', (team_id,))
    team = cur.fetchone()
    cur.close()
    conn.close()

    if not team:
        return jsonify({'error': "Équipe non trouvée."}), 404

    current_step, start_time, completed, score = team
    elapsed_time = (datetime.datetime.now() - start_time).total_seconds() if start_time else 0

    return jsonify({
        'team_id': team_id,
        'current_step': current_step,
        'elapsed_time': elapsed_time,
        'completed': completed,
        'score': score
    })

@app.route('/validate_step', methods=['POST'])
def validate_step():
    """Validation d'une étape pour une équipe."""
    data = request.get_json()
    team_id = data.get('team_id')

    if not team_id:
        return jsonify({'error': "L'ID de l'équipe est requis."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': "Impossible de se connecter à la base de données."}), 500

    cur = conn.cursor()
    cur.execute('SELECT current_step FROM teams WHERE id = %s', (team_id,))
    team = cur.fetchone()

    if not team:
        cur.close()
        conn.close()
        return jsonify({'error': "Équipe non trouvée."}), 404

    current_step = team[0]

    if current_step >= 7:
        cur.execute('UPDATE teams SET completed = TRUE WHERE id = %s', (team_id,))
    else:
        cur.execute('UPDATE teams SET current_step = current_step + 1 WHERE id = %s', (team_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': "Étape validée.", 'next_step': current_step + 1})

@app.route('/get_spectator_data', methods=['GET'])
def get_spectator_data():
    """Récupération des données pour la page spectateur."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': "Impossible de se connecter à la base de données."}), 500

    cur = conn.cursor()
    cur.execute('SELECT id, name, current_step, start_time, completed, score FROM teams ORDER BY score DESC, completed DESC, current_step DESC, start_time ASC')
    teams = cur.fetchall()
    cur.close()
    conn.close()

    teams_data = []
    for team in teams:
        team_id, name, current_step, start_time, completed, score = team
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds() if start_time else 0
        teams_data.append({
            'id': team_id,
            'name': name,
            'current_step': current_step,
            'elapsed_time': elapsed_time,
            'completed': completed,
            'score': score
        })

    return jsonify({'teams': teams_data})

def log_flask_routes():
    """Affiche les routes de l'application pour le debug."""
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    print("✅ Routes Flask disponibles :", routes)

# --- MAIN ---
if __name__ == '__main__':
    init_db()  # Initialise la base
    log_flask_routes()  # Log des routes
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
