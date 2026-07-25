import pandas as pd
import pytest

from indicators.cpr import calculate_cpr


def test_first_row_is_nan():
    data = pd.DataFrame({
        "High": [110, 112],
        "Low": [95, 97],
        "Close": [108, 109],
    })

    result = calculate_cpr(data)

    assert result["Pivot"].iloc[0] != result["Pivot"].iloc[0]  # NaN


def test_levels_derived_from_previous_row():
    data = pd.DataFrame({
        "High": [110, 112],
        "Low": [95, 97],
        "Close": [108, 109],
    })

    result = calculate_cpr(data).iloc[1]

    assert result["Pivot"] == pytest.approx(104.3333, abs=1e-3)
    assert result["BC"] == pytest.approx(102.5, abs=1e-3)
    assert result["TC"] == pytest.approx(106.1667, abs=1e-3)
    assert result["R1"] == pytest.approx(113.6667, abs=1e-3)
    assert result["S1"] == pytest.approx(98.6667, abs=1e-3)
    assert result["R2"] == pytest.approx(119.3333, abs=1e-3)
    assert result["S2"] == pytest.approx(89.3333, abs=1e-3)
    assert result["R3"] == pytest.approx(128.6667, abs=1e-3)
    assert result["S3"] == pytest.approx(83.6667, abs=1e-3)


def test_resistance_levels_ordered_above_support_levels():
    data = pd.DataFrame({
        "High": [110, 112, 108],
        "Low": [95, 97, 90],
        "Close": [108, 109, 100],
    })

    result = calculate_cpr(data).iloc[2]

    assert result["S3"] < result["S2"] < result["S1"] < result["Pivot"] < result["R1"] < result["R2"] < result["R3"]
