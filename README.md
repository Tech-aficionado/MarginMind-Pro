# 🛡️ MarginMind Pro - The Elite Binance Futures Terminal

**MarginMind Pro** is a high-performance, stability-hardened trading terminal for **Binance Futures**. It transforms a basic trading script into a resilient execution engine, featuring a "Fintech Pro" interface, real-time data multiplexing, and a zero-hang asynchronous architecture.

---

## 🚀 The Four Pillars of Pro

### 📡 1. High-Bandwidth Market Pulse
*   **WebSocket Multiplexing**: Instead of individual sockets, we consolidate 7+ primary assets (BTC, ETH, SOL, BNB, XRP, ADA, DOGE) into a single, synchronized multiplexed stream.
*   **Real-time Deltas**: Dynamic price tracking with high-contrast color coding (**Emerald #0ECB81** for gains, **Crimson #F6465D** for losses) and vector arrows.

### ⚡ 2. Zero-Hang Asymmetric Boot
*   **Asynchronous Handshake**: The terminal connects to the Binance cloud, performs authentication, and synchronizes time in a background thread.
*   **Instant Responsiveness**: The dashboard appears instantly upon launch, providing live status updates (`WAKING ENGINE...` -> `ENGINE ARMED`) while the engine "wakes up."

### 🛡️ 3. Resilient Self-Healing Connectivity
*   **Pulse Watchdog**: A real-time monitor detects if data ticks from the exchange stop or if the Testnet closes the connection loop.
*   **Staggered Startup**: Implements a 500ms–800ms "Secure Handshake" delay between stream initializations to prevent Testnet race conditions and "Read loop closed" errors.
*   **Automatic Recovery**: Features a zero-touch reconnection engine that restores missing pulses within seconds.

### 📜 4. Authoritative Audit Ledger
*   **Direct API Integration**: Unlike basic logs, the "Order History" tab pulls live data directly from the **Binance Futures API**.
*   **Status-Based Coloring**: Orders are color-coded by status—**FILLED**, **NEW**, or **CANCELED**—for enterprise-grade trade transparency.
*   **Full Temporal Audit**: Every trade includes a high-fidelity timestamp (YYYY-MM-DD HH:MM:SS) for total auditability.

---

## 🏗️ Technical Architecture

### **Core Engine (`BinanceClient`)**
*   **Thread-Safe Lifecycle**: Uses a `threading.Lock` to protect the WebSocket manager during reconnection cycles.
*   **Rest fallback**: Integrated REST-based "FORCE SYNC" buttons to prime price data during server-side maintenance.
*   **Precision Safety**: Automatic rounding to `stepSize` and `tickSize` ensures no "Invalid Quantity" rejections.

### **Communication (`SignalBridge`)**
*   **Decoupled Flux**: Uses PyQt6 signals to bridge data from high-frequency background threads (WebSockets) to the UI thread safely, maintaining zero-latency dashboard updates.

---

## 🛠️ Installation & Setup

### 1. Requirements
*   **Python**: 3.9+ 
*   **Core**: `python-binance`, `PyQt6`, `python-dotenv`, `qtawesome`.

```bash
pip install -r requirements.txt
```

### 2. Environment (`.env`)
Configure your Binance API credentials in the root directory:

```env
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
BINANCE_USE_TESTNET=True
```

### 3. Launch the Terminal
```bash
python gui.py
```

---

## 🎯 Project Goals & Status
*   **Stability**: Hardened for Testnet race conditions.
*   **UX**: Low-latency execution with "Fintech Pro" visuals.
*   **Integrity**: 100% accurate API-driven historical ledger.

**Status:** `VERIFIED` on Binance Futures Testnet.
