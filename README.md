# CRAIzy - Clash Royale AI System

A complete, working Clash Royale AI system using pure reinforcement learning (PPO) with vision-based input. The AI learns to play competitively with a fixed beatdown deck, deciding the best move (card + position or "wait") from grayscale screenshots alone.

## 🎯 Project Overview

This system uses reinforcement learning to train an AI that can play Clash Royale competitively. The AI learns purely through trial and error in real games on burner accounts, using only screenshot input - no manual feature extraction.

### Key Features
- **Vision-Based Learning**: Input is grayscale screenshots every 3 seconds
- **PPO Algorithm**: Uses Stable-Baselines3 with CNN policy
- **Fixed Beatdown Deck**: 8-card deck with 3.6 average elixir
- **Scalable Architecture**: Supports multiple bots across VMs
- **Real-time Dashboard**: Web UI for monitoring training progress

## 🏗️ Architecture

The system consists of 3 main components:

### 1. Central Server (`1_central_server/`)
- **server.py**: Flask REST API server
- **state_manager.py**: Manages bot states and game data
- **kaggle_client.py**: Handles training data and model updates
- **UI Dashboard**: Real-time monitoring at `http://localhost:5000/ui`

### 2. Bot Client (`2_bot_client/`)
- **main.py**: Main bot loop and game playing logic
- **vision_agent.py**: AI model for action prediction
- **game_interface.py**: BuildABot wrapper for game interaction
- **server_client.py**: Communication with central server

### 3. Kaggle Training (`3_kaggle_training/`)
- **train_ppo.py**: PPO training implementation
- **model.py**: CNN architecture
- **data_loader.py**: Batch data processing

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Windows 10/11 (for Hyper-V VMs)
- Android emulator (BlueStacks 5 recommended)
- Clash Royale installed on emulator

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/idkwhatitshouldbeman/CRAIzy.git
cd CRAIzy
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup BuildABot:**
Follow the [ClashRoyaleBuildABot guide](https://github.com/Pbatch/ClashRoyaleBuildABot) to install and configure BuildABot in your emulator.

### Running the System

#### Phase 1: Single Bot Setup
1. **Start the server:**
```bash
cd 1_central_server
python server.py
```

2. **Run a bot client:**
```bash
cd 2_bot_client
python main.py
```

3. **Monitor progress:**
Open `http://localhost:5000/ui` in your browser

#### Phase 2: Multi-Bot Setup
1. Create Hyper-V VMs (Windows, 4GB RAM, 2 cores each)
2. Install Python, BlueStacks, Clash Royale, and BuildABot in each VM
3. Copy the `2_bot_client/` folder to each VM
4. Start the server on the host
5. Start bots in each VM

## 🎮 Deck Configuration

The AI uses a fixed beatdown deck:
- **Knight** (3 elixir, Lv2)
- **Valkyrie** (3 elixir, Lv3) 
- **Minions** (3 elixir, Lv1)
- **Arrows** (3 elixir, Lv1)
- **Fireball** (4 elixir, Lv3)
- **Giant** (5 elixir, Lv3)
- **Pekka** (4 elixir, Lv3)
- **Dark Prince** (4 elixir, Lv4)

Average elixir: 3.6

## 🧠 AI Learning Process

### Input Processing
- **Screenshots**: Grayscale, 224x128 resolution
- **Compression**: JPEG Q=40, base64 encoded (~3-5KB/frame)
- **Frame Rate**: Every 3 seconds during gameplay

### Action Space
- **Discrete Actions**: 2305 total actions
- **Card Slots**: 4 slots × 576 positions (24×24 grid)
- **Wait Action**: Action 2304 = "wait"
- **Encoding**: `action_id = slot * 576 + (y * 24 + x)`

### Rewards
- **Per Step**: +0.01/HP enemy damage, -0.01/HP my damage
- **Tower Destroy**: +50 enemy tower, -50 my tower
- **Step Penalty**: -0.1 per step
- **Game End**: +100 win, -100 loss, 0 draw

## 📊 Training Process

1. **Data Collection**: Bots play real matches (3-5 minutes each)
2. **Batch Size**: 17 games collected, train on first 16
3. **Training**: PPO with CNN policy on Kaggle
4. **Model Update**: New model distributed to all bots
5. **Cycle**: Continuous learning and improvement

## 🔧 Configuration

### Server Config (`1_central_server/config.json`)
```json
{
  "host": "0.0.0.0",
  "port": 5000,
  "batch_size": 16,
  "safety_games": 17,
  "heartbeat_interval": 10,
  "heartbeat_timeout": 30
}
```

### Bot Config (`2_bot_client/config.json`)
```json
{
  "server_url": "http://192.168.86.21:5000",
  "deck": ["knight", "valkyrie", "minions", "arrows", "fireball", "giant", "pekka", "dark_prince"],
  "frame_interval_seconds": 3,
  "action_space_size": 2305,
  "image_size": {"height": 224, "width": 128}
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **Server Connection Failed**
   - Check firewall settings: `netsh advfirewall firewall add rule name='ClashServer' dir=in action=allow protocol=TCP localport=5000`
   - Verify IP address in bot config

2. **BuildABot Connection Issues**
   - Ensure emulator is running on port 5554
   - Check ADB connection: `adb devices`
   - Restart emulator if needed

3. **Model Loading Errors**
   - Ensure model file exists in `models/` directory
   - Check file permissions
   - Verify PyTorch installation

### Performance Optimization

- **Storage**: Delete old batch files after training
- **Memory**: Monitor RAM usage with multiple bots
- **Network**: Use wired connection for stability

## 📈 Monitoring

### Dashboard Features
- **Server Status**: Collecting/Training/Ready
- **Bot Status**: Individual bot states and progress
- **Game Progress**: Games completed per bot
- **Model Version**: Current model version
- **Recent Events**: Log of system events

### Logs
- Server logs: Console output
- Bot logs: Individual bot console
- Training logs: Kaggle notebook output

## 🔒 Security & Ethics

### Burner Accounts
- Use training camp and low ladder to avoid reports
- Create accounts via Supercell ID (email/phone)
- Link accounts to emulator for testing

### Detection Avoidance
- Random delays (0.5-2s) between actions
- Imperfect mouse movements
- Human-like play patterns

## 📚 Technical Details

### CNN Architecture
```
Input: [1, 224, 128] grayscale
Conv2d(1→32, 8×8, stride=4) → [32, 55, 31]
ReLU
Conv2d(32→64, 4×4, stride=2) → [64, 26, 14]  
ReLU
Conv2d(64→64, 3×3, stride=1) → [64, 24, 12]
ReLU
Flatten → 18432
Linear(18432→512)
ReLU
```

### PPO Hyperparameters
- **Learning Rate**: 3e-4
- **N Steps**: 2048
- **Batch Size**: 64
- **N Epochs**: 10
- **Total Timesteps**: 2,000,000 (incremental)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE.md file for details.

## 🙏 Acknowledgments

- [ClashRoyaleBuildABot](https://github.com/Pbatch/ClashRoyaleBuildABot) for game automation
- [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) for RL algorithms
- [OpenCV](https://opencv.org/) for image processing

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the BuildABot documentation

---

**Note**: This is a hobby project for educational purposes. Use responsibly and in accordance with Clash Royale's terms of service.