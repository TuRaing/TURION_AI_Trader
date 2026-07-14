import sys
from datetime import datetime

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QGridLayout, QHeaderView, QComboBox
)

from indicators.ema import calculate_ema
from data.watchlist import NIFTY_50_SYMBOLS, INDICES
from strategy.watchlist_scanner import download_watchlist, analyze_symbol, MIN_CANDLES
from strategy.paper_trading import load_portfolio

REFRESH_INTERVAL_MS = 15 * 60 * 1000

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

        self.overview_tab = self.build_overview_tab()
        self.chart_tab = self.build_chart_tab()
        self.watchlist_tab = self.build_watchlist_tab()
        self.paper_trading_tab = self.build_paper_trading_tab()

        self.tabs.addTab(self.overview_tab, "Market Overview")
        self.tabs.addTab(self.chart_tab, "Chart")
        self.tabs.addTab(self.watchlist_tab, "Watchlist")
        self.tabs.addTab(self.paper_trading_tab, "Paper Trading")

        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.start_refresh)
        self.auto_refresh_timer.start(REFRESH_INTERVAL_MS)

        self.start_refresh()

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
