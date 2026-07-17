from strategy.option_chain_engine import analyze_option_chain


def _fixture_chain():
    return {
        "records": {
            "data": [
                {
                    "strikePrice": 22000,
                    "CE": {"openInterest": 500, "changeinOpenInterest": 50, "impliedVolatility": 15},
                    "PE": {"openInterest": 1200, "changeinOpenInterest": 20, "impliedVolatility": 14},
                },
                {
                    "strikePrice": 22100,
                    "CE": {"openInterest": 700, "changeinOpenInterest": 100, "impliedVolatility": 16},
                    "PE": {"openInterest": 500, "changeinOpenInterest": 30, "impliedVolatility": 15},
                },
                {
                    "strikePrice": 22200,
                    "CE": {"openInterest": 300, "changeinOpenInterest": 10, "impliedVolatility": 17},
                    "PE": {"openInterest": 300, "changeinOpenInterest": 5, "impliedVolatility": 16},
                },
            ]
        }
    }


def test_pcr_and_bias():
    result = analyze_option_chain(_fixture_chain())

    assert result["Available"] is True
    assert result["PCR"] == 1.33
    assert result["Bias"] == "Bullish"


def test_max_pain_picks_lowest_payout_strike():
    result = analyze_option_chain(_fixture_chain())

    assert result["Max Pain"] == 22100


def test_call_and_put_writing_ranked_by_oi_change():
    result = analyze_option_chain(_fixture_chain())

    assert result["Call Writing"][0] == 22100
    assert result["Put Writing"][0] == 22100


def test_average_iv():
    result = analyze_option_chain(_fixture_chain())

    assert result["IV"] == 15.5


def test_empty_chain_is_unavailable():
    result = analyze_option_chain({"records": {"data": []}})

    assert result["Available"] is False
    assert "Reason" in result


def test_bearish_pcr():
    chain = _fixture_chain()
    # Flip so calls dominate open interest -> bearish PCR
    chain["records"]["data"][0]["CE"]["openInterest"] = 5000

    result = analyze_option_chain(chain)

    assert result["PCR"] < 0.8
    assert result["Bias"] == "Bearish"
