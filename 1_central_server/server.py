from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from state_manager import ServerState
from kaggle_client import send_batch_to_kaggle
import logging
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # For VM cross-origin
state = ServerState('config.json')  # Load config
state.load_state()  # Restore on start

logging.basicConfig(level=logging.INFO)

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    bot_id = data['bot_id']
    status = data['status']
    progress = data.get('game_progress', 0.0)
    state.update_heartbeat(bot_id, status, progress)
    return jsonify({"acknowledged": True, "server_status": state.get_status(bot_id)})

@app.route('/can_i_play')
def can_i_play():
    bot_id = request.args.get('bot_id')
    allowed, reason = state.can_bot_play(bot_id)
    return jsonify({"allowed": allowed, "reason": reason})

@app.route('/game_complete', methods=['POST'])
def game_complete():
    data = request.json
    bot_id = data['bot_id']
    state.add_game_data(data)
    return jsonify({
        "received": True,
        "total_games": state.total_games_collected,
        "games_until_batch": state.config['safety_games'] - state.total_games_collected
    })

@app.route('/status')
def status():
    bot_id = request.args.get('bot_id')
    return jsonify(state.get_status(bot_id))

@app.route('/download_model')
def download_model():
    model_path = state.config['model_save_path']
    if os.path.exists(model_path):
        return send_file(model_path, as_attachment=False)
    else:
        return "Model not ready", 404

@app.route('/ui')
def ui():
    # Render dashboard with state
    bots_list = "\n".join([f"<tr><td>{id}</td><td>{b['status']}</td><td>{b['progress']:.2f}</td><td>{b['games_completed']}</td></tr>" for id, b in state.bots.items()])
    recent_events = "Log: Bot1 connected, Game from Bot3 added..."  # From log file parse, or in-memory list
    html = render_template_string(ui_template, bots=bots_list, status=state.status, games=state.total_games_collected, version=state.model_version, events=recent_events)
    return html

# Exact HTML for ui_template (clean table, CSS for mobile/resize)
ui_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Clash Royale AI Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body { font-family: Arial; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .status { font-weight: bold; }
    </style>
</head>
<body>
    <h1>Clash Royale AI Dashboard</h1>
    <p>Server Status: <span class="status">{{ status }}</span></p>
    <p>Games Collected: {{ games }}/17 (Train on 16)</p>
    <p>Model Version: {{ version }}</p>
    <h2>Bots Status</h2>
    <table>
        <tr><th>Bot ID</th><th>Status</th><th>Progress</th><th>Games Done</th></tr>
        {{ bots }}
    </table>
    <h2>Recent Events</h2>
    <pre>{{ events }}</pre>
</body>
</html>
"""

if __name__ == '__main__':
    logging.info("Starting server on 192.168.86.21:5000")
    app.run(host=state.config['host'], port=state.config['port'], debug=False)
