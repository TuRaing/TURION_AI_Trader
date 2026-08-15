import json
import sys
import time
from datetime import datetime

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import requests

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QGridLayout, QHeaderView, QComboBox, QDialog, QScrollArea,
    QAbstractItemView
)

from indicators.ema import calculate_ema
from data.watchlist import NIFTY_50_SYMBOLS, INDICES
from strategy.watchlist_scanner import download_watchlist, analyze_symbol, MIN_CANDLES
from strategy.paper_trading import load_portfolio
from strategy.options_strategies import ALL_STRATEGIES
from strategy.portfolio_aggregation import realized_pnl_from_trades
from strategy.options_transaction_costs import calculate_options_round_trip_cost

NEWS_SHORTLIST_FILE = "reports/best_trade_shortlist.json"
BEST_TRADE_PICK_FILE = "reports/best_trade_pick.json"

# Added 15-Aug-2026 - every one of the 8 new options/Fyers-test/
# history/news tabs now fetches its report JSON straight from GitHub
# instead of the local checkout, mirroring exactly how the mobile app
# already solved this (mobile_app/lib/api.dart's _repoRawBase) - no
# `git pull` needed on this machine before the desktop app shows real
# results. Deliberately NOT done via an in-app `git pull` (rejected
# alternative): this repo has other sessions committing/pushing to it
# regularly, and an app-triggered git pull firing on a timer risks a
# lock conflict with that unrelated git activity. A plain HTTPS GET
# has no such risk. The original 4 tabs (Market Overview/Chart/
# Watchlist/Paper Trading) are UNCHANGED - Watchlist/Chart/Overview
# were already live (yfinance), Paper Trading still reads the local
# strategy.paper_trading.load_portfolio() untouched, per this repo's
# "never modify a working module" rule.
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/TuRaing/TURION_AI_Trader/main"


def fetch_github_json(path, timeout=10):
    """
    Same contract as mobile_app/lib/api.dart's fetchJson(): cache-
    busted with the current time (raw.githubusercontent.com is CDN-
    fronted and can otherwise serve a stale cached copy), returns
    None (not an exception) for a 404 - some report files legitimately
    don't exist yet until a book's first real trade happens.
    """

    url = f"{GITHUB_RAW_BASE}/{path}?t={int(time.time())}"
    response = requests.get(url, timeout=timeout)

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json()


class JsonFetchWorker(QThread):
    """
    Generic background fetch for any list of report paths - used by
    every tab below that needs 1-2 files (History, News, Fyers Test,
    Best Trade Shortlist, the strategy pickers, TradeDetailDialog).
    Options Grouped/Summary keep their OWN worker classes below
    instead of this one - they fetch all 59 books' worth in one go,
    a large enough batch to be worth its own progress/error handling.
    """

    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, paths):

        super().__init__()
        self.paths = paths

    def run(self):

        try:

            results = {}

            for path in self.paths:
                results[path] = fetch_github_json(path)

            self.finished.emit(results)

        except Exception as error:

            self.failed.emit(str(error))

REFRESH_INTERVAL_MS = 15 * 60 * 1000

# Step 1 of the Desktop-App/Android-parity plan, 15-Aug - the most-used
# mobile screen (FyersOptionsGroupedScreen) ported to PySide6. Unlike
# the Dart side (which fetches over HTTP and keeps its own hardcoded
# _allBooks copy of the 59-book list, since the phone can't import
# Python), this reuses options_strategies.ALL_STRATEGIES directly - one
# real source of truth, never goes stale as new books get added. Same
# reason the cost breakdown below calls calculate_options_round_trip_
# cost() directly instead of a ported copy (no options_transaction_
# costs.dart equivalent needed here - this already runs in Python).
INDEX_LOT_SIZE = {"NIFTY": 75, "BANKNIFTY": 30}

# Step 4 of the Desktop-App parity plan, 15-Aug - ported directly from
# mobile_app/lib/screens/fyers_multi_strategy_options_screen.dart and
# fyers_threshold_options_screen.dart, same scope on purpose (parity
# with the existing Android app, not a superset) - deliberately does
# NOT include the 6 oi_hybrid_sl variants, matching the mobile side's
# own explicit 14-Aug decision to keep those out of the per-strategy
# tab pickers (only in the Grouped view).
OPTIONS_STRATEGY_NAMES = [
    "simple_st1", "st2", "st3", "st4", "gapfill", "vix_filter", "oi_footprint",
    "credit_spread", "pcr_momentum", "max_pain_drift", "pcr_vix_combo", "oi_iv_combo",
    "simple_st1_slcap", "st2_slcap", "st3_slcap",
]

OPTIONS_STRATEGY_DESCRIPTIONS = {
    "simple_st1": "RSI direction (CE/PE), ATM strike, 3% Target / 3% Stop-Loss.",
    "st2": "RSI direction, ATM strike, 5% Target / 2% Stop-Loss (best ratio per backtest).",
    "st3": "RSI direction, ATM strike, 5% Target / 5% Stop-Loss.",
    "st4": "One high-confidence trade/day - 15m/5m/1m alignment + ADX>25, ATR trailing stop after Rs 1,000 profit.",
    "gapfill": "Bets the morning gap fills back toward prev close - PE on gap up, CE on gap down, entry only until 10am.",
    "vix_filter": "RSI>60/<40 + India VIX in its own 30-70 percentile band (BANKNIFTY only).",
    "oi_footprint": "ATM Open Interest buildup (institutional footprint) - small, fast Rs 1,500 Target/Stop-Loss.",
    "credit_spread": "Sells premium (theta) - only when VIX high, RSI-directional Bull Put/Bear Call spread (2 legs).",
    "pcr_momentum": "How fast the full option chain's Put-Call OI Ratio is changing (+ volume confirmation).",
    "max_pain_drift": "Which way the Max Pain strike is drifting - only within 2 days of expiry.",
    "pcr_vix_combo": "PCR Momentum + India VIX in its calm 30-70 percentile band - two signals combined.",
    "oi_iv_combo": "OI-buildup signal + option's IV not more than 1.5x underlying's realized volatility.",
    "simple_st1_slcap": "Same as simple_st1, but hybrid Stop-Loss cap (min of flat 2% and 2% of deployed capital).",
    "st2_slcap": "Same as st2, hybrid Stop-Loss cap (min of flat 2% and 2% of deployed capital).",
    "st3_slcap": "Same as st3, hybrid Stop-Loss cap (min of flat 2% and 2% of deployed capital).",
}

OPTIONS_BANNER_TEXT = (
    "15 strategies, each with its own Rs 1,00,000 (vix_filter is BANKNIFTY-only) - "
    "real live premium quotes, paper trades only."
)

THRESHOLD_STRATEGY_NAMES = [
    "simple_st1_threshold", "st2_threshold", "st3_threshold", "st4_threshold",
    "gapfill_threshold", "st3_threshold_slcap", "st2_threshold_slcap",
]

THRESHOLD_STRATEGY_DESCRIPTIONS = {
    "simple_st1_threshold": "Same as simple_st1, but stops opening new trades once today's profit hits Rs 2,000+.",
    "st2_threshold": "Same as st2, but stops opening new trades once today's profit hits Rs 2,000+.",
    "st3_threshold": "Same as st3, but stops opening new trades once today's profit hits Rs 2,000+.",
    "st4_threshold": "Same as st4, but stops opening new trades once today's profit hits Rs 2,000+.",
    "gapfill_threshold": "Same as gapfill, but stops opening new trades once today's profit hits Rs 2,000+.",
    "st3_threshold_slcap": "Same as st3_threshold, plus hybrid Stop-Loss cap - NIFTY only.",
    "st2_threshold_slcap": "Same as st2_threshold, plus hybrid Stop-Loss cap - BANKNIFTY only.",
}

THRESHOLD_BANNER_TEXT = (
    "Same strategies as Options (+ 2 hybrid-SL-cap variants), but stop opening new trades "
    "once today's realized profit hits Rs 2,000+ - locks in the day's gain."
)

# Combined lookup for TradeDetailDialog (reached from Options Grouped,
# where any of the 59 books can appear) - books outside these 22 (the
# newer slcap/oi_hybrid_sl batches) simply have no description yet,
# same as the mobile app never having written one for them either.
ALL_STRATEGY_DESCRIPTIONS = {**OPTIONS_STRATEGY_DESCRIPTIONS, **THRESHOLD_STRATEGY_DESCRIPTIONS}

# Same special-cased exceptions as the mobile side's _strategyIndices -
# every other name here runs both indices.
STRATEGY_INDEX_OVERRIDES = {
    "vix_filter": ["BANKNIFTY"],
    "st3_threshold_slcap": ["NIFTY"],
    "st2_threshold_slcap": ["BANKNIFTY"],
}


def indices_for_strategy(name):

    return STRATEGY_INDEX_OVERRIDES.get(name, ["NIFTY", "BANKNIFTY"])


STRATEGY_CONFIG_LOOKUP = {(cfg["name"], cfg["index"]): cfg for _, cfg in ALL_STRATEGIES}


def is_slcap_book(name):

    return name.endswith("_slcap") or name.startswith("oi_hybrid_sl")


def classify_group(name, pnl, trades):

    if is_slcap_book(name):
        return "New (SL-cap)"

    if trades == 0:
        return "No data yet"

    if pnl > 0:
        return "Profitable"

    return "Loss-making"

DARK_STYLESHEET = """
QMainWindow, QWidget { background-color: #1e1e2e; color: #cdd6f4; }
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 10px;
    font-weight: bold;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QTableWidget {
    background-color: #181825;
    gridline-color: #45475a;
    color: #cdd6f4;
}
QHeaderView::section {
    background-color: #313244;
    color: #cdd6f4;
    padding: 4px;
    border: none;
}
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}
QPushButton:disabled { background-color: #45475a; color: #6c7086; }
QTabWidget::pane { border: 1px solid #45475a; }
QTabBar::tab {
    background: #313244;
    color: #cdd6f4;
    padding: 8px 16px;
}
QTabBar::tab:selected { background: #89b4fa; color: #1e1e2e; }
QComboBox { background-color: #313244; color: #cdd6f4; padding: 4px; }
"""

GREEN = QColor("#a6e3a1")
RED = QColor("#f38ba8")
YELLOW = QColor("#f9e2af")


def bias_color(bias):

    if bias == "Bullish":
        return GREEN

    if bias == "Bearish":
        return RED

    return YELLOW


def build_full_watchlist():

    symbols = dict(INDICES)

    for ticker in NIFTY_50_SYMBOLS:
        symbols[ticker.replace(".NS", "")] = ticker

    return symbols


class RefreshWorker(QThread):

    finished = Signal(dict)
    failed = Signal(str)

    def run(self):

        try:

            symbols = build_full_watchlist()
            frames = download_watchlist(symbols, period="6mo", interval="1d")

            index_analysis = {}
            watchlist_results = []
            chart_data = {}

            for name, ticker in symbols.items():

                frame = frames.get(name)

                if frame is None or len(frame) < MIN_CANDLES:
                    continue

                analysis = analyze_symbol(frame)

                if name in INDICES:
                    index_analysis[name] = analysis

                watchlist_results.append({"Name": name, **analysis})

                close = frame["Close"]

                if hasattr(close, "columns"):
                    close = close.iloc[:, 0]

                ema20 = calculate_ema(frame, 20)
                ema50 = calculate_ema(frame, 50)

                chart_data[name] = {
                    "dates": list(close.index[-90:]),
                    "close": list(close.iloc[-90:]),
                    "ema20": list(ema20.iloc[-90:]),
                    "ema50": list(ema50.iloc[-90:])
                }

            watchlist_results.sort(key=lambda r: r["Confidence"], reverse=True)

            portfolio = load_portfolio()

            self.finished.emit({
                "indices": index_analysis,
                "watchlist": watchlist_results,
                "portfolio": portfolio,
                "chart_data": chart_data
            })

        except Exception as error:

            self.failed.emit(str(error))


class GroupedRefreshWorker(QThread):

    finished = Signal(list)
    failed = Signal(str)

    def run(self):

        try:

            rows = []

            for _, cfg in ALL_STRATEGIES:

                portfolio = fetch_github_json(cfg["portfolio_file"]) or {
                    "Cash": 100000.0, "Closed Trades": [], "Positions": {}
                }

                cash = portfolio.get("Cash", 100000.0)
                trades = len(portfolio.get("Closed Trades", []))
                pnl = realized_pnl_from_trades(portfolio)
                name = cfg["name"]

                rows.append({
                    "name": name,
                    "index": cfg["index"],
                    "pnl": pnl,
                    "trades": trades,
                    "group": classify_group(name, pnl, trades),
                    "portfolio_file": cfg["portfolio_file"],
                })

            self.finished.emit(rows)

        except Exception as error:

            self.failed.emit(str(error))


class SummaryRefreshWorker(QThread):
    """
    Step 2 of the Desktop-App parity plan - flat, single-table view of
    all 59 books (Initial/Current/Profit), same content as the mobile
    app's FyersOptionsSummaryScreen but read from ALL_STRATEGIES
    directly instead of a hand-maintained _books list (the mobile
    version needed manual updates - see PROJECT_STATUS.md's note that
    it "had to be completed to all 59 entries, was previously 41,
    missing the oi_footprint variants" - reading ALL_STRATEGIES here
    makes that particular staleness impossible).
    """

    finished = Signal(list)
    failed = Signal(str)

    def run(self):

        try:

            rows = []

            for _, cfg in ALL_STRATEGIES:

                portfolio = fetch_github_json(cfg["portfolio_file"]) or {}
                cash = portfolio.get("Cash", 100000.0)

                rows.append({
                    "name": cfg["name"],
                    "index": cfg["index"],
                    "initial": 100000.0,
                    "current": cash,
                    "profit": realized_pnl_from_trades(portfolio),
                })

            self.finished.emit(rows)

        except Exception as error:

            self.failed.emit(str(error))


class TradeDetailDialog(QDialog):
    """
    Same content as the mobile app's showOptionTradeDetails() bottom
    sheet: open position (if any), then every closed trade with its
    itemized cost breakdown - explicitly trading costs only, not
    personal income tax, same note the mobile version carries.
    """

    def __init__(self, book_name, index, portfolio_file, parent=None):

        super().__init__(parent)

        self.setWindowTitle(f"{book_name} - {index}")
        self.resize(650, 500)

        layout = QVBoxLayout(self)

        description = ALL_STRATEGY_DESCRIPTIONS.get(book_name)
        if description:
            description_label = QLabel(description)
            description_label.setWordWrap(True)
            description_label.setStyleSheet("color: #a6adc8; font-style: italic;")
            layout.addWidget(description_label)

        try:
            portfolio = fetch_github_json(portfolio_file) or {"Cash": 100000.0, "Closed Trades": [], "Positions": {}}
        except Exception as error:
            portfolio = {"Cash": 100000.0, "Closed Trades": [], "Positions": {}}
            layout.addWidget(QLabel(f"Fetch failed: {error}"))

        lot_size = INDEX_LOT_SIZE.get(index, 75)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)

        position = portfolio.get("Positions") or portfolio.get("Position")
        if position:
            inner_layout.addWidget(QLabel("<b>Open Position</b>"))
            for field in ("Symbol", "Strike", "Option Type", "Entry Time", "Entry Premium", "Lots"):
                if field in position:
                    inner_layout.addWidget(QLabel(f"{field}: {position[field]}"))

        closed = portfolio.get("Closed Trades", [])
        inner_layout.addWidget(QLabel(f"<b>Closed Trades ({len(closed)})</b>"))

        for trade in reversed(closed):

            box = QGroupBox()
            box_layout = QVBoxLayout(box)

            entry = trade.get("Entry Premium")
            exit_ = trade.get("Exit Premium")
            lots = trade.get("Lots")
            net_pnl = trade.get("Net PnL", trade.get("PnL", 0.0))

            header = f"{trade.get('Symbol', '')}  Entry {entry} -> Exit {exit_}  ({trade.get('Exit Reason', '')})"
            header_label = QLabel(header)
            box_layout.addWidget(header_label)

            if entry is not None and exit_ is not None and lots:
                cost = calculate_options_round_trip_cost(entry, exit_, lot_size, lots)
                box_layout.addWidget(QLabel(f"Trading cost (brokerage/STT/exchange/stamp/SEBI/GST): Rs {cost:.2f}"))

            pnl_label = QLabel(f"Net PnL: Rs {net_pnl:.2f}")
            pnl_label.setStyleSheet(f"color: {(GREEN if net_pnl > 0 else RED).name()}; font-weight: bold;")
            box_layout.addWidget(pnl_label)

            inner_layout.addWidget(box)

        inner_layout.addWidget(QLabel(
            "<i>Trading costs only (brokerage/STT/exchange/stamp duty/SEBI/GST) - "
            "not personal income tax.</i>"
        ))
        inner_layout.addStretch()

        scroll.setWidget(inner)
        layout.addWidget(scroll)


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("TURION AI Trader - Desktop Dashboard")
        self.resize(1100, 700)

        self.worker = None
        self.chart_data = {}

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        top_bar = QHBoxLayout()

        self.status_label = QLabel("Not refreshed yet")
        self.refresh_button = QPushButton("Refresh Now")
        self.refresh_button.clicked.connect(self.start_refresh)

        top_bar.addWidget(self.status_label)
        top_bar.addStretch()
        top_bar.addWidget(self.refresh_button)

        layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.strategy_picker_widgets = {}

        self.overview_tab = self.build_overview_tab()
        self.chart_tab = self.build_chart_tab()
        self.watchlist_tab = self.build_watchlist_tab()
        self.paper_trading_tab = self.build_paper_trading_tab()
        self.options_grouped_tab = self.build_options_grouped_tab()
        self.options_summary_tab = self.build_options_summary_tab()
        self.options_picker_tab = self.build_strategy_picker_tab(
            "options", OPTIONS_STRATEGY_NAMES, OPTIONS_STRATEGY_DESCRIPTIONS, OPTIONS_BANNER_TEXT
        )
        self.threshold_picker_tab = self.build_strategy_picker_tab(
            "threshold", THRESHOLD_STRATEGY_NAMES, THRESHOLD_STRATEGY_DESCRIPTIONS, THRESHOLD_BANNER_TEXT
        )
        self.history_tab = self.build_history_tab()
        self.news_tab = self.build_news_tab()
        self.fyers_test_tab = self.build_fyers_test_tab()
        self.best_trade_shortlist_tab = self.build_best_trade_shortlist_tab()

        self.tabs.addTab(self.overview_tab, "Market Overview")
        self.tabs.addTab(self.chart_tab, "Chart")
        self.tabs.addTab(self.watchlist_tab, "Watchlist")
        self.tabs.addTab(self.paper_trading_tab, "Paper Trading")
        self.tabs.addTab(self.options_grouped_tab, "Options Grouped")
        self.tabs.addTab(self.options_summary_tab, "Options Summary")
        self.tabs.addTab(self.options_picker_tab, "Options")
        self.tabs.addTab(self.threshold_picker_tab, "Threshold Options")
        self.tabs.addTab(self.history_tab, "History")
        self.tabs.addTab(self.news_tab, "News")
        self.tabs.addTab(self.fyers_test_tab, "Fyers (Test)")
        self.tabs.addTab(self.best_trade_shortlist_tab, "Best Trade Shortlist")

        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.start_refresh)
        self.auto_refresh_timer.start(REFRESH_INTERVAL_MS)

        # Reads local report JSON files only (no network download like
        # the yfinance-based refresh above), so a much shorter interval
        # is cheap - matches how frequently the underlying options
        # cron triggers themselves update those files (~1 min).
        self.options_grouped_worker = None
        self.options_grouped_timer = QTimer(self)
        self.options_grouped_timer.timeout.connect(self.start_options_grouped_refresh)
        self.options_grouped_timer.start(2 * 60 * 1000)

        self.options_summary_worker = None
        self.options_summary_timer = QTimer(self)
        self.options_summary_timer.timeout.connect(self.start_options_summary_refresh)
        self.options_summary_timer.start(2 * 60 * 1000)

        self.start_refresh()
        self.start_options_grouped_refresh()
        self.start_options_summary_refresh()
        self.refresh_history()
        self.refresh_news()
        self.refresh_fyers_test()
        self.refresh_best_trade_shortlist()

    def build_overview_tab(self):

        widget = QWidget()
        layout = QHBoxLayout(widget)

        self.index_boxes = {}

        for name in INDICES:

            box = QGroupBox(name)
            grid = QGridLayout(box)

            labels = {}

            fields = ["Price", "Bias", "Confidence", "Support", "Resistance", "ATR", "Candle Pattern"]

            for i, field in enumerate(fields):

                grid.addWidget(QLabel(f"{field}:"), i, 0)

                value_label = QLabel("-")
                grid.addWidget(value_label, i, 1)

                labels[field] = value_label

            self.index_boxes[name] = labels

            layout.addWidget(box)

        return widget

    def build_chart_tab(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Symbol:"))

        self.chart_symbol_combo = QComboBox()
        self.chart_symbol_combo.currentTextChanged.connect(self.draw_chart)

        selector_row.addWidget(self.chart_symbol_combo)
        selector_row.addStretch()

        layout.addLayout(selector_row)

        self.figure = Figure(facecolor="#1e1e2e")
        self.canvas = FigureCanvasQTAgg(self.figure)

        layout.addWidget(self.canvas)

        return widget

    def build_watchlist_tab(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(6)
        self.watchlist_table.setHorizontalHeaderLabels(
            ["Name", "Price", "Decision", "Bias", "Confidence %", "Candle Pattern"]
        )
        self.watchlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.watchlist_table)

        return widget

    def build_paper_trading_tab(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.portfolio_summary_label = QLabel("Cash: -   Open Positions: -   Closed Trades: -   Total PnL: -")
        layout.addWidget(self.portfolio_summary_label)

        layout.addWidget(QLabel("Open Positions"))

        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(4)
        self.positions_table.setHorizontalHeaderLabels(["Symbol", "Entry Price", "Stop Loss", "Target"])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.positions_table)

        layout.addWidget(QLabel("Closed Trades"))

        self.closed_trades_table = QTableWidget()
        self.closed_trades_table.setColumnCount(6)
        self.closed_trades_table.setHorizontalHeaderLabels(
            ["Symbol", "Entry Price", "Exit Price", "Reason", "PnL", "Exit Time"]
        )
        self.closed_trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.closed_trades_table)

        return widget

    def build_options_grouped_tab(self):

        widget = QWidget()
        outer_layout = QVBoxLayout(widget)

        summary_row = QHBoxLayout()
        self.options_grouped_status_label = QLabel("Not refreshed yet")
        self.options_grouped_summary_label = QLabel("")
        summary_row.addWidget(self.options_grouped_status_label)
        summary_row.addStretch()
        summary_row.addWidget(self.options_grouped_summary_label)
        outer_layout.addLayout(summary_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        scroll.setWidget(inner)

        self.options_group_boxes = {}
        self.options_group_tables = {}

        group_order = ["New (SL-cap)", "Profitable", "Loss-making", "No data yet"]

        for group_name in group_order:

            box = QGroupBox(group_name)
            box_layout = QVBoxLayout(box)

            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Strategy", "Index", "Trades", "PnL"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.cellDoubleClicked.connect(
                lambda row, col, g=group_name: self.open_trade_detail(g, row)
            )

            box_layout.addWidget(table)
            inner_layout.addWidget(box)

            self.options_group_boxes[group_name] = box
            self.options_group_tables[group_name] = table

        inner_layout.addStretch()

        return widget

    def build_options_summary_tab(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)

        top_row = QHBoxLayout()
        self.options_summary_status_label = QLabel("Not refreshed yet")
        self.options_summary_total_label = QLabel("")
        top_row.addWidget(self.options_summary_status_label)
        top_row.addStretch()
        top_row.addWidget(self.options_summary_total_label)
        layout.addLayout(top_row)

        self.options_summary_table = QTableWidget()
        self.options_summary_table.setColumnCount(5)
        self.options_summary_table.setHorizontalHeaderLabels(["Strategy", "Index", "Initial", "Current", "Profit"])
        self.options_summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.options_summary_table.setSortingEnabled(True)
        self.options_summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout.addWidget(self.options_summary_table)

        return widget

    def build_strategy_picker_tab(self, key, strategy_names, descriptions, banner_text):
        """
        Step 4 of the Desktop-App parity plan - one shared builder for
        both the "Options" and "Threshold Options" tabs, same idea as
        the mobile side reusing FyersMultiStrategyOptionsScreen with
        different constructor params instead of duplicating the tab/
        list/portfolio-fetch UI twice. Uses a strategy+index dropdown
        pair instead of mobile's nested TabBars - simpler in PySide6,
        same underlying data.
        """

        widget = QWidget()
        layout = QVBoxLayout(widget)

        banner = QLabel(banner_text)
        banner.setWordWrap(True)
        banner.setStyleSheet("color: #89b4fa;")
        layout.addWidget(banner)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Strategy:"))
        strategy_combo = QComboBox()
        strategy_combo.addItems(strategy_names)
        selector_row.addWidget(strategy_combo)
        selector_row.addWidget(QLabel("Index:"))
        index_combo = QComboBox()
        selector_row.addWidget(index_combo)
        selector_row.addStretch()
        layout.addLayout(selector_row)

        description_label = QLabel("")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #a6adc8;")
        layout.addWidget(description_label)

        summary_label = QLabel("Cash: -   Win rate: -   Closed trades: -")
        layout.addWidget(summary_label)

        layout.addWidget(QLabel("Position"))
        position_table = QTableWidget()
        position_table.setColumnCount(4)
        position_table.setHorizontalHeaderLabels(["Symbol", "Strike", "Type", "Entry Premium"])
        position_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        position_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(position_table)

        layout.addWidget(QLabel("Closed Trades (double-click a row for the cost breakdown)"))
        closed_table = QTableWidget()
        closed_table.setColumnCount(5)
        closed_table.setHorizontalHeaderLabels(["Symbol", "Entry", "Exit", "Reason", "Net PnL"])
        closed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        closed_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(closed_table)

        self.strategy_picker_widgets[key] = {
            "strategy_combo": strategy_combo,
            "index_combo": index_combo,
            "description_label": description_label,
            "summary_label": summary_label,
            "position_table": position_table,
            "closed_table": closed_table,
            "descriptions": descriptions,
            "current_name": None,
            "current_index": None,
            "current_portfolio_file": None,
            "worker": None,
        }

        strategy_combo.currentTextChanged.connect(lambda _, k=key: self.on_strategy_picker_strategy_changed(k))
        index_combo.currentTextChanged.connect(lambda _, k=key: self.refresh_strategy_picker(k))
        closed_table.cellDoubleClicked.connect(lambda row, col, k=key: self.open_strategy_picker_detail(k))

        self.on_strategy_picker_strategy_changed(key)

        return widget

    def on_strategy_picker_strategy_changed(self, key):

        state = self.strategy_picker_widgets[key]
        name = state["strategy_combo"].currentText()

        state["index_combo"].blockSignals(True)
        state["index_combo"].clear()
        state["index_combo"].addItems(indices_for_strategy(name))
        state["index_combo"].blockSignals(False)

        state["description_label"].setText(state["descriptions"].get(name, ""))

        self.refresh_strategy_picker(key)

    def refresh_strategy_picker(self, key):

        state = self.strategy_picker_widgets[key]
        name = state["strategy_combo"].currentText()
        index = state["index_combo"].currentText()

        if not name or not index:
            return

        cfg = STRATEGY_CONFIG_LOOKUP.get((name, index))

        if cfg is None:
            return

        portfolio_file = cfg["portfolio_file"]

        state["current_name"] = name
        state["current_index"] = index
        state["current_portfolio_file"] = portfolio_file
        state["summary_label"].setText("Refreshing...")

        state["worker"] = JsonFetchWorker([portfolio_file])
        state["worker"].finished.connect(lambda results, k=key: self.on_strategy_picker_refresh_done(k, results))
        state["worker"].failed.connect(lambda msg, k=key: self.strategy_picker_widgets[k]["summary_label"].setText(f"Refresh failed: {msg}"))
        state["worker"].start()

    def on_strategy_picker_refresh_done(self, key, results):

        state = self.strategy_picker_widgets[key]
        portfolio_file = state["current_portfolio_file"]

        portfolio = results.get(portfolio_file) or {"Cash": 100000.0, "Position": None, "Closed Trades": []}

        cash = portfolio.get("Cash", 100000.0)
        position = portfolio.get("Position")
        closed = portfolio.get("Closed Trades", [])

        wins = sum(1 for t in closed if t.get("Net PnL", t.get("PnL", 0)) > 0)
        win_rate = f"{(wins / len(closed) * 100):.0f}%" if closed else "-"

        state["summary_label"].setText(f"Cash: Rs {cash:.2f}   Win rate: {win_rate}   Closed trades: {len(closed)}")

        position_table = state["position_table"]
        position_table.setRowCount(1 if position else 0)

        if position:
            position_table.setItem(0, 0, QTableWidgetItem(str(position.get("Symbol", ""))))
            position_table.setItem(0, 1, QTableWidgetItem(str(position.get("Strike", ""))))
            position_table.setItem(0, 2, QTableWidgetItem(str(position.get("Option Type", ""))))
            position_table.setItem(0, 3, QTableWidgetItem(str(position.get("Entry Premium", ""))))

        closed_table = state["closed_table"]
        closed_table.setRowCount(len(closed))

        for row_index, trade in enumerate(reversed(closed)):

            net_pnl = trade.get("Net PnL", trade.get("PnL", 0.0))

            closed_table.setItem(row_index, 0, QTableWidgetItem(str(trade.get("Symbol", ""))))
            closed_table.setItem(row_index, 1, QTableWidgetItem(str(trade.get("Entry Premium", ""))))
            closed_table.setItem(row_index, 2, QTableWidgetItem(str(trade.get("Exit Premium", ""))))
            closed_table.setItem(row_index, 3, QTableWidgetItem(str(trade.get("Exit Reason", ""))))

            pnl_item = QTableWidgetItem(f"Rs {net_pnl:+.2f}")
            pnl_item.setForeground(GREEN if net_pnl > 0 else (RED if net_pnl < 0 else YELLOW))
            closed_table.setItem(row_index, 4, pnl_item)

    def open_strategy_picker_detail(self, key):

        state = self.strategy_picker_widgets[key]

        if state["current_portfolio_file"] is None:
            return

        dialog = TradeDetailDialog(
            state["current_name"], state["current_index"], state["current_portfolio_file"], parent=self
        )
        dialog.exec()

    def build_history_tab(self):
        """
        Step 5 of the Desktop-App parity plan - mirrors mobile's
        HistoryScreen. The Swing half duplicates what the existing
        Paper Trading tab already shows (same reports/paper_portfolio.
        json via the same load_portfolio()) - kept anyway, matching
        the user's own "मूळ योजनेप्रमाणे वेगळे tabs हवेत" (separate
        tabs per the original plan) call on Step 4. The real gap this
        tab actually fills is Intraday (Best Trade) - reports/
        best_trade_portfolio.json had NO view anywhere on desktop
        before this. Local file reads only (like TradeDetailDialog),
        no QThread needed - it's microseconds, not a network call.
        """

        widget = QWidget()
        outer_layout = QVBoxLayout(widget)

        top_row = QHBoxLayout()
        self.history_status_label = QLabel("Not refreshed yet")
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_history)
        top_row.addWidget(self.history_status_label)
        top_row.addStretch()
        top_row.addWidget(refresh_button)
        outer_layout.addLayout(top_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        scroll.setWidget(inner)

        swing_box = QGroupBox("Swing (Closed)")
        swing_layout = QVBoxLayout(swing_box)
        self.history_swing_summary_label = QLabel("")
        swing_layout.addWidget(self.history_swing_summary_label)
        self.history_swing_table = QTableWidget()
        self.history_swing_table.setColumnCount(5)
        self.history_swing_table.setHorizontalHeaderLabels(["Symbol", "Entry", "Exit", "Reason", "PnL"])
        self.history_swing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_swing_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        swing_layout.addWidget(self.history_swing_table)
        inner_layout.addWidget(swing_box)

        intraday_box = QGroupBox("Intraday (Closed)")
        intraday_layout = QVBoxLayout(intraday_box)
        self.history_intraday_summary_label = QLabel("")
        intraday_layout.addWidget(self.history_intraday_summary_label)
        self.history_intraday_table = QTableWidget()
        self.history_intraday_table.setColumnCount(5)
        self.history_intraday_table.setHorizontalHeaderLabels(["Symbol", "Entry", "Exit", "Reason", "PnL"])
        self.history_intraday_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_intraday_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        intraday_layout.addWidget(self.history_intraday_table)
        inner_layout.addWidget(intraday_box)

        return widget

    def refresh_history(self):

        self.history_status_label.setText("Refreshing...")

        self.history_worker = JsonFetchWorker(["reports/paper_portfolio.json", "reports/best_trade_portfolio.json"])
        self.history_worker.finished.connect(self.on_history_refresh_done)
        self.history_worker.failed.connect(lambda msg: self.history_status_label.setText(f"Refresh failed: {msg}"))
        self.history_worker.start()

    def on_history_refresh_done(self, results):

        swing_portfolio = results.get("reports/paper_portfolio.json") or {"Cash": 100000.0, "Closed Trades": []}
        intraday_portfolio = results.get("reports/best_trade_portfolio.json") or {"Cash": 100000.0, "Closed Trades": []}

        self._fill_history_section(
            swing_portfolio, self.history_swing_summary_label, self.history_swing_table, "Swing"
        )
        self._fill_history_section(
            intraday_portfolio, self.history_intraday_summary_label, self.history_intraday_table, "Intraday"
        )

        self.history_status_label.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def _fill_history_section(self, portfolio, summary_label, table, label):

        # Prefers "Net PnL" (options/Fyers trades that carry a real
        # cost breakdown) and falls back to "PnL" (plain yfinance
        # trades, which never have a "Net PnL" field) - safe for every
        # caller, since the two field names never coexist by accident.
        cash = portfolio.get("Cash", 100000.0)
        closed = portfolio.get("Closed Trades", [])
        total_pnl = sum(t.get("Net PnL", t.get("PnL", 0.0)) for t in closed)
        wins = sum(1 for t in closed if t.get("Net PnL", t.get("PnL", 0)) > 0)
        win_rate = f"{(wins / len(closed) * 100):.0f}%" if closed else "-"

        summary_label.setText(
            f"{label} Total PnL: Rs {total_pnl:+.2f}   Cash: Rs {cash:.2f}   "
            f"Win rate: {win_rate}   Closed trades: {len(closed)}"
        )

        table.setRowCount(len(closed))

        for row_index, trade in enumerate(reversed(closed)):

            pnl = trade.get("Net PnL", trade.get("PnL", 0.0))

            table.setItem(row_index, 0, QTableWidgetItem(str(trade.get("Symbol", trade.get("Name", "NIFTY 50")))))
            table.setItem(row_index, 1, QTableWidgetItem(f"{trade.get('Entry Price', ''):.2f}" if trade.get("Entry Price") is not None else ""))
            table.setItem(row_index, 2, QTableWidgetItem(f"{trade.get('Exit Price', ''):.2f}" if trade.get("Exit Price") is not None else ""))
            table.setItem(row_index, 3, QTableWidgetItem(str(trade.get("Exit Reason", ""))))

            pnl_item = QTableWidgetItem(f"Rs {pnl:+.2f}")
            pnl_item.setForeground(GREEN if pnl > 0 else (RED if pnl < 0 else YELLOW))
            table.setItem(row_index, 4, pnl_item)

    def build_news_tab(self):
        """
        Step 5, second half - mirrors mobile's NewsScreen: reports/
        best_trade_shortlist.json's "Market Headlines", each with a
        Sentiment badge (Bullish/Bearish/Neutral). Genuinely new
        content, no overlap with anything else on desktop.
        """

        widget = QWidget()
        layout = QVBoxLayout(widget)

        top_row = QHBoxLayout()
        self.news_status_label = QLabel("Not refreshed yet")
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_news)
        top_row.addWidget(self.news_status_label)
        top_row.addStretch()
        top_row.addWidget(refresh_button)
        layout.addLayout(top_row)

        self.news_table = QTableWidget()
        self.news_table.setColumnCount(2)
        self.news_table.setHorizontalHeaderLabels(["Sentiment", "Headline"])
        self.news_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.news_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.news_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.news_table.setWordWrap(True)

        layout.addWidget(self.news_table)

        return widget

    def refresh_news(self):

        self.news_status_label.setText("Refreshing...")

        self.news_worker = JsonFetchWorker([NEWS_SHORTLIST_FILE])
        self.news_worker.finished.connect(self.on_news_refresh_done)
        self.news_worker.failed.connect(lambda msg: self.news_status_label.setText(f"Refresh failed: {msg}"))
        self.news_worker.start()

    def on_news_refresh_done(self, results):

        shortlist = results.get(NEWS_SHORTLIST_FILE) or {}
        headlines = shortlist.get("Market Headlines", [])

        self.news_table.setRowCount(len(headlines))

        for row_index, headline in enumerate(headlines):

            sentiment = headline.get("Sentiment", "Neutral")
            color = GREEN if sentiment == "Bullish" else (RED if sentiment == "Bearish" else YELLOW)

            sentiment_item = QTableWidgetItem(sentiment)
            sentiment_item.setForeground(color)
            self.news_table.setItem(row_index, 0, sentiment_item)
            self.news_table.setItem(row_index, 1, QTableWidgetItem(str(headline.get("Headline", ""))))

        if not headlines:
            self.news_status_label.setText("No headlines fetched yet.")
        else:
            self.news_status_label.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def build_fyers_test_tab(self):
        """
        Gap 1 from the Desktop-App parity plan, 15-Aug - mirrors
        mobile's FyersPortfolioScreen: the Fyers-SOURCED Swing +
        Intraday test engines (reports/fyers_test_portfolio.json,
        reports/fyers_best_trade_portfolio.json) - real broker data,
        still being proven out in parallel with the yfinance ones.
        Completely separate from the yfinance Paper Trading/History
        tabs above (different portfolio files, different engines) and
        from the Options tabs (options strategies are a different
        engine family entirely - see this repo's own "options logic
        stays separate from stock/index logic" rule).
        """

        widget = QWidget()
        outer_layout = QVBoxLayout(widget)

        banner = QLabel("Fyers (test) - real broker data, paper trades only, still being proven in parallel with yfinance.")
        banner.setWordWrap(True)
        banner.setStyleSheet("color: #89b4fa;")
        outer_layout.addWidget(banner)

        top_row = QHBoxLayout()
        self.fyers_test_status_label = QLabel("Not refreshed yet")
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_fyers_test)
        top_row.addWidget(self.fyers_test_status_label)
        top_row.addStretch()
        top_row.addWidget(refresh_button)
        outer_layout.addLayout(top_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        scroll.setWidget(inner)

        swing_box = QGroupBox("Swing (Fyers test)")
        swing_layout = QVBoxLayout(swing_box)
        self.fyers_test_swing_summary_label = QLabel("")
        swing_layout.addWidget(self.fyers_test_swing_summary_label)
        swing_layout.addWidget(QLabel("Open Positions"))
        self.fyers_test_swing_positions_table = QTableWidget()
        self.fyers_test_swing_positions_table.setColumnCount(4)
        self.fyers_test_swing_positions_table.setHorizontalHeaderLabels(["Symbol", "Entry Price", "Stop Loss", "Target"])
        self.fyers_test_swing_positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fyers_test_swing_positions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        swing_layout.addWidget(self.fyers_test_swing_positions_table)
        swing_layout.addWidget(QLabel("Closed Trades"))
        self.fyers_test_swing_closed_table = QTableWidget()
        self.fyers_test_swing_closed_table.setColumnCount(5)
        self.fyers_test_swing_closed_table.setHorizontalHeaderLabels(["Symbol", "Entry", "Exit", "Reason", "PnL"])
        self.fyers_test_swing_closed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fyers_test_swing_closed_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        swing_layout.addWidget(self.fyers_test_swing_closed_table)
        inner_layout.addWidget(swing_box)

        intraday_box = QGroupBox("Intraday (Fyers test)")
        intraday_layout = QVBoxLayout(intraday_box)
        self.fyers_test_intraday_summary_label = QLabel("")
        intraday_layout.addWidget(self.fyers_test_intraday_summary_label)
        self.fyers_test_intraday_closed_table = QTableWidget()
        self.fyers_test_intraday_closed_table.setColumnCount(5)
        self.fyers_test_intraday_closed_table.setHorizontalHeaderLabels(["Symbol", "Entry", "Exit", "Reason", "PnL"])
        self.fyers_test_intraday_closed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fyers_test_intraday_closed_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        intraday_layout.addWidget(self.fyers_test_intraday_closed_table)
        inner_layout.addWidget(intraday_box)

        return widget

    def refresh_fyers_test(self):

        self.fyers_test_status_label.setText("Refreshing...")

        self.fyers_test_worker = JsonFetchWorker(
            ["reports/fyers_test_portfolio.json", "reports/fyers_best_trade_portfolio.json"]
        )
        self.fyers_test_worker.finished.connect(self.on_fyers_test_refresh_done)
        self.fyers_test_worker.failed.connect(lambda msg: self.fyers_test_status_label.setText(f"Refresh failed: {msg}"))
        self.fyers_test_worker.start()

    def on_fyers_test_refresh_done(self, results):

        swing_portfolio = results.get("reports/fyers_test_portfolio.json") or {
            "Cash": 100000.0, "Positions": {}, "Closed Trades": []
        }
        intraday_portfolio = results.get("reports/fyers_best_trade_portfolio.json") or {
            "Cash": 100000.0, "Position": None, "Closed Trades": []
        }

        cash = swing_portfolio.get("Cash", 100000.0)
        positions = swing_portfolio.get("Positions", {})
        closed = swing_portfolio.get("Closed Trades", [])
        total_pnl = sum(t.get("Net PnL", t.get("PnL", 0.0)) for t in closed)
        wins = sum(1 for t in closed if t.get("Net PnL", t.get("PnL", 0)) > 0)
        win_rate = f"{(wins / len(closed) * 100):.0f}%" if closed else "-"

        self.fyers_test_swing_summary_label.setText(
            f"Swing Total PnL: Rs {total_pnl:+.2f}   Cash: Rs {cash:.2f}   "
            f"Win rate: {win_rate}   Open: {len(positions)}   Closed: {len(closed)}"
        )

        pos_table = self.fyers_test_swing_positions_table
        pos_table.setRowCount(len(positions))

        for row_index, (symbol, position) in enumerate(positions.items()):
            pos_table.setItem(row_index, 0, QTableWidgetItem(symbol))
            pos_table.setItem(row_index, 1, QTableWidgetItem(f"{position.get('Entry Price', 0):.2f}"))
            pos_table.setItem(row_index, 2, QTableWidgetItem(f"{position.get('Stop Loss', 0):.2f}" if position.get("Stop Loss") is not None else ""))
            pos_table.setItem(row_index, 3, QTableWidgetItem(f"{position.get('Target', 0):.2f}" if position.get("Target") is not None else ""))

        self._fill_history_section(swing_portfolio, QLabel(), self.fyers_test_swing_closed_table, "Swing")

        intraday_position = intraday_portfolio.get("Position")
        intraday_closed = intraday_portfolio.get("Closed Trades", [])
        intraday_pnl = sum(t.get("Net PnL", t.get("PnL", 0.0)) for t in intraday_closed)

        position_note = ""
        if intraday_position:
            symbol = intraday_position.get("Name", intraday_position.get("Symbol", "NIFTY 50"))
            entry = intraday_position.get("Entry Price", 0)
            position_note = f"   Today's Position: {symbol} @ Rs {entry:.2f}"

        self.fyers_test_intraday_summary_label.setText(
            f"Intraday Total PnL: Rs {intraday_pnl:+.2f}   Closed: {len(intraday_closed)}{position_note}"
        )

        self._fill_history_section(intraday_portfolio, QLabel(), self.fyers_test_intraday_closed_table, "Intraday")

        self.fyers_test_status_label.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def build_best_trade_shortlist_tab(self):
        """
        Gap 2 from the Desktop-App parity plan, 15-Aug - mirrors
        mobile's BestTradeScreen: today's locked pick (reports/
        best_trade_pick.json's "Best Trade" + "Reason") plus the full
        ranked shortlist that fed into it - genuinely different content
        from History's closed-trade list (this is the "why" behind
        today's entry decision, not the outcome of past ones).
        """

        widget = QWidget()
        layout = QVBoxLayout(widget)

        top_row = QHBoxLayout()
        self.shortlist_status_label = QLabel("Not refreshed yet")
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_best_trade_shortlist)
        top_row.addWidget(self.shortlist_status_label)
        top_row.addStretch()
        top_row.addWidget(refresh_button)
        layout.addLayout(top_row)

        layout.addWidget(QLabel("Locked for today"))
        self.shortlist_pick_label = QLabel("No shortlist scan yet today.")
        self.shortlist_pick_label.setWordWrap(True)
        layout.addWidget(self.shortlist_pick_label)

        layout.addWidget(QLabel("Shortlist (ranked)"))
        self.shortlist_table = QTableWidget()
        self.shortlist_table.setColumnCount(4)
        self.shortlist_table.setHorizontalHeaderLabels(["Name", "Type", "Decision", "Confidence"])
        self.shortlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.shortlist_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.shortlist_table)

        return widget

    def refresh_best_trade_shortlist(self):

        self.shortlist_status_label.setText("Refreshing...")

        self.shortlist_worker = JsonFetchWorker([BEST_TRADE_PICK_FILE])
        self.shortlist_worker.finished.connect(self.on_best_trade_shortlist_refresh_done)
        self.shortlist_worker.failed.connect(lambda msg: self.shortlist_status_label.setText(f"Refresh failed: {msg}"))
        self.shortlist_worker.start()

    def on_best_trade_shortlist_refresh_done(self, results):

        pick = results.get(BEST_TRADE_PICK_FILE)

        if pick is None:
            self.shortlist_pick_label.setText("No shortlist scan yet today.")
            self.shortlist_table.setRowCount(0)
            self.shortlist_status_label.setText("No data")
            return

        best = pick.get("Best Trade")
        reason = pick.get("Reason", "")
        ranked = pick.get("Ranked", [])

        if best:
            confidence = best.get("Final Confidence", best.get("Confidence"))
            self.shortlist_pick_label.setText(
                f"{best.get('Name', '')} ({best.get('Type', '')}) - {best.get('Decision', '')}, "
                f"confidence {confidence}%\n{reason}"
            )
        else:
            self.shortlist_pick_label.setText(reason or "No trade cleared today's bar.")

        self.shortlist_table.setRowCount(len(ranked))

        for row_index, item in enumerate(ranked):

            bias = item.get("Bias", "")
            color = GREEN if bias == "Bullish" else (RED if bias == "Bearish" else YELLOW)

            self.shortlist_table.setItem(row_index, 0, QTableWidgetItem(str(item.get("Name", ""))))
            self.shortlist_table.setItem(row_index, 1, QTableWidgetItem(str(item.get("Type", ""))))

            decision_item = QTableWidgetItem(str(item.get("Decision", "")))
            decision_item.setForeground(color)
            self.shortlist_table.setItem(row_index, 2, decision_item)

            confidence = item.get("Final Confidence", item.get("Confidence"))
            self.shortlist_table.setItem(row_index, 3, QTableWidgetItem(f"{confidence}%" if confidence is not None else ""))

        self.shortlist_status_label.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def start_refresh(self):

        self.refresh_button.setEnabled(False)
        self.status_label.setText("Refreshing...")

        self.worker = RefreshWorker()
        self.worker.finished.connect(self.on_refresh_done)
        self.worker.failed.connect(self.on_refresh_failed)
        self.worker.start()

    def on_refresh_failed(self, message):

        self.status_label.setText(f"Refresh failed: {message}")
        self.refresh_button.setEnabled(True)

    def on_refresh_done(self, data):

        for name, analysis in data["indices"].items():

            labels = self.index_boxes[name]

            labels["Price"].setText(str(analysis["Price"]))
            labels["Bias"].setText(f"{analysis['Bias']} ({analysis['Decision']})")
            labels["Confidence"].setText(f"{analysis['Confidence']}%")
            labels["ATR"].setText(str(analysis["ATR"]))
            labels["Candle Pattern"].setText(analysis["Candle Pattern"])

            color = bias_color(analysis["Bias"])

            for field in ("Bias", "Confidence"):
                labels[field].setStyleSheet(f"color: {color.name()}; font-weight: bold;")

        results = data["watchlist"]

        self.watchlist_table.setRowCount(len(results))

        for row, r in enumerate(results):

            values = [r["Name"], str(r["Price"]), r["Decision"], r["Bias"], str(r["Confidence"]), r["Candle Pattern"]]

            for col, value in enumerate(values):

                item = QTableWidgetItem(value)
                item.setForeground(bias_color(r["Bias"]))

                self.watchlist_table.setItem(row, col, item)

        portfolio = data["portfolio"]
        positions = portfolio["Positions"]
        closed = portfolio["Closed Trades"]
        total_pnl = sum(t["PnL"] for t in closed)

        self.portfolio_summary_label.setText(
            f"Cash: {portfolio['Cash']:.2f}   Open Positions: {len(positions)}   "
            f"Closed Trades: {len(closed)}   Total PnL: {total_pnl:.2f}"
        )

        self.positions_table.setRowCount(len(positions))

        for row, (symbol, position) in enumerate(positions.items()):

            self.positions_table.setItem(row, 0, QTableWidgetItem(symbol))
            self.positions_table.setItem(row, 1, QTableWidgetItem(f"{position['Entry Price']:.2f}"))
            self.positions_table.setItem(row, 2, QTableWidgetItem(f"{position['Stop Loss']:.2f}"))
            self.positions_table.setItem(row, 3, QTableWidgetItem(f"{position['Target']:.2f}"))

        self.closed_trades_table.setRowCount(len(closed))

        for row, trade in enumerate(closed):

            pnl = trade["PnL"]

            row_values = [
                trade.get("Symbol", "NIFTY 50"),
                f"{trade['Entry Price']:.2f}",
                f"{trade['Exit Price']:.2f}",
                trade["Exit Reason"],
                f"{pnl:.2f}",
                trade["Exit Time"]
            ]

            for col, value in enumerate(row_values):

                item = QTableWidgetItem(value)

                if col == 4:
                    item.setForeground(GREEN if pnl > 0 else RED)

                self.closed_trades_table.setItem(row, col, item)

        self.chart_data = data["chart_data"]

        current_symbol = self.chart_symbol_combo.currentText()

        self.chart_symbol_combo.blockSignals(True)
        self.chart_symbol_combo.clear()
        self.chart_symbol_combo.addItems(list(self.chart_data.keys()))
        self.chart_symbol_combo.blockSignals(False)

        if current_symbol in self.chart_data:
            self.chart_symbol_combo.setCurrentText(current_symbol)
        elif "NIFTY 50" in self.chart_data:
            self.chart_symbol_combo.setCurrentText("NIFTY 50")

        self.draw_chart(self.chart_symbol_combo.currentText())

        self.status_label.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.refresh_button.setEnabled(True)

    def start_options_grouped_refresh(self):

        self.options_grouped_status_label.setText("Refreshing...")

        self.options_grouped_worker = GroupedRefreshWorker()
        self.options_grouped_worker.finished.connect(self.on_options_grouped_refresh_done)
        self.options_grouped_worker.failed.connect(self.on_options_grouped_refresh_failed)
        self.options_grouped_worker.start()

    def on_options_grouped_refresh_failed(self, message):

        self.options_grouped_status_label.setText(f"Refresh failed: {message}")

    def on_options_grouped_refresh_done(self, rows):

        self.options_grouped_rows_by_group = {}

        total_pnl = sum(r["pnl"] for r in rows)

        for group_name, table in self.options_group_tables.items():

            group_rows = [r for r in rows if r["group"] == group_name]

            if group_name == "Profitable":
                group_rows.sort(key=lambda r: r["pnl"], reverse=True)
            elif group_name == "Loss-making":
                group_rows.sort(key=lambda r: r["pnl"])
            else:
                group_rows.sort(key=lambda r: r["pnl"], reverse=True)

            self.options_grouped_rows_by_group[group_name] = group_rows
            self.options_group_boxes[group_name].setTitle(f"{group_name} ({len(group_rows)})")

            table.setRowCount(len(group_rows))

            for row_index, r in enumerate(group_rows):

                table.setItem(row_index, 0, QTableWidgetItem(r["name"]))
                table.setItem(row_index, 1, QTableWidgetItem(r["index"]))
                table.setItem(row_index, 2, QTableWidgetItem(str(r["trades"])))

                pnl_item = QTableWidgetItem(f"Rs {r['pnl']:+.2f}")
                pnl_item.setForeground(GREEN if r["pnl"] > 0 else (RED if r["pnl"] < 0 else YELLOW))
                table.setItem(row_index, 3, pnl_item)

        self.options_grouped_summary_label.setText(f"{len(rows)} books  |  Total PnL: Rs {total_pnl:+.2f}")
        self.options_grouped_status_label.setText(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def open_trade_detail(self, group_name, row_index):

        row = self.options_grouped_rows_by_group[group_name][row_index]

        dialog = TradeDetailDialog(row["name"], row["index"], row["portfolio_file"], parent=self)
        dialog.exec()

    def start_options_summary_refresh(self):

        self.options_summary_status_label.setText("Refreshing...")

        self.options_summary_worker = SummaryRefreshWorker()
        self.options_summary_worker.finished.connect(self.on_options_summary_refresh_done)
        self.options_summary_worker.failed.connect(self.on_options_summary_refresh_failed)
        self.options_summary_worker.start()

    def on_options_summary_refresh_failed(self, message):

        self.options_summary_status_label.setText(f"Refresh failed: {message}")

    def on_options_summary_refresh_done(self, rows):

        total_initial = sum(r["initial"] for r in rows)
        total_current = sum(r["current"] for r in rows)
        total_profit = sum(r["profit"] for r in rows)

        table = self.options_summary_table
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))

        for row_index, r in enumerate(rows):

            table.setItem(row_index, 0, QTableWidgetItem(r["name"]))
            table.setItem(row_index, 1, QTableWidgetItem(r["index"]))
            table.setItem(row_index, 2, QTableWidgetItem(f"Rs {r['initial']:.2f}"))
            table.setItem(row_index, 3, QTableWidgetItem(f"Rs {r['current']:.2f}"))

            profit_item = QTableWidgetItem(f"Rs {r['profit']:+.2f}")
            profit_item.setForeground(GREEN if r["profit"] > 0 else (RED if r["profit"] < 0 else YELLOW))
            table.setItem(row_index, 4, profit_item)

        table.setSortingEnabled(True)

        self.options_summary_total_label.setText(
            f"Total Initial: Rs {total_initial:.2f}   Total Current: Rs {total_current:.2f}   "
            f"Total Profit: Rs {total_profit:+.2f}"
        )
        self.options_summary_status_label.setText(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def draw_chart(self, symbol):

        if not symbol or symbol not in self.chart_data:
            return

        series = self.chart_data[symbol]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#181825")

        ax.plot(series["dates"], series["close"], label="Close", color="#89b4fa", linewidth=2)
        ax.plot(series["dates"], series["ema20"], label="EMA 20", color="#a6e3a1", linewidth=1)
        ax.plot(series["dates"], series["ema50"], label="EMA 50", color="#f38ba8", linewidth=1)

        ax.set_title(symbol, color="#cdd6f4")
        ax.tick_params(colors="#cdd6f4")

        for spine in ax.spines.values():
            spine.set_color("#45475a")

        ax.legend(facecolor="#313244", labelcolor="#cdd6f4")
        ax.grid(True, color="#45475a", alpha=0.3)

        self.figure.autofmt_xdate()
        self.canvas.draw()


def main():

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
