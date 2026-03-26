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
        self.root.title("My Binance Dashboard - PrimeTrade.ai")
        self.root.geometry("450x550")
        
        # Initialize logging and core UI frames.
        setup_logging()
        
        # Main layout container.
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Intern Trading Bot v1.0", font=("Arial", 16, "bold")).grid(row=0, columnspan=2, pady=10)
        
        # Hardcoded to Futures as per project requirements.
        self.market_var = tk.StringVar(value="FUTURES")
        
        # Choosing the coin pair.
        ttk.Label(main_frame, text="Symbol (e.g. BTCUSDT):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.symbol_entry = ttk.Entry(main_frame)
        self.symbol_entry.insert(0, "BTCUSDT")
        self.symbol_entry.grid(row=2, column=1, sticky=tk.EW)
        
        # BUY or SELL?
        ttk.Label(main_frame, text="Action:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.side_var = tk.StringVar(value="BUY")
        ttk.OptionMenu(main_frame, self.side_var, "BUY", "BUY", "SELL").grid(row=3, column=1, sticky=tk.W)
        
        # MARKET or LIMIT?
        ttk.Label(main_frame, text="Order Type:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="MARKET")
        self.type_menu = ttk.OptionMenu(main_frame, self.type_var, "MARKET", "MARKET", "LIMIT", command=self.toggle_price)
        self.type_menu.grid(row=4, column=1, sticky=tk.W)
        
        # Amount to trade.
        ttk.Label(main_frame, text="Quantity:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.qty_entry = ttk.Entry(main_frame)
        self.qty_entry.grid(row=5, column=1, sticky=tk.EW)
        
        # Price section with the "Auto Price" button I added.
        price_frame = ttk.Frame(main_frame)
        price_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(price_frame, text="Price:").pack(side=tk.LEFT)
        self.price_entry = ttk.Entry(price_frame, state="disabled") # Disabled by default for Market orders.
        self.price_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # This button is super helpful for Limit orders!
        self.auto_price_btn = ttk.Button(price_frame, text="Get Current Price", command=self.fetch_market_price)
        self.auto_price_btn.pack(side=tk.LEFT)
        
        # The main action button.
        self.btn = ttk.Button(main_frame, text="EXECUTE ORDER", command=self.run_bot)
        self.btn.grid(row=7, columnspan=2, pady=25)
        
        # A status bar at the bottom so I can see what's happening.
        self.status_label = tk.Label(main_frame, text="Status: Ready to trade!", fg="blue", wraplength=400)
        self.status_label.grid(row=8, columnspan=2, pady=10)

    def toggle_price(self, *args):
        """Toggle the visibility of the Price entry field based on Order Type."""
        if self.type_var.get() == "LIMIT":
            self.price_entry.config(state="normal")
        else:
            self.price_entry.config(state="disabled")

    def fetch_market_price(self):
        """Fetch and display the current market price for the selected symbol."""
        sym = self.symbol_entry.get().upper()
        if not sym:
            messagebox.showwarning("Wait!", "Please enter a symbol first!")
            return
            
        mkt = self.market_var.get()
        key = os.getenv("BINANCE_API_KEY")
        sec = os.getenv("BINANCE_API_SECRET")
        
        try:
            bot = BinanceClient(key, sec)
            price_data = bot.client.futures_symbol_ticker(symbol=sym)
            
            cur_price = price_data.get('price')
            
            # Put the fetched price into the box.
            self.price_entry.config(state="normal")
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, cur_price)
            
            # If we are not in LIMIT mode, we should disable the box again.
            if self.type_var.get() != "LIMIT":
                self.price_entry.config(state="disabled")
                
            self.status_label.config(text=f"Market price for {sym}: {cur_price}", fg="green")
            
        except Exception as e:
            msg = f"Failed to get price: {e}\n\nTip: Check if your .env keys match the Testnet/Mainnet setting (BINANCE_USE_TESTNET)."
            messagebox.showerror("Error", msg)

    def run_bot(self):
        """Validate inputs and execute the trading order."""
        mkt = self.market_var.get()
        sym = self.symbol_entry.get().upper()
        side = self.side_var.get()
        otype = self.type_var.get()
        qty = self.qty_entry.get()
        price = self.price_entry.get() if otype == "LIMIT" else None
        
        # Authenticate via environment variables.
        key = os.getenv("BINANCE_API_KEY")
        sec = os.getenv("BINANCE_API_SECRET")
        
        if not key or not sec:
            messagebox.showerror("Keys Missing", "I can't find your API keys. Check your .env file!")
            return

        self.status_label.config(text="Processing... please wait.", fg="orange")
        self.root.update()
        
        try:
            # Connect, validate, and place!
            bot = BinanceClient(key, sec)
            res = place_order(bot, sym, side, otype, qty, price)
            
            oid = res.get('orderId')
            self.status_label.config(text=f"DONE! Order ID: {oid}", fg="green")
            messagebox.showinfo("Success!", f"The order was placed successfully!\nOrder ID: {oid}")
            
        except Exception as e:
            self.status_label.config(text=f"Failed: {e}", fg="red")
            msg = f"The bot ran into a problem: {e}\n\nTip: Verify your API keys in .env and ensure BINANCE_USE_TESTNET is correct."
            messagebox.showerror("Execution Error", msg)

if __name__ == "__main__":
    # Tkinter Application Entry Point.
    win = tk.Tk()
    app = TradingBotGUI(win)
    win.mainloop()
