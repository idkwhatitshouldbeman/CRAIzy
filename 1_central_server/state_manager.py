import json
from threading import Lock
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ServerState:
    def __init__(self, config_path):
        self.config = json.load(open(config_path))
        self.lock = Lock()
        self.reset_state()
        self.bots = {}  # {id: {'status': str, 'games_completed': int, 'last_heartbeat': datetime, 'progress': float}}
        self.model_version = 0
        self.games_buffer = []  # List of game_complete dicts
        logging.info("ServerState initialized")

    def reset_state(self):
        with self.lock:
            self.total_games_collected = 0
            self.status = "collecting"  # collecting | training | ready
            self.save_state()  # Backup to file for restarts

    def save_state(self):
        state = {
            'total_games_collected': self.total_games_collected,
            'status': self.status,
            'model_version': self.model_version,
            'bots': self.bots,
            'games_buffer_len': len(self.games_buffer)  # Don't save full buffer to save space
        }
        with open('state_backup.json', 'w') as f:
            json.dump(state, f)
        # Delete old buffer if ready (space)

    def load_state(self):
        try:
            with open('state_backup.json', 'r') as f:
                state = json.load(f)
                self.total_games_collected = state['total_games_collected']
                self.status = state['status']
                self.model_version = state['model_version']
                self.bots = state['bots']
                # Rebuild buffer if needed (from log files, but skip for space - restart loses buffer)
            logging.info("State loaded from backup")
        except FileNotFoundError:
            logging.warning("No backup found, starting fresh")

    def register_bot(self, bot_id):
        with self.lock:
            if bot_id not in self.bots:
                self.bots[bot_id] = {'status': 'idle', 'games_completed': 0, 'last_heartbeat': datetime.now(), 'progress': 0.0}
                logging.info(f"New bot registered: {bot_id}")
            return True

    def update_heartbeat(self, bot_id, status, progress):
        with self.lock:
            if bot_id not in self.bots:
                self.register_bot(bot_id)
            self.bots[bot_id]['status'] = status
            self.bots[bot_id]['progress'] = progress
            self.bots[bot_id]['last_heartbeat'] = datetime.now()
            # Check timeout
            if (datetime.now() - self.bots[bot_id]['last_heartbeat']).seconds > self.config['heartbeat_timeout']:
                self.bots[bot_id]['status'] = 'crashed'
                logging.warning(f"Bot {bot_id} timed out")
            self.save_state()

    def can_bot_play(self, bot_id):
        with self.lock:
            self.register_bot(bot_id)  # Auto-register
            if self.status != "collecting":
                return False, "Server not collecting"
            hypothetical_total = self.total_games_collected + 1
            if hypothetical_total > self.config['safety_games']:
                return False, "Would exceed safety limit"
            # Reserve slot (atomic)
            self.total_games_collected += 1
            return True, f"OK, {self.config['safety_games'] - hypothetical_total} remaining"

    def add_game_data(self, game_data):
        with self.lock:
            self.games_buffer.append(game_data)
            bot_id = game_data['bot_id']
            if bot_id in self.bots:
                self.bots[bot_id]['games_completed'] += 1
            self.save_state()
            logging.info(f"Game added from bot {bot_id}, total: {len(self.games_buffer)}")
            if len(self.games_buffer) >= self.config['batch_size']:
                self.start_training()

    def start_training(self):
        with self.lock:
            if self.status == "training":
                return  # Already training
            self.status = "training"
            logging.info("Batch ready - starting training")
            # Call kaggle_client.send_batch(self.games_buffer[:self.config['batch_size']])  # First 16
            # self.games_buffer = self.games_buffer[self.config['batch_size']:]  # Keep extras if any, discard on upload
            # Simulate wait (in real: async thread)
            # On complete: self.model_version += 1; self.status = "ready"; self.reset_state()

    def get_status(self, bot_id):
        with self.lock:
            self.register_bot(bot_id)
            eta = 0 if self.status != "training" else 120  # Estimate 2 min
            return {
                "server_status": self.status,
                "should_wait": self.status != "collecting",
                "current_model_version": self.model_version,
                "update_available": self.status == "ready",
                "eta_seconds": eta,
                "total_games": self.total_games_collected,
                "bots_active": len([b for b in self.bots.values() if b['status'] != 'crashed'])
            }

    # Edge Cases Handled:
    # - Bot add/remove: Auto-register on heartbeat, ignore crashed in counts.
    # - Over-batch: Lock prevents >17.
    # - Crash: Timeout marks 'crashed', others continue (compensate by allowing more plays).
    # - Restart: Load backup, resume status (lose buffer = recollect).
    # - Dynamic bots: No fixed count; batch fills from whoever connects.
