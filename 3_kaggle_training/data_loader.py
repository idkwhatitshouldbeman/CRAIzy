import json
import numpy as np
import torch
from image_utils import decompress_image  # Shared, copy to folder

def load_batch(batch_file):
    with open(batch_file, 'r') as f:
        batch = json.load(f)  # List of 16 games
    trajectories = []
    for game in batch:
        traj = game['trajectory']
        obs = []
        actions = []
        rewards = []
        dones = []
        for step in traj:
            obs.append(decompress_image({"data": step['image'], "shape": step['image_shape']}))
            actions.append(step['action'])
            rewards.append(step['reward'])
            dones.append(step.get('done', False))
        trajectories.append((np.array(obs), np.array(actions), np.array(rewards), np.array(dones)))
    return trajectories  # For PPO replay

def preprocess_images(images):
    # [N, H, W] -> [N, 1, H, W] normalized
    tensor = torch.from_numpy(images).float().unsqueeze(1) / 255.0
    return tensor
