import pandas as pd


def validate_market_data(data):
    """
    Validate Market Data

    Returns
    -------
    is_valid : bool

    errors : list
    """

    errors = []

    # --------------------------
    # Empty Data
    # --------------------------

    if data.empty:
        errors.append("Market data is empty.")

    # --------------------------
    # Required Columns
    # --------------------------

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    for column in required_columns:

        if column not in data.columns:
            errors.append(f"Missing column : {column}")

    if errors:
        return False, errors

    # Support latest yfinance
    for column in required_columns:

        if isinstance(data[column], pd.DataFrame):
            data[column] = data[column].iloc[:, 0]

    # --------------------------
    # Missing Values
    # --------------------------

    if data[required_columns].isnull().values.any():
        errors.append("Missing (NaN) values found.")

    # --------------------------
    # Duplicate Candles
    # --------------------------

    if data.index.duplicated().any():
        errors.append("Duplicate candles found.")


    # --------------------------
    # Minimum Candles
    # --------------------------

    if len(data) < 50:
        errors.append("Less than 50 candles available.")

    # --------------------------
    # Final Result
    # --------------------------

    if len(errors) == 0:

        return True, []

    return False, errors