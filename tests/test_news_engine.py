from strategy.news_engine import score_sentiment


def test_all_positive_headlines_is_bullish():
    headlines = [
        "Sensex surges 500 points on strong earnings",
        "Nifty rallies to record high, banks lead gains",
    ]
    result = score_sentiment(headlines)

    assert result["Positive"] == 2
    assert result["Negative"] == 0
    assert result["Sentiment"] == "Bullish"
    assert result["Score"] == 1.0


def test_all_negative_headlines_is_bearish():
    headlines = [
        "Markets crash as global recession fears grow",
        "Nifty plunges, IT stocks slump on weak guidance",
    ]
    result = score_sentiment(headlines)

    assert result["Positive"] == 0
    assert result["Negative"] == 2
    assert result["Sentiment"] == "Bearish"
    assert result["Score"] == -1.0


def test_mixed_and_irrelevant_headlines_are_neutral():
    headlines = [
        "RBI holds policy meeting on Thursday",
        "Company announces new product launch",
    ]
    result = score_sentiment(headlines)

    assert result["Positive"] == 0
    assert result["Negative"] == 0
    assert result["Neutral"] == 2
    assert result["Sentiment"] == "Neutral"
    assert result["Score"] == 0.0


def test_no_headlines_is_neutral_with_zero_confidence():
    result = score_sentiment([])

    assert result["Sentiment"] == "Neutral"
    assert result["Score"] == 0.0
    assert result["Confidence"] == 0.0


def test_keyword_filter_only_scores_relevant_headlines():
    headlines = [
        "TCS profit beats estimates, stock gains",
        "ITC shares fall after weak results",
        "Weather forecast: heavy rain expected",
    ]
    result = score_sentiment(headlines, keywords=["TCS"])

    assert result["Headlines"] == ["TCS profit beats estimates, stock gains"]
    assert result["Positive"] == 1
    assert result["Negative"] == 0
    assert result["Sentiment"] == "Bullish"


def test_headline_with_both_positive_and_negative_words_is_neutral():
    headlines = ["Stock gains initially before crash in late trade"]
    result = score_sentiment(headlines)

    assert result["Positive"] == 0
    assert result["Negative"] == 0
    assert result["Neutral"] == 1
