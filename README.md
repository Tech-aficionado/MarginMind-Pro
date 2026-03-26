# Binance Trading Bot - Final Assignment Submission

This is the complete, humanized trading bot developed for the PrimeTrade.ai Python Developer internship. It supports both Spot and Futures testnets with CLI and GUI interfaces.

## Final Project Structure:
- `bot/`: Core logic package (Client, Orders, Validators, Logging).
- `logs/`: Centralized folder for all output logs.
- `cli.py`: Command-line tool (Interactive or with flags).
- `gui.py`: Visual dashboard with **Auto-Price** fetching.
- `.env`: API credentials (Key & Secret).
- `requirements.txt`: Project dependencies.
- `README.md`: This file.

## How to use:

### 1. Requirements
```bash
pip install -r requirements.txt
```

### 2. Running the Tools
You can now run everything directly from this folder:

**GUI (Visual Interface)**:
```bash
python gui.py
```

**CLI (Terminal Interface)**:
```bash
# Interactive mode
python cli.py

# Single command (Example)
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

## Note for Evaluators:
The project has been organized for root execution to make it easier to navigate. All logs are stored in the `/logs` directory for cleanliness.
