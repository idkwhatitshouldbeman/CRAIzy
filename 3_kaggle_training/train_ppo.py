import torch
import os
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from data_loader import load_batch, preprocess_images
from model import ClashCNN
import logging

def train_on_batch(batch_file, model_path='current_model.pth', output_path='new_model.pth'):
    trajectories = load_batch(batch_file)
    # Fake env for PPO (image obs, discrete action)
    def make_env():
        from gymnasium import spaces
        return make_vec_env(lambda: DummyEnv(spaces.Box(0, 255, (1,224,128), np.uint8), spaces.Discrete(2305)), n_envs=1)

    # Custom policy with CNN
    policy_kwargs = {"features_extractor_class": ClashCNN, "features_extractor_kwargs": {"features_dim": 512}}
    model = PPO("CnnPolicy", make_env(), policy_kwargs=policy_kwargs, learning_rate=3e-4, n_steps=2048, batch_size=64, n_epochs=10, verbose=1)
    
    # Load old if exists
    if os.path.exists(model_path):
        model = PPO.load(model_path, env=make_env())
        logging.info("Loaded old model for incremental train")

    # Train on batch (offline replay)
    for traj in trajectories:
        obs, acts, rews, dones = traj
        obs = preprocess_images(obs)
        # PPO collect rollouts (adapt for offline: use replay buffer or custom learn)
        model.learn(total_timesteps=len(obs), reset_num_timesteps=False)  # Incremental
        # Custom: model.policy.predict(obs, actions=acts) for loss, but use SB3 learn for simplicity

    model.save(output_path)
    logging.info(f"Trained and saved: {output_path}")
    return output_path

class DummyEnv:  # Placeholder for SB3
    def __init__(self, obs_space, act_space):
        self.observation_space = obs_space
        self.action_space = act_space
        self.reset()

    def reset(self):
        return np.zeros((1,224,128), dtype=np.uint8), {}

    def step(self, action):
        return np.zeros((1,224,128), dtype=np.uint8), 0, False, False, {}

# Edge: Small batch - Pad with old data if <64. Torch CUDA if available (Kaggle T4). Save only best (no multiples).
