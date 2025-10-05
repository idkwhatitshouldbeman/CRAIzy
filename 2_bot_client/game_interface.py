# Wrapper for ClashRoyaleBuildABot - assume their API/classes imported
# from ClashRoyaleBuildABot import StateReader, ActionExecutor  # Per their guide
import random
import time
import logging

class GameInterface:
    def __init__(self):
        # self.reader = StateReader(device='emulator-5554')  # Per BuildABot
        # self.executor = ActionExecutor(device='emulator-5554')
        self.prev_tower_hp = {'my_total': 6400, 'enemy_total': 6400, 'my_towers_down': 0, 'enemy_towers_down': 0}  # King+2 towers

    def capture_screenshot(self):
        # return self.reader.get_screenshot()  # np.array BGR, fixed 720x1280
        # Mock for testing
        import numpy as np
        return np.random.randint(0, 255, (1280, 720, 3), dtype=np.uint8)

    def play_card(self, slot, x, y):
        if slot is None:
            return  # Wait
        # BuildABot execute: Drag card slot to grid pos (map 24x24 to screen coords)
        screen_x = int((x / 24.0) * 720)  # Scale to emulator width
        screen_y = int((y / 24.0) * 1280)  # Height
        # self.executor.play_card(slot, screen_x, screen_y)
        time.sleep(random.uniform(0.5, 2.0))  # Human-like delay
        # Imperfect mouse: Add random offset ±5px (BuildABot supports)

    def get_tower_hp(self):
        # BuildABot reliable read: Return {'my_total': int, 'enemy_total': int, 'my_towers_down': int, 'enemy_towers_down': int}
        # return self.reader.get_tower_health()
        # Mock for testing
        return {'my_total': 6000, 'enemy_total': 5800, 'my_towers_down': 0, 'enemy_towers_down': 0}

    def is_game_active(self):
        # return self.reader.is_in_battle()
        # Mock for testing
        return True

    def get_game_outcome(self):
        # Post-game: 'win'/'loss'/'draw' from reader
        # return self.reader.get_battle_result()
        # Mock for testing
        return 'win'

    def get_game_time(self):
        # return self.reader.get_battle_time()  # Seconds elapsed
        # Mock for testing
        return 120

    def calculate_reward(self):
        current = self.get_tower_hp()
        reward = 0.0
        enemy_dmg = self.prev_tower_hp['enemy_total'] - current['enemy_total']
        reward += enemy_dmg * 0.01
        my_dmg = self.prev_tower_hp['my_total'] - current['my_total']
        reward -= my_dmg * 0.01
        if current['enemy_towers_down'] > self.prev_tower_hp['enemy_towers_down']:
            reward += 50
        if current['my_towers_down'] > self.prev_tower_hp['my_towers_down']:
            reward -= 50
        reward -= 0.1  # Step penalty
        self.prev_tower_hp = current
        return reward

# Edge: If BuildABot fail (e.g., emulator disconnect), log, retry 3x, then 'crashed' status to server.
