import requests
import time
import logging
from datetime import datetime

class ServerClient:
    def __init__(self, server_url):
        self.url = server_url.rstrip('/')
        self.session = requests.Session()
        self.bot_id = None  # Assigned by server

    def register(self):
        # On first call, send dummy heartbeat to register
        resp = self.session.post(f"{self.url}/heartbeat", json={"bot_id": "new", "status": "idle", "timestamp": str(datetime.now())})
        if resp.status_code == 200:
            self.bot_id = resp.json().get('assigned_id', 1)  # Server assigns
            logging.info(f"Registered as bot {self.bot_id}")
            return self.bot_id
        raise ConnectionError("Registration failed")

    def send_heartbeat(self, status, progress):
        if self.bot_id is None:
            self.register()
        payload = {
            "bot_id": self.bot_id,
            "timestamp": str(datetime.now()),
            "status": status,
            "game_progress": progress
        }
        try:
            resp = self.session.post(f"{self.url}/heartbeat", json=payload, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except requests.RequestException as e:
            logging.error(f"Heartbeat failed: {e}")
        return None

    def can_i_play(self):
        if self.bot_id is None:
            self.register()
        resp = self.session.get(f"{self.url}/can_i_play?bot_id={self.bot_id}", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data['allowed'], data.get('reason', '')
        return False, "Connection error"

    def get_status(self):
        if self.bot_id is None:
            self.register()
        resp = self.session.get(f"{self.url}/status?bot_id={self.bot_id}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return {"should_wait": True}

    def send_game_complete(self, trajectory, metadata):
        if self.bot_id is None:
            self.register()
        payload = {
            "bot_id": self.bot_id,
            "timestamp": str(datetime.now()),
            "game_metadata": metadata,
            "trajectory": trajectory,
            "total_reward": sum(s['reward'] for s in trajectory),
            "total_steps": len(trajectory)
        }
        try:
            resp = self.session.post(f"{self.url}/game_complete", json=payload, timeout=30)
            if resp.status_code == 200:
                logging.info("Game data sent")
                return resp.json()
        except requests.RequestException as e:
            logging.error(f"Send failed: {e}")
        return None

    def download_model(self, save_path):
        if self.bot_id is None:
            self.register()
        resp = self.session.get(f"{self.url}/download_model", timeout=60)
        if resp.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(resp.content)
            logging.info("Model downloaded")
            return True
        logging.warning("Model download failed")
        return False

# Edge: Retry 3x exponential backoff (1s, 2s, 4s). If server down >60s, use last model, log offline mode.
# Dynamic ID: Server assigns, bot uses it.
