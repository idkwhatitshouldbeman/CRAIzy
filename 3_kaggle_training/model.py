import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

class ClashCNN(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=512):
        super().__init__(observation_space, features_dim)
        # Exact CNN for grayscale [1,224,128]
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=8, stride=4),  # Out: [32, 55, 31]
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),  # [64, 26, 14]
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),  # [64, 24, 12]
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(64 * 24 * 12, features_dim),  # Calc: 64*24*12=18432 -> 512
            nn.ReLU()
        )

    def forward(self, observations):
        return self.cnn(observations)
