import torch
import random
import logging
from image_utils import decompress_image

class VisionAgent:
    def __init__(self, model_path, action_size=2305):
        self.model_path = model_path
        self.action_size = action_size
        self.model = None
        self.load_model()

    def load_model(self):
        try:
            self.model = torch.load(self.model_path)  # PPO policy
            self.model.eval()
            logging.info("Model loaded")
        except FileNotFoundError:
            logging.warning("No model - using random actions")
            self.model = None

    def predict(self, compressed_image):
        if self.model is None:
            # Random for initial
            return random.randint(0, self.action_size - 1)
        img = decompress_image(compressed_image)
        img_tensor = torch.from_numpy(img).float().unsqueeze(0).unsqueeze(0) / 255.0  # [1,1,H,W]
        with torch.no_grad():
            action, _ = self.model.predict(img_tensor, deterministic=False)  # PPO predict
        return int(action)

    def encode_action(self, slot, x, y):
        if slot is None:
            return 2304  # Wait
        pos_id = y * 24 + x
        return slot * 576 + pos_id

    def decode_action(self, action_id):
        if action_id == 2304:
            return None, None, None
        slot = action_id // 576
        pos_id = action_id % 576
        x = pos_id % 24
        y = pos_id // 24
        return slot, x, y

# Edge: Invalid action (e.g., low elixir? Log, but play anyway - AI learns). Reload model after download.
