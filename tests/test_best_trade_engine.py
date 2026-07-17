from strategy.best_trade_engine import (
    _news_adjustment,
    rank_trade_candidates,
    pick_best_trade,
)


# ---------------- news adjustment ----------------

def test_news_agrees_gives_bonus():
    assert _news_adjustment("Bullish", {"Sentiment": "Bullish"}) == 10


def test_news_disagrees_gives_penalty():
    assert _news_adjustment("Bullish", {"Sentiment": "Bearish"}) == -10


def test_news_neutral_gives_no_adjustment():
    assert _news_adjustment("Bullish", {"Sentiment": "Neutral"}) == 0


def test_no_news_gives_no_adjustment():
    assert _news_adjustment("Bullish", None) == 0


# ---------------- ranking ----------------

def _stock_candidates():
    return [
        {"Name": "TCS", "Symbol": "TCS.NS", "Decision": "BUY", "Bias": "Bullish",
         "Confidence": 70, "Price": 3800, "ATR": 40, "Candle Pattern": "Hammer"},
        {"Name": "ITC", "Symbol": "ITC.NS", "Decision": "NO TRADE", "Bias": "Neutral",
         "Confidence": 0, "Price": 400, "ATR": 5, "Candle Pattern": "No Pattern"},
        {"Name": "INFY", "Symbol": "INFY.NS", "Decision": "SELL", "Bias": "Bearish",
         "Confidence": 65, "Price": 1500, "ATR": 15, "Candle Pattern": "Shooting Star"},
    ]


def _options_candidates():
    return [
        {"Name": "NIFTY 50", "Bias": "Bullish", "Decision": "BUY CE",
         "Confidence": 75, "Reason": "Price action confirmed by option chain."},
        {"Name": "BANK NIFTY", "Bias": "Neutral", "Decision": "NO TRADE",
         "Confidence": 0, "Reason": "No clear bias."},
    ]


def _news_map():
    return {
        "TCS": {"Sentiment": "Bullish"},
        "INFY": {"Sentiment": "Bullish"},  # disagrees with INFY's Bearish bias
        "ITC": None,
        "NIFTY 50": {"Sentiment": "Bullish"},
    }


def test_no_trade_candidates_are_filtered_out():
    ranked = rank_trade_candidates(_stock_candidates(), [], {})
    names = [r["Name"] for r in ranked]

    assert "ITC" not in names


def test_no_trade_options_are_filtered_out():
    ranked = rank_trade_candidates([], _options_candidates(), {})
    names = [r["Name"] for r in ranked]

    assert "BANK NIFTY" not in names
    assert "NIFTY 50" in names


def test_ranking_and_news_adjustment_end_to_end():
    ranked = rank_trade_candidates(_stock_candidates(), _options_candidates(), _news_map())

    by_name = {r["Name"]: r for r in ranked}

    assert by_name["TCS"]["Final Confidence"] == 80.0  # 70 + 10 (agrees)
    assert by_name["INFY"]["Final Confidence"] == 55.0  # 65 - 10 (disagrees)
    assert by_name["NIFTY 50"]["Final Confidence"] == 85.0  # 75 + 10 (agrees)
    assert by_name["NIFTY 50"]["Type"] == "Index Option (CE/PE)"
    assert by_name["TCS"]["Type"] == "Equity Intraday"

    # sorted descending by Final Confidence
    assert [r["Name"] for r in ranked] == ["NIFTY 50", "TCS", "INFY"]


def test_confidence_clamped_to_100():
    stock = [{"Name": "TCS", "Symbol": "TCS.NS", "Decision": "BUY", "Bias": "Bullish",
              "Confidence": 95, "Price": 3800, "ATR": 40, "Candle Pattern": "Hammer"}]
    news = {"TCS": {"Sentiment": "Bullish"}}

    ranked = rank_trade_candidates(stock, [], news)

    assert ranked[0]["Final Confidence"] == 100.0


def test_pick_best_trade_returns_top_candidate():
    ranked = rank_trade_candidates(_stock_candidates(), _options_candidates(), _news_map())
    result = pick_best_trade(ranked)

    assert result["Best Trade"]["Name"] == "NIFTY 50"
    assert len(result["Ranked"]) <= 5


def test_pick_best_trade_handles_no_candidates():
    result = pick_best_trade([])

    assert result["Best Trade"] is None
    assert result["Ranked"] == []
