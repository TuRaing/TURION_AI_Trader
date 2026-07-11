import pandas as pd


def calculate_average_volume(data, period=20):

    volume = data["Volume"]

    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    return volume.rolling(window=period).mean()


def build_volume_analysis(current_volume, average_volume, spike_multiplier=1.5):

    if pd.isna(average_volume) or average_volume == 0:

        return {
            "Current Volume": int(current_volume),
            "Average Volume": 0,
            "Volume Ratio": 0,
            "Spike": False
        }

    ratio = current_volume / average_volume

    return {
        "Current Volume": int(current_volume),
        "Average Volume": int(average_volume),
        "Volume Ratio": round(ratio, 2),
        "Spike": ratio >= spike_multiplier
    }


def get_volume_analysis(data, period=20, spike_multiplier=1.5):
    """
    Detect Volume Spikes relative to the recent average

    Parameters
    ----------
    data : DataFrame
    period : int
    spike_multiplier : float

    Returns
    -------
    dict
    """

    volume = data["Volume"]

    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    avg_volume = calculate_average_volume(data, period)

    return build_volume_analysis(volume.iloc[-1], avg_volume.iloc[-1], spike_multiplier)
