import feedparser

NEWS_FEEDS = [
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
]

POSITIVE_WORDS = [
    "surge", "rally", "jump", "gain", "gains", "rises", "rise", "rising",
    "soar", "soars", "beat", "beats", "upgrade", "upgraded", "record high",
    "outperform", "buy", "bullish", "strong", "profit", "growth", "recovery",
    "boost", "rebound",
]

NEGATIVE_WORDS = [
    "plunge", "plunges", "crash", "crashes", "fall", "falls", "falling",
    "slump", "slumps", "drop", "drops", "downgrade", "downgraded",
    "record low", "underperform", "sell", "bearish", "weak", "loss",
    "losses", "decline", "selloff", "sell-off", "recession", "default",
]


def fetch_headlines(feed_urls=None, limit=30):
    """
    Pull headlines from RSS feeds. Each feed is fetched independently -
    one dead/unreachable feed does not stop the others.

    Returns
    -------
    list of str
    """

    feed_urls = feed_urls if feed_urls is not None else NEWS_FEEDS

    headlines = []

    for url in feed_urls:

        try:

            parsed = feedparser.parse(url)

            for entry in parsed.entries:

                title = entry.get("title")

                if title:
                    headlines.append(title.strip())

        except Exception as error:

            print(f"Skipped news feed {url}: {error}")

    return headlines[:limit]


def score_sentiment(headlines, keywords=None):
    """
    Keyword-lexicon sentiment score, same transparent rule-based
    philosophy as the AI Decision Engine (not a trained model).

    Parameters
    ----------
    headlines : list of str
    keywords : list of str, optional
        If given, only headlines mentioning at least one keyword
        (case-insensitive) are scored - lets one shared headline pool
        give a per-symbol read instead of a network call per symbol.

    Returns
    -------
    dict
    """

    if keywords:

        keywords_lower = [k.lower() for k in keywords]

        relevant = [
            h for h in headlines
            if any(k in h.lower() for k in keywords_lower)
        ]

    else:

        relevant = list(headlines)

    positive = 0
    negative = 0

    for headline in relevant:

        text = headline.lower()

        is_positive = any(word in text for word in POSITIVE_WORDS)
        is_negative = any(word in text for word in NEGATIVE_WORDS)

        if is_positive and not is_negative:
            positive += 1

        elif is_negative and not is_positive:
            negative += 1

    neutral = len(relevant) - positive - negative

    total = positive + negative

    score = (positive - negative) / total if total > 0 else 0.0

    if score > 0.15:
        sentiment = "Bullish"

    elif score < -0.15:
        sentiment = "Bearish"

    else:
        sentiment = "Neutral"

    confidence = round(abs(score) * 100, 1)

    return {
        "Headlines": relevant,
        "Positive": positive,
        "Negative": negative,
        "Neutral": neutral,
        "Sentiment": sentiment,
        "Score": round(score, 2),
        "Confidence": confidence,
    }


def classify_headline_sentiment(headline):
    """
    Single-headline Bullish/Bearish/Neutral tag using the same keyword
    lexicon as score_sentiment(), for UI display (e.g. the mobile app's
    News tab) where each headline needs its own tag rather than an
    aggregate score.

    Returns
    -------
    str
    """

    text = headline.lower()

    is_positive = any(word in text for word in POSITIVE_WORDS)
    is_negative = any(word in text for word in NEGATIVE_WORDS)

    if is_positive and not is_negative:
        return "Bullish"

    if is_negative and not is_positive:
        return "Bearish"

    return "Neutral"


def get_market_news_sentiment(keywords=None, limit=30):
    """
    I/O convenience wrapper: fetch + score in one call.

    Returns
    -------
    dict (see score_sentiment)
    """

    headlines = fetch_headlines(limit=limit)

    return score_sentiment(headlines, keywords)
