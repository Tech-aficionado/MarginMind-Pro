import sys
import os
import logging
import threading
import time
from datetime import datetime
from dotenv import load_dotenv

try:
    import qta
except ImportError:
    qta = None

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QComboBox, QTabWidget, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
    QMessageBox, QTextEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon

from bot.client import BinanceClient
from bot.orders import calculate_position_size, place_order

absolute_application_path = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(absolute_application_path, ".env"))
TRADING_SESSION_LOG = os.path.join(absolute_application_path, "logs", "trading_bot.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(TRADING_SESSION_LOG),
        logging.StreamHandler(sys.stdout)
    ]
)

MONITORED_TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]

class ApplicationSignalBridge(QObject):
    pulse_received = pyqtSignal(dict)
    data_refreshed = pyqtSignal(object) 
    log_updated = pyqtSignal(str)
    status_msg = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    engine_armed = pyqtSignal()

class TradingTerminalInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MarginMind Pro - Advanced Trading Terminal")
        self.setMinimumSize(1300, 950)
        
        self.last_known_prices = {}
        self.last_log_read_position = 0
        self.current_pulse_status_count = 0
        self.is_reconnecting_active = False
        self.communication_bridge = ApplicationSignalBridge()
        
        self.communication_bridge.pulse_received.connect(self.process_pulse_update)
        self.communication_bridge.data_refreshed.connect(self.update_user_interface)
        self.communication_bridge.log_updated.connect(self.append_text_to_console)
        self.communication_bridge.status_msg.connect(lambda msg_text: self.connection_status_text_label.setText(msg_text.upper()))
        self.communication_bridge.error_occurred.connect(self.display_error_dialog)
        self.communication_bridge.engine_armed.connect(self.on_engine_startup_complete)
        
        self.initialize_ui_components()
        self.apply_visual_styles()
        
        self.background_log_timer = QTimer()
        self.background_log_timer.timeout.connect(self.read_new_log_lines)
        self.background_log_timer.start(1000)
        
        self.system_clock_timer = QTimer()
        self.system_clock_timer.timeout.connect(self.update_terminal_clock)
        self.system_clock_timer.start(1000)
        
        QTimer.singleShot(100, self.begin_async_initialization)

    def initialize_ui_components(self):
        root_container = QWidget()
        self.setCentralWidget(root_container)
        
        master_layout = QVBoxLayout(root_container)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)

        self.header_panel = QFrame()
        self.header_panel.setObjectName("Header")
        self.header_panel.setFixedHeight(95)
        
        header_content_layout = QHBoxLayout(self.header_panel)
        header_content_layout.setContentsMargins(40, 0, 40, 0)
        
        branding_vertical_layout = QVBoxLayout()
        self.logo_label = QLabel("MARGINMIND <span style='color:#0ECB81'>PRO</span>")
        self.logo_label.setObjectName("Logo")
        branding_vertical_layout.addWidget(self.logo_label)
        
        self.environment_status_label = QLabel("BINANCE FUTURES TESTNET LIVE")
        self.environment_status_label.setObjectName("EnvLbl")
        branding_vertical_layout.addWidget(self.environment_status_label)
        
        header_content_layout.addLayout(branding_vertical_layout)
        header_content_layout.addStretch()
        
        ticker_display_layout = QVBoxLayout()
        self.current_symbol_display = QLabel("BTCUSDT")
        self.current_symbol_display.setObjectName("CurSym")
        self.market_price_indicator = QLabel("CONNECTING...")
        self.market_price_indicator.setObjectName("PriceMain")
        
        ticker_display_layout.addWidget(self.current_symbol_display, 0, Qt.AlignmentFlag.AlignRight)
        ticker_display_layout.addWidget(self.market_price_indicator, 0, Qt.AlignmentFlag.AlignRight)
        
        header_content_layout.addLayout(ticker_display_layout)
        master_layout.addWidget(self.header_panel)

        main_content_area = QHBoxLayout()
        main_content_area.setContentsMargins(30, 30, 30, 30)
        main_content_area.setSpacing(30)
        
        sidebar_vertical_layout = QVBoxLayout()
        sidebar_vertical_layout.setSpacing(25)
        
        self.equity_summary_card = self.create_ui_card("ACCOUNT EQUITY", "fa5s.wallet")
        self.balance_value_label = QLabel("$0.00")
        self.balance_value_label.setObjectName("BigBal")
        self.equity_summary_card.layout().addWidget(self.balance_value_label)
        
        self.unrealized_pnl_label = QLabel("PnL: $0.00")
        self.unrealized_pnl_label.setObjectName("PnLSub")
        self.equity_summary_card.layout().addWidget(self.unrealized_pnl_label)
        
        refresh_all_btn = QPushButton(" REFRESH ALL STREAMS")
        self.equity_summary_card.layout().addWidget(refresh_all_btn)
        
        if qta:
            refresh_all_btn.setIcon(qta.icon("fa5s.sync-alt", color="white"))
        refresh_all_btn.clicked.connect(self.trigger_manual_sync)
        sidebar_vertical_layout.addWidget(self.equity_summary_card)
        
        self.market_pulse_card = self.create_ui_card("MARKET PULSE", "fa5s.bolt")
        self.market_pulse_card.setMinimumWidth(380)
        
        self.watchlist_table_widget = QTableWidget(len(MONITORED_TRADING_PAIRS), 3)
        self.watchlist_table_widget.setHorizontalHeaderLabels(["Asset", "Price", "24h % Delta"])
        self.watchlist_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.watchlist_table_widget.verticalHeader().setVisible(False)
        self.watchlist_table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.watchlist_table_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.watchlist_table_widget.setObjectName("WatchTable")
        self.watchlist_table_widget.itemSelectionChanged.connect(self.on_watchlist_item_selected)
        
        self.watchlist_asset_map = {}
        for row_index, asset_name in enumerate(MONITORED_TRADING_PAIRS):
            self.watchlist_table_widget.setItem(row_index, 0, QTableWidgetItem(asset_name.replace("USDT","")))
            price_cell = QTableWidgetItem("---")
            delta_cell = QTableWidgetItem("0.00%")
            self.watchlist_table_widget.setItem(row_index, 1, price_cell)
            self.watchlist_table_widget.setItem(row_index, 2, delta_cell)
            self.watchlist_asset_map[asset_name] = (price_cell, delta_cell, row_index)
            
        self.market_pulse_card.layout().addWidget(self.watchlist_table_widget)
        
        force_price_sync_btn = QPushButton(" FORCE SYNC PRICES")
        self.market_pulse_card.layout().addWidget(force_price_sync_btn)
        
        if qta:
            force_price_sync_btn.setIcon(qta.icon("fa5s.bolt", color="#F0B90B"))
        force_price_sync_btn.clicked.connect(self.request_rest_price_sync)
        sidebar_vertical_layout.addWidget(self.market_pulse_card)
        
        sidebar_vertical_layout.addStretch()
        main_content_area.addLayout(sidebar_vertical_layout, 1)

        right_panel_column = QVBoxLayout()
        right_panel_column.setSpacing(25)
        
        self.execution_engine_card = self.create_ui_card("UNIFIED EXECUTION ENGINE", "fa5s.paper-plane")
        engine_form_layout = QVBoxLayout()
        engine_form_layout.setSpacing(20)
        
        symbol_settings_row = QHBoxLayout()
        self.symbol_selector_box = QComboBox()
        self.symbol_selector_box.addItems(MONITORED_TRADING_PAIRS)
        symbol_settings_row.addWidget(self.symbol_selector_box)
        self.symbol_selector_box.currentIndexChanged.connect(self.on_selected_symbol_changed)
        
        self.margin_mode_selector = QComboBox()
        self.margin_mode_selector.addItems(["CROSSED", "ISOLATED"])
        symbol_settings_row.addWidget(self.margin_mode_selector)
        
        self.leverage_input_field = QLineEdit("10")
        symbol_settings_row.addWidget(self.leverage_input_field)
        engine_form_layout.addLayout(symbol_settings_row)
        
        order_details_row = QHBoxLayout()
        self.order_side_selector = QComboBox()
        self.order_side_selector.addItems(["BUY / LONG", "SELL / SHORT"])
        order_details_row.addWidget(self.order_side_selector)
        
        self.position_quantity_input = QLineEdit()
        self.position_quantity_input.setPlaceholderText("Position Quantity")
        order_details_row.addWidget(self.position_quantity_input)
        
        self.order_type_selector = QComboBox()
        self.order_type_selector.addItems(["MARKET", "LIMIT"])
        order_details_row.addWidget(self.order_type_selector)
        engine_form_layout.addLayout(order_details_row)
        
        entry_price_row = QHBoxLayout()
        self.limit_price_input = QLineEdit()
        self.limit_price_input.setPlaceholderText("Entry Price (Limit Only)")
        entry_price_row.addWidget(self.limit_price_input)
        
        self.optimize_sizing_btn = QPushButton(" OPTIMIZE SIZE")
        entry_price_row.addWidget(self.optimize_sizing_btn)
        
        if qta:
            self.optimize_sizing_btn.setIcon(qta.icon("fa5s.magic", color="white"))
        self.optimize_sizing_btn.clicked.connect(self.on_auto_sizing_trigger)
        engine_form_layout.addLayout(entry_price_row)
        
        self.execute_trade_btn = QPushButton(" DEPLOY CAPITAL NOW")
        self.execute_trade_btn.setObjectName("TradeBtn")
        self.execute_trade_btn.setFixedHeight(55)
        
        if qta:
            self.execute_trade_btn.setIcon(qta.icon("fa5s.paper-plane", color="#0B0E11"))
        self.execute_trade_btn.clicked.connect(self.process_trade_execution)
        engine_form_layout.addWidget(self.execute_trade_btn)
        
        self.execution_engine_card.layout().addLayout(engine_form_layout)
        right_panel_column.addWidget(self.execution_engine_card)
        
        self.main_tabs_component = QTabWidget()
        self.active_positions_table = self.create_data_table(["Symbol", "Direction", "Quantity", "Entry Price", "Mark Price", "uPnL"])
        self.execution_history_table = self.create_data_table(["Date/Time", "Symbol", "Side", "Type", "Status", "Price", "Qty"])
        self.terminal_log_output = QTextEdit()
        self.terminal_log_output.setReadOnly(True)
        self.terminal_log_output.setObjectName("Console")
        
        self.active_positions_table.verticalHeader().setVisible(False)
        self.execution_history_table.verticalHeader().setVisible(False)

        self.main_tabs_component.addTab(self.active_positions_table, "Live Positions")
        self.main_tabs_component.addTab(self.execution_history_table, "Order History")
        self.main_tabs_component.addTab(self.terminal_log_output, "Engine Terminal")
        right_panel_column.addWidget(self.main_tabs_component, 1)
        
        main_content_area.addLayout(right_panel_column, 2)
        master_layout.addLayout(main_content_area)

        self.footer_status_bar = QFrame()
        self.footer_status_bar.setFixedHeight(40)
        self.footer_status_bar.setObjectName("Footer")
        
        footer_horizontal_layout = QHBoxLayout(self.footer_status_bar)
        footer_horizontal_layout.setContentsMargins(30, 0, 30, 0)
        
        self.connection_status_text_label = QLabel("INITIALIZING...")
        footer_horizontal_layout.addWidget(self.connection_status_text_label)
        footer_horizontal_layout.addStretch()
        
        self.live_pulse_indicator = QLabel("PULSE: OFFLINE")
        self.live_pulse_indicator.setObjectName("WssIndicator")
        footer_horizontal_layout.addWidget(self.live_pulse_indicator)
        footer_horizontal_layout.addSpacing(30)
        
        self.terminal_clock_label = QLabel("--:--:--")
        footer_horizontal_layout.addWidget(self.terminal_clock_label)
        master_layout.addWidget(self.footer_status_bar)

    def create_ui_card(self, section_title, font_icon=None):
        card_frame = QFrame()
        card_frame.setObjectName("Card")
        
        card_vertical_layout = QVBoxLayout(card_frame)
        card_vertical_layout.setContentsMargins(25, 25, 25, 25)
        card_vertical_layout.setSpacing(10)
        
        title_horizontal_row = QHBoxLayout()
        if qta and font_icon:
            icon_container = QLabel()
            icon_container.setPixmap(qta.icon(font_icon, color="#848E9C").pixmap(16, 16))
            title_horizontal_row.addWidget(icon_container)
            
        title_text_label = QLabel(section_title.upper())
        title_text_label.setObjectName("CardTitle")
        
        title_horizontal_row.addWidget(title_text_label)
        title_horizontal_row.addStretch()
        card_vertical_layout.addLayout(title_horizontal_row)
        
        return card_frame

    def create_data_table(self, column_headers):
        table_ref = QTableWidget(0, len(column_headers))
        table_ref.setHorizontalHeaderLabels(column_headers)
        table_ref.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_ref.setAlternatingRowColors(True)
        return table_ref

    def apply_visual_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0B0E11; }
            #Header { background-color: #181A20; border-bottom: 2px solid #2B3139; }
            #Logo { font-size: 26px; font-weight: 900; color: #0ECB81; }
            #EnvLbl { color: #848E9C; font-size: 10px; font-weight: 800; letter-spacing: 1px; margin-top: -5px; }
            #CurSym { color: #848E9C; font-size: 12px; font-weight: bold; }
            #PriceMain { font-size: 36px; font-weight: bold; color: #F0B90B; font-family: 'Bahnschrift'; }
            #Card { background-color: #1E2329; border-radius: 15px; border: 1px solid #2B3139; }
            #CardTitle { color: #848E9C; font-size: 11px; font-weight: 800; }
            #BigBal { font-size: 42px; font-weight: 800; color: #FFFFFF; margin: 10px 0; }
            #PnLSub { font-size: 15px; font-weight: bold; color: #0ECB81; margin-bottom: 15px; }
            #Console { background-color: #000000; color: #0ECB81; font-family: 'Consolas'; font-size: 12px; border: 1px solid #2B3139; padding: 15px; }
            QPushButton { background-color: #2B3139; color: white; border-radius: 8px; padding: 12px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background-color: #3e444e; border: 1px solid #474D57; }
            #TradeBtn { background-color: #0ECB81; color: #0B0E11; font-size: 18px; border: none; font-weight: 900; }
            QLineEdit, QComboBox { background-color: #2B3139; color: white; border: 1px solid #474D57; padding: 14px; border-radius: 8px; font-size: 14px; }
            QTableWidget { background-color: #1E2329; alternate-background-color: #181A20; border: none; color: #EAECEF; gridline-color: transparent; selection-background-color: #2B3139; selection-color: #0ECB81; }
            QHeaderView::section { background-color: #2B3139; color: #848E9C; font-size: 11px; padding: 12px; border: none; font-weight: bold; }
            #Footer { background-color: #181A20; border-top: 1px solid #2B3139; }
            #WssIndicator { color: #848E9C; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 4px; border: 1px solid #2B3139; }
            QTabWidget::pane { border: 1px solid #2B3139; background: #1E2329; border-top: 2px solid #0ECB81; }
            QTabBar::tab { background: #181A20; color: #848E9C; padding: 12px 25px; border-right: 1px solid #2B3139; font-weight: bold; }
            QTabBar::tab:selected { background: #1E2329; color: #0ECB81; }
        """)

    def begin_async_initialization(self):
        auth_key = os.getenv("BINANCE_API_KEY")
        auth_secret = os.getenv("BINANCE_API_SECRET")
        
        if not auth_key or not auth_secret:
            self.display_error_dialog("Credentials Missing")
            return
        
        self.communication_bridge.status_msg.emit("WAKING ENGINE...")
        
        def run_startup_thread():
            try:
                self.trading_bot_client = BinanceClient(auth_key, auth_secret)
                self.communication_bridge.engine_armed.emit()
            except Exception as startup_err:
                self.communication_bridge.error_occurred.emit(str(startup_err))
                
        threading.Thread(target=run_startup_thread, daemon=True).start()

    def on_engine_startup_complete(self):
        self.communication_bridge.status_msg.emit("ENGINE ARMED - SYNCING...")
        
        QTimer.singleShot(100, lambda: self.trading_bot_client.start_market_pulse_stream(MONITORED_TRADING_PAIRS, lambda payload: self.communication_bridge.pulse_received.emit(payload)))
        QTimer.singleShot(800, lambda: self.trading_bot_client.start_user_data_stream(lambda event: self.trigger_manual_sync()))
        
        self.trigger_manual_sync()
        self.communication_bridge.status_msg.emit("TERMINAL SYNCHRONIZED")

    def update_terminal_clock(self):
        self.terminal_clock_label.setText(datetime.now().strftime("%H:%M:%S"))
        
        if self.current_pulse_status_count == 0:
            self.live_pulse_indicator.setText("PULSE: OFFLINE")
            self.live_pulse_indicator.setStyleSheet("color: #848E9C; border: 1px solid #2B3139;")
        else:
            self.current_pulse_status_count -= 1
            if self.current_pulse_status_count < 1 and not self.is_reconnecting_active:
                self.initiate_stream_reconnect()

    def initiate_stream_reconnect(self):
        if self.is_reconnecting_active:
            return
            
        self.is_reconnecting_active = True
        self.communication_bridge.status_msg.emit("REBOOTING STREAMS...")
        
        def reconnect_worker():
            try:
                self.trading_bot_client.stop_all_streams()
                time.sleep(1)
                self.trading_bot_client.start_market_pulse_stream(MONITORED_TRADING_PAIRS, lambda p: self.communication_bridge.pulse_received.emit(p))
                time.sleep(0.5)
                self.trading_bot_client.start_user_data_stream(lambda ev: self.trigger_manual_sync())
                self.is_reconnecting_active = False
                self.communication_bridge.status_msg.emit("STREAMS RECOVERED")
            except:
                self.is_reconnecting_active = False
                
        threading.Thread(target=reconnect_worker, daemon=True).start()

    def process_pulse_update(self, update_payload):
        try:
            target_symbol = update_payload['symbol']
            price_val = float(update_payload.get('price', 0))
            delta_val = float(update_payload.get('change', 0))
            
            self.last_known_prices[target_symbol] = price_val
            self.current_pulse_status_count = 15
            
            self.live_pulse_indicator.setText("PULSE: LIVE")
            self.live_pulse_indicator.setStyleSheet("color: #0ECB81; border: 1px solid #0ECB81;")
            
            if target_symbol == self.symbol_selector_box.currentText():
                self.market_price_indicator.setText(f"${price_val:,.2f}")
                self.market_price_indicator.setStyleSheet(f"color: {'#0ECB81' if delta_val >= 0 else '#F6465D'}")
                
            if target_symbol in self.watchlist_asset_map:
                price_cell_node, delta_cell_node, row_idx = self.watchlist_asset_map[target_symbol]
                price_cell_node.setText(f"${price_val:,.2f}")
                
                trend_arrow = "▲" if delta_val >= 0 else "▼"
                delta_cell_node.setText(f"{trend_arrow} {abs(delta_val):.2f}%")
                delta_cell_node.setForeground(QColor("#0ECB81" if delta_val >= 0 else "#F6465D"))
        except:
            pass

    def trigger_manual_sync(self):
        if not hasattr(self, 'trading_bot_client'):
            return
            
        def data_fetch_worker():
            try:
                collected_data = {
                    'account_bal': self.trading_bot_client.get_account_balance(),
                    'active_pos': self.trading_bot_client.get_positions(),
                    'pending_ords': self.trading_bot_client.get_open_orders(),
                    'trade_hist': self.trading_bot_client.get_order_history()
                }
                self.communication_bridge.data_refreshed.emit(collected_data)
            except Exception as sync_err:
                self.communication_bridge.error_occurred.emit(str(sync_err))
                
        threading.Thread(target=data_fetch_worker, daemon=True).start()

    def update_user_interface(self, raw_data_bundle):
        try:
            self.balance_value_label.setText(f"${raw_data_bundle['account_bal']:,.2f}")
            self.active_positions_table.setRowCount(0)
            
            computed_total_pnl = 0.0
            
            for position_entry in raw_data_bundle['active_pos']:
                row_count = self.active_positions_table.rowCount()
                self.active_positions_table.insertRow(row_count)
                
                amount_val = float(position_entry['positionAmt'])
                pnl_val = float(position_entry['unRealizedProfit'])
                computed_total_pnl += pnl_val
                
                self.active_positions_table.setItem(row_count, 0, QTableWidgetItem(position_entry['symbol']))
                self.active_positions_table.setItem(row_count, 1, QTableWidgetItem("LONG" if amount_val > 0 else "SHORT"))
                self.active_positions_table.setItem(row_count, 2, QTableWidgetItem(f"{abs(amount_val):.3f}"))
                self.active_positions_table.setItem(row_count, 3, QTableWidgetItem(f"${float(position_entry['entryPrice']):,.2f}"))
                self.active_positions_table.setItem(row_count, 4, QTableWidgetItem(f"${float(position_entry['markPrice']):,.2f}"))
                
                profit_status_item = QTableWidgetItem(f"${pnl_val:,.2f}")
                profit_status_item.setForeground(QColor("#0ECB81" if pnl_val >= 0 else "#F6465D"))
                self.active_positions_table.setItem(row_count, 5, profit_status_item)
                
            self.unrealized_pnl_label.setText(f"PORTFOLIO DELTA: ${computed_total_pnl:,.2f}")
            self.unrealized_pnl_label.setStyleSheet(f"color: {'#0ECB81' if computed_total_pnl >= 0 else '#F6465D'}; font-weight: bold;")

            self.execution_history_table.setRowCount(0)
            for history_record in raw_data_bundle['trade_hist']:
                history_row = self.execution_history_table.rowCount()
                self.execution_history_table.insertRow(history_row)
                
                timestamp_formatted = datetime.fromtimestamp(history_record['time']/1000).strftime("%Y-%m-%d %H:%M:%S")
                execution_status = history_record['status']
                
                self.execution_history_table.setItem(history_row, 0, QTableWidgetItem(timestamp_formatted))
                self.execution_history_table.setItem(history_row, 1, QTableWidgetItem(history_record['symbol']))
                self.execution_history_table.setItem(history_row, 2, QTableWidgetItem(history_record['side']))
                self.execution_history_table.setItem(history_row, 3, QTableWidgetItem(history_record['type']))
                
                status_display_cell = QTableWidgetItem(execution_status)
                if execution_status == "FILLED":
                    status_display_cell.setForeground(QColor("#0ECB81"))
                elif execution_status in ["CANCELED", "EXPIRED", "REJECTED"]:
                    status_display_cell.setForeground(QColor("#F6465D"))
                elif execution_status == "NEW":
                    status_display_cell.setForeground(QColor("#F0B90B"))
                    
                self.execution_history_table.setItem(history_row, 4, status_display_cell)
                self.execution_history_table.setItem(history_row, 5, QTableWidgetItem(f"${float(history_record['avgPrice'] or history_record['price']):,.2f}"))
                self.execution_history_table.setItem(history_row, 6, QTableWidgetItem(str(history_record['origQty'])))
        except Exception as ui_error:
            logging.debug(f"Data Sync UI Error: {ui_error}")

    def on_selected_symbol_changed(self, selection_index):
        active_symbol_name = self.symbol_selector_box.currentText()
        if active_symbol_name in self.watchlist_asset_map:
            self.watchlist_table_widget.selectRow(self.watchlist_asset_map[active_symbol_name][2])
            if active_symbol_name in self.last_known_prices:
                self.market_price_indicator.setText(f"${self.last_known_prices[active_symbol_name]:,.2f}")

    def on_watchlist_item_selected(self):
        currently_selected_items = self.watchlist_table_widget.selectedItems()
        if currently_selected_items:
            found_symbol_key = self.watchlist_table_widget.item(currently_selected_items[0].row(), 0).text() + "USDT"
            dropdown_index = self.symbol_selector_box.findText(found_symbol_key)
            if dropdown_index >= 0:
                self.symbol_selector_box.blockSignals(True)
                self.symbol_selector_box.setCurrentIndex(dropdown_index)
                self.symbol_selector_box.blockSignals(False)

    def request_rest_price_sync(self):
        if not hasattr(self, 'trading_bot_client'):
            return
            
        def manual_rest_sync_thread():
            try:
                self.communication_bridge.status_msg.emit("FORCING REST PRICE SYNC...")
                historical_pulses = self.trading_bot_client.get_24h_tickers(MONITORED_TRADING_PAIRS)
                for pulse_data in historical_pulses:
                    self.communication_bridge.pulse_received.emit(pulse_data)
                self.communication_bridge.status_msg.emit("SYNC SUCCESSFUL")
            except Exception as rest_err:
                self.communication_bridge.error_occurred.emit(str(rest_err))
                
        threading.Thread(target=manual_rest_sync_thread, daemon=True).start()

    def on_auto_sizing_trigger(self):
        try:
            active_pair = self.symbol_selector_box.currentText()
            available_balance_val = float(self.balance_value_label.text().replace("$","").replace(",",""))
            latest_price = self.last_known_prices.get(active_pair)
            
            if latest_price:
                recommended_qty = calculate_position_size(self.trading_bot_client, active_pair, available_balance_val, 1.0, latest_price, int(self.leverage_input_field.text()))
                self.position_quantity_input.setText(str(recommended_qty))
        except:
            pass

    def process_trade_execution(self):
        selected_asset = self.symbol_selector_box.currentText()
        trade_side_label = "BUY" if "BUY" in self.order_side_selector.currentText() else "SELL"
        trade_volume = self.position_quantity_input.text()
        
        def execute_order_worker():
            try:
                self.trading_bot_client.change_leverage(selected_asset, int(self.leverage_input_field.text()))
                self.trading_bot_client.change_margin_mode(selected_asset, self.margin_mode_selector.currentText())
                place_order(self.trading_bot_client, selected_asset, trade_side_label, self.order_type_selector.currentText(), trade_volume, price=self.limit_price_input.text() or None)
                self.communication_bridge.status_msg.emit("TRADE DEPLOYED")
                self.trigger_manual_sync()
            except Exception as exec_err:
                self.communication_bridge.error_occurred.emit(str(exec_err))
                
        threading.Thread(target=execute_order_worker, daemon=True).start()

    def append_text_to_console(self, console_text):
        timestamp_log = f"<span style='color: #848E9C;'>[{datetime.now().strftime('%H:%M:%S')}]</span> {console_text}"
        self.terminal_log_output.append(timestamp_log)
        self.terminal_log_output.verticalScrollBar().setValue(self.terminal_log_output.verticalScrollBar().maximum())

    def read_new_log_lines(self):
        if not os.path.exists(TRADING_SESSION_LOG):
            return
            
        try:
            current_log_file_size = os.path.getsize(TRADING_SESSION_LOG)
            if current_log_file_size > self.last_log_read_position:
                with open(TRADING_SESSION_LOG, 'r') as session_file:
                    session_file.seek(self.last_log_read_position)
                    for buffer_line in session_file.readlines():
                        if "DEBUG" not in buffer_line:
                            self.communication_bridge.log_updated.emit(buffer_line.strip())
                    self.last_log_read_position = current_log_file_size
        except:
            pass

    def display_error_dialog(self, error_content_msg):
        if "Read loop has been closed" in error_content_msg:
            self.initiate_stream_reconnect()
            return
            
        QMessageBox.critical(self, "TERMINAL ERROR", error_content_msg)

    def closeEvent(self, termination_event):
        if hasattr(self, 'trading_bot_client'):
            self.trading_bot_client.stop_all_streams()
        termination_event.accept()

if __name__ == "__main__":
    application_instance = QApplication(sys.argv)
    terminal_main_window = TradingTerminalInterface()
    terminal_main_window.show()
    sys.exit(application_instance.exec())
