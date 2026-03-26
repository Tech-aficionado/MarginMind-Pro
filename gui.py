# -----------------------------------------------------------------------------
# Module: gui
# Description: Tkinter-based Dashboard for Binance Futures Trading.
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import os
from dotenv import load_dotenv
from bot.client import BinanceClient
from bot.orders import place_order
from bot.logging_config import setup_logging

# Load environment variables (.env) from the script's directory.
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

class TradingBotGUI:
    """
    User Interface for the PrimeTrade.ai Binance Bot.
    Handles user input, order execution, and real-time status updates.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("PrimeTrade.ai | Futures Terminal")
        self.root.geometry("480x620")
        
        # --- UI Configuration (Premium Dark Theme) ---
        self.bg_color = "#1E1E1E"       # Deep dark background
        self.card_color = "#2D2D2D"     # Slightly lighter card background
        self.accent_color = "#007AFF"   # Electric blue accent
        self.text_color = "#FFFFFF"     # White text
        self.status_bg = "#252526"      # Status bar background
        
        self.root.configure(bg=self.bg_color)
        
        # Standard Style Config
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=self.bg_color)
        style.configure("Card.TFrame", background=self.card_color, borderwidth=1, relief="flat")
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), padding=10)
        style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), foreground="white", background=self.accent_color)
        
        # Initialize logging
        setup_logging()
        
        # --- Main Layout ---
        header_frame = ttk.Frame(root)
        header_frame.pack(fill=tk.X, pady=(20, 10))
        
        ttk.Label(header_frame, text="PRIME", font=("Segoe UI", 18, "bold"), foreground=self.accent_color).pack(side=tk.LEFT, padx=(30, 0))
        ttk.Label(header_frame, text="TRADE.AI", font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)
        
        # Main Entry Card
        card = ttk.Frame(root, style="Card.TFrame", padding="30")
        card.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Symbol Input
        ttk.Label(card, text="SYMBOL", background=self.card_color).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.symbol_entry = tk.Entry(card, bg="#3C3C3C", fg="white", insertbackground="white", font=("Consolas", 12), borderwidth=0)
        self.symbol_entry.insert(0, "BTCUSDT")
        self.symbol_entry.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 15), ipady=8)
        
        # Side & Type Row
        ttk.Label(card, text="ACTION", background=self.card_color).grid(row=2, column=0, sticky=tk.W)
        self.side_var = tk.StringVar(value="BUY")
        self.side_menu = ttk.OptionMenu(card, self.side_var, "BUY", "BUY", "SELL")
        self.side_menu.grid(row=3, column=0, sticky=tk.W, pady=(5, 15))
        
        ttk.Label(card, text="TYPE", background=self.card_color).grid(row=2, column=1, sticky=tk.W, padx=(20, 0))
        self.type_var = tk.StringVar(value="MARKET")
        self.type_menu = ttk.OptionMenu(card, self.type_var, "MARKET", "MARKET", "LIMIT", command=self.toggle_price)
        self.type_menu.grid(row=3, column=1, sticky=tk.W, padx=(20, 0), pady=(5, 15))
        
        # Quantity
        ttk.Label(card, text="QUANTITY", background=self.card_color).grid(row=4, column=0, sticky=tk.W)
        self.qty_entry = tk.Entry(card, bg="#3C3C3C", fg="white", insertbackground="white", font=("Consolas", 12), borderwidth=0)
        self.qty_entry.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(5, 15), ipady=8)
        
        # Price (with helper button)
        ttk.Label(card, text="LIMIT PRICE", background=self.card_color).grid(row=6, column=0, sticky=tk.W)
        price_subframe = tk.Frame(card, bg=self.card_color)
        price_subframe.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=(5, 15))
        
        self.price_entry = tk.Entry(price_subframe, bg="#3C3C3C", fg="gray", insertbackground="white", font=("Consolas", 12), borderwidth=0, state="disabled")
        self.price_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        
        self.auto_price_btn = tk.Button(price_subframe, text="FETCH", command=self.fetch_market_price, bg=self.accent_color, fg="white", font=("Segoe UI", 9, "bold"), borderwidth=0, padx=10)
        self.auto_price_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Execution Button
        self.btn = tk.Button(card, text="EXECUTE FUTURES TRADE", command=self.run_bot, bg="#28A745", fg="white", font=("Segoe UI", 12, "bold"), borderwidth=0, cursor="hand2")
        self.btn.grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0), ipady=12)
        
        # --- Status Terminal ---
        self.status_terminal = tk.Text(root, bg=self.status_bg, fg="#D4D4D4", font=("Consolas", 9), height=4, borderwidth=0, padx=20, pady=10)
        self.status_terminal.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_terminal.insert(tk.END, ">>> Terminal initialized. Ready for orders...")
        self.status_terminal.config(state="disabled")

    def log_status(self, message, color="#D4D4D4"):
        """Update the terminal-style status box."""
        self.status_terminal.config(state="normal")
        self.status_terminal.delete("1.0", tk.END)
        self.status_terminal.insert(tk.END, f">>> {message}")
        self.status_terminal.config(state="disabled")
        self.status_terminal.see(tk.END)

    def toggle_price(self, *args):
        """Toggle the visibility of the Price entry field based on Order Type."""
        if self.type_var.get() == "LIMIT":
            self.price_entry.config(state="normal", fg="white")
        else:
            self.price_entry.config(state="disabled", fg="gray")

    def fetch_market_price(self):
        """Fetch and display the current market price for the selected symbol."""
        sym = self.symbol_entry.get().upper()
        if not sym:
            messagebox.showwarning("Incomplete", "Please input a Symbol first.")
            return
            
        key = os.getenv("BINANCE_API_KEY")
        sec = os.getenv("BINANCE_API_SECRET")
        
        try:
            bot = BinanceClient(key, sec)
            price_data = bot.client.futures_symbol_ticker(symbol=sym)
            cur_price = price_data.get('price')
            
            self.price_entry.config(state="normal", fg="white")
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, cur_price)
            
            if self.type_var.get() != "LIMIT":
                self.price_entry.config(state="disabled", fg="gray")
                
            self.log_status(f"Live Market Price [{sym}]: {cur_price}")
            
        except Exception as e:
            messagebox.showerror("API Error", f"Sync failed: {e}")

    def run_bot(self):
        """Validate inputs and execute the trading order."""
        sym = self.symbol_entry.get().upper()
        side = self.side_var.get()
        otype = self.type_var.get()
        qty = self.qty_entry.get()
        price = self.price_entry.get() if otype == "LIMIT" else None
        
        key = os.getenv("BINANCE_API_KEY")
        sec = os.getenv("BINANCE_API_SECRET")
        
        if not key or not sec:
            messagebox.showerror("Authentication", "API Keys not detected in .env system.")
            return

        self.log_status("DISPATCHING ORDER TO BINANCE CLOUD...", "#FFB900")
        self.root.update()
        
        try:
            bot = BinanceClient(key, sec)
            res = place_order(bot, sym, side, otype, qty, price)
            
            oid = res.get('orderId')
            self.log_status(f"TRADE EXECUTED SUCCESSFULLY. ID: {oid}")
            messagebox.showinfo("Order Confirmed", f"Order {oid} has been broadcasted to the exchange.")
            
        except Exception as e:
            self.log_status(f"EXECUTION FAILED: {e}")
            messagebox.showerror("Execution Fault", str(e))

if __name__ == "__main__":
    win = tk.Tk()
    # Apply a dark theme to the window title bar if on Windows
    try:
        from ctypes import windll, byref, sizeof, c_int
        HWND = windll.user32.GetParent(win.winfo_id())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        windll.dwmapi.DwmSetWindowAttribute(HWND, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(c_int(1)), sizeof(c_int))
    except:
        pass
        
    app = TradingBotGUI(win)
    win.mainloop()
