import os
from datetime import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

FILE_NAME = "reports/TURION_AI_Trader.xlsx"


def save_market_summary(
    symbol,
    timeframe,
    price,
    ema20,
    ema50,
    rsi,
    market_state,
    market_structure,
    action,
    support=None,
    resistance=None,
    atr=None
):

    os.makedirs("reports", exist_ok=True)

    # Create Excel File
    if not os.path.exists(FILE_NAME):

        workbook = Workbook()

        sheet = workbook.active

        sheet.title = "Market Summary"

        sheet.append([
            "Run ID",
            "Date",
            "Time",
            "Symbol",
            "Timeframe",
            "Price",
            "EMA20",
            "EMA50",
            "RSI",
            "Market State",
            "Market Structure",
            "AI Decision",
            "Support",
            "Resistance",
            "ATR14"
        ])

        # ---------------- Header Style ----------------

        blue_fill = PatternFill(
            fill_type="solid",
            start_color="1F4E78",
            end_color="1F4E78"
        )

        white_font = Font(
            bold=True,
            color="FFFFFF"
        )

        center = Alignment(
            horizontal="center",
            vertical="center"
        )

        thin = Side(
            border_style="thin",
            color="000000"
        )

        border = Border(
            left=thin,
            right=thin,
            top=thin,
            bottom=thin
        )

        for cell in sheet[1]:
            cell.fill = blue_fill
            cell.font = white_font
            cell.alignment = center
            cell.border = border

        # Column Width

        widths = {
            "A":10,
            "B":14,
            "C":12,
            "D":12,
            "E":12,
            "F":12,
            "G":12,
            "H":12,
            "I":10,
            "J":18,
            "K":18,
            "L":18,
            "M":12,
            "N":12,
            "O":10
        }

        for col, width in widths.items():
            sheet.column_dimensions[col].width = width

        # Freeze Header
        sheet.freeze_panes = "A2"

        # Filter
        sheet.auto_filter.ref = "A1:O1"

        workbook.save(FILE_NAME)

    workbook = load_workbook(FILE_NAME)

    sheet = workbook["Market Summary"]

    # Updated: 2026-07-11 - backfill Support/Resistance/ATR14 headers for report files created before these columns existed
    if sheet["M1"].value != "Support":
        sheet["M1"] = "Support"

    if sheet["N1"].value != "Resistance":
        sheet["N1"] = "Resistance"

    if sheet["O1"].value != "ATR14":
        sheet["O1"] = "ATR14"

    run_id = sheet.max_row

    now = datetime.now()

    sheet.append([

        run_id,

        now.strftime("%d-%m-%Y"),

        now.strftime("%H:%M:%S"),

        symbol,

        timeframe,

        round(price, 2),

        round(ema20, 2),

        round(ema50, 2),

        round(rsi, 2),

        market_state,

        market_structure,

        action,

        round(support, 2) if support is not None else "",

        round(resistance, 2) if resistance is not None else "",

        round(atr, 2) if atr is not None else ""

    ])

    # ---------------- Color Coding ----------------

    green = PatternFill(
        fill_type="solid",
        start_color="C6EFCE",
        end_color="C6EFCE"
    )

    red = PatternFill(
        fill_type="solid",
        start_color="FFC7CE",
        end_color="FFC7CE"
    )

    yellow = PatternFill(
        fill_type="solid",
        start_color="FFF2CC",
        end_color="FFF2CC"
    )

    gray = PatternFill(
        fill_type="solid",
        start_color="D9D9D9",
        end_color="D9D9D9"
    )

    last_row = sheet.max_row

    state_cell = sheet[f"J{last_row}"]
    structure_cell = sheet[f"K{last_row}"]
    decision_cell = sheet[f"L{last_row}"]

    # Market State

    if "Bullish" in str(state_cell.value):
        state_cell.fill = green

    elif "Bearish" in str(state_cell.value):
        state_cell.fill = red

    else:
        state_cell.fill = yellow

    # Market Structure

    if "Bullish" in str(structure_cell.value):
        structure_cell.fill = green

    elif "Bearish" in str(structure_cell.value):
        structure_cell.fill = red

    else:
        structure_cell.fill = yellow

    # AI Decision

    value = str(decision_cell.value).upper()

    if "BUY" in value:
        decision_cell.fill = green

    elif "SELL" in value:
        decision_cell.fill = red

    elif "WAIT" in value:
        decision_cell.fill = yellow

    else:
        decision_cell.fill = gray

    workbook.save(FILE_NAME)

    print("Excel Database Updated Successfully.")