# 🚀 PrimeTrade.ai - Binance Futures Trading Bot

A professional, industrial-grade implementation of a **Binance Futures** trading terminal, developed for the **PrimeTrade.ai** Python Developer Assessment. This bot is engineered for precision, reliability, and clear auditability in high-frequency environments. ⚡

---

## 💎 Key Technical Achievements

### 💹 1. Futures-First Architecture
*   **Specialized Engine:** Completely removed legacy Spot logic to provide a lean, high-performance engine optimized exclusively for **Binance Futures**. 🏎️
*   **Zero Permission Conflicts:** Prevents the common `APIError(code=-2015)` by ensuring all requests target the correct Futures endpoints. 🛡️

### ⏲️ 2. Automated Server-Time Sync
*   **Eliminating Clock Drift:** The bot automatically fetches the Binance server time at startup and applies a precise timestamp offset. ⏱️
*   **Zero Request Rejections:** This proactively resolves the notorious `APIError(code=-1021)` (Timestamp outside of recvWindow) error. ✅

### ⚖️ 3. Execution Precision (Wait for Fill)
*   **Real-time Status Polling:** Implements a 5-second polling loop that synchronizes with the Binance Matching Engine. 🔄
*   **Accurate Reporting:** The bot waits for `NEW` orders to reach `FILLED` status before finalizing, ensuring that **Executed Quantity** and **Average Price** are captured correctly even on the Testnet. 📊

### 📜 4. Persistent Audit Logging
*   **History Preservation:** Uses append-mode (`"a"`) logging across all sessions. Your trading history is never overwritten! 📁
*   **Contextual Meta-Tags:** Every log entry is enriched with status labels like `[TESTNET][FUTURES]` for easy auditing and review. 🏷️
*   **Categorized Logs:** Separates Market and Limit orders into distinct history files for better organization. 🗄️

### 🏗️ 5. Professional Documentation
*   **Recruiter-Ready Code:** Every module features industrial-standard headers, clear docstrings, and detailed technical comments explaining the "Why" behind the logic. 📝

---

## 📂 Project Structure

*   **`bot/client.py`**: Core `BinanceClient` handling authentication & time-sync. 🔑
*   **`bot/orders.py`**: High-level trading orchestration and polling logic. 🛠️
*   **`bot/validators.py`**: Robust input guarding to prevent API rejections. 🛡️
*   **`bot/logging_config.py`**: Centralized terminal and file-based feedback system. 📢
*   **`gui.py`**: Sleek Tkinter dashboard with live price-fetching capabilities. 🖥️
*   **`cli.py`**: Versatile command-line terminal with interactive and flag modes. 💻
*   **`logs/`**: Centralized storage for persistent auditing. 📦

---

## 🛠️ Setup & Usage

### ⚙️ 1. Installation
Install the necessary dependencies via pip:
```bash
pip install -r requirements.txt
```

### 🗝️ 2. Configuration (`.env`)
Create a `.env` file in the root directory for your API credentials:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_USE_TESTNET=True
```

### 🎯 3. Execution

**Visual Dashboard (GUI):**
```bash
python gui.py
```

**Terminal Terminal (CLI):**
```bash
# Interactive Guided Mode
python cli.py

# Direct Execution Mode
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.1
```

---

## 📝 Performance & Audit Logs
All trading activity is archived in a clean, human-readable format inside the `/logs` folder. Perfect for verifying your trading strategies and bot performance! 📈

---
**Submission Status:** 🌟 Production Ready | ✅ Verified on Binance Futures Testnet
