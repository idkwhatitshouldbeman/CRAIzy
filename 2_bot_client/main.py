import time
import threading
import logging
from json import load as json_load
from vision_agent import VisionAgent
from game_interface import GameInterface
from server_client import ServerClient
from card_tracker import CardTracker
from image_utils import compress_screenshot

logging.basicConfig(level=logging.INFO)

def heartbeat_thread(client, interface):
    while True:
        status = "playing" if interface.is_game_active() else "waiting"
        progress = interface.get_game_time() / 180.0  # Normalize to 1
        client.send_heartbeat(status, progress)
        time.sleep(10)

def play_one_game(client, agent, interface, tracker, config):
    trajectory = []
    last_frame = 0
    metadata = {"duration_seconds": 0, "outcome": "draw", "final_crowns": {"mine": 0, "enemy": 0}}
    interface.prev_tower_hp = {'my_total': 6400, 'enemy_total': 6400, 'my_towers_down': 0, 'enemy_towers_down': 0}  # Reset

    while interface.is_game_active():
        current_time = interface.get_game_time()
        metadata["duration_seconds"] = current_time

        if current_time - last_frame >= config['frame_interval_seconds']:
            screenshot = interface.capture_screenshot()
            compressed = compress_screenshot(screenshot)
            action_id = agent.predict(compressed)
            slot, x, y = agent.decode_action(action_id)
            card_name = tracker.card_played(slot)
            interface.play_card(slot, x, y)
            reward = interface.calculate_reward()
            action_details = {"type": "play_card" if slot else "wait", "slot": slot, "card": card_name, "position": {"x": x, "y": y} if slot else None}
            trajectory.append({
                "step": len(trajectory),
                "time": current_time,
                "image": compressed['data'],
                "image_shape": compressed['shape'],
                "action": action_id,
                "action_details": action_details,
                "reward": reward
            })
            last_frame = current_time

    # End game
    outcome = interface.get_game_outcome()
    final_reward = 100 if outcome == "win" else (-100 if outcome == "loss" else 0)
    if len(trajectory) > 0:
        trajectory[-1]['reward'] += final_reward  # Add to last step
    metadata["outcome"] = outcome
    client.send_game_complete(trajectory, metadata)
    logging.info(f"Game complete: {outcome}, steps: {len(trajectory)}")
    return trajectory

if __name__ == '__main__':
    config = json_load(open('config.json'))
    client = ServerClient(config['server_url'])
    agent = VisionAgent(config['model_path'])
    interface = GameInterface()
    tracker = CardTracker(config['deck'])

    # Start heartbeat thread
    heartbeat_t = threading.Thread(target=heartbeat_thread, args=(client, interface), daemon=True)
    heartbeat_t.start()

    while True:
        allowed, reason = client.can_i_play()
        if allowed:
            logging.info(f"Playing game: {reason}")
            play_one_game(client, agent, interface, tracker, config)
        else:
            status = client.get_status()
            if status['update_available']:
                if client.download_model(config['model_path']):
                    agent.load_model()
                    logging.info("Updated to new model")
            logging.info(f"Waiting: {reason}")
            time.sleep(5)  # Poll interval

# Edge: Mid-game pause - Check is_game_active() before frame; if pause signal from status, finish if progress>0.5 else abort (rare). Crash: Thread safe, restart script reloads last model.
