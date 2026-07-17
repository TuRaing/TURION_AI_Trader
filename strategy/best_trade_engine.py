NEWS_AGREE_BONUS = 10
NEWS_DISAGREE_PENALTY = 10


def _news_adjustment(bias, news_sentiment):
    """
    Small confidence nudge depending on whether the shared news-headline
    pool agrees or disagrees with a candidate's bias. Neutral news, or
    no relevant headlines at all, makes no adjustment.
    """

    if news_sentiment is None or news_sentiment["Sentiment"] == "Neutral":
        return 0

    if news_sentiment["Sentiment"] == bias:
        return NEWS_AGREE_BONUS

    return -NEWS_DISAGREE_PENALTY


def rank_trade_candidates(stock_candidates, options_candidates, news_sentiment_by_symbol):
    """
    Build one ranked list where equity (stock/index) candidates and
    index options candidates are comparable on the same confidence scale.

    Parameters
    ----------
    stock_candidates : list of dict
        Output of strategy.watchlist_scanner.scan_watchlist(...) -
        each dict has Name/Symbol/Decision/Bias/Confidence/Price/... .
        Index entries (e.g. "NIFTY 50", "BANK NIFTY") should already be
        excluded by the caller - those are represented via
        options_candidates instead.
    options_candidates : list of dict
        One entry per index, each with:
        {"Name": str, "Bias": str, "Decision": str, "Confidence": float, "Reason": str}
        - Decision/Confidence/Reason coming from
        strategy.options_decision_engine.get_options_decision(...).
    news_sentiment_by_symbol : dict
        {symbol_name: news_engine.score_sentiment(...) result or None}.
        Every candidate name should have an entry (None if no relevant
        headlines were found for it).

    Returns
    -------
    list of dict, sorted by Final Confidence descending. Each entry
    keeps its original fields plus "Type" and "Final Confidence".
    """

    ranked = []

    for candidate in stock_candidates:

        if candidate["Decision"] not in ("BUY", "SELL"):
            continue

        news = news_sentiment_by_symbol.get(candidate["Name"])
        adjustment = _news_adjustment(candidate["Bias"], news)

        final_confidence = round(max(0.0, min(100.0, candidate["Confidence"] + adjustment)), 1)

        ranked.append({
            **candidate,
            "Type": "Equity Intraday",
            "Final Confidence": final_confidence,
        })

    for option in options_candidates:

        if option["Decision"] not in ("BUY CE", "BUY PE"):
            continue

        news = news_sentiment_by_symbol.get(option["Name"])
        adjustment = _news_adjustment(option["Bias"], news)

        final_confidence = round(max(0.0, min(100.0, option["Confidence"] + adjustment)), 1)

        ranked.append({
            "Name": option["Name"],
            "Symbol": None,
            "Decision": option["Decision"],
            "Bias": option["Bias"],
            "Confidence": option["Confidence"],
            "Reason": option["Reason"],
            "Type": "Index Option (CE/PE)",
            "Final Confidence": final_confidence,
        })

    ranked.sort(key=lambda r: r["Final Confidence"], reverse=True)

    return ranked


def pick_best_trade(ranked, top_n=5):
    """
    Lock the single best trade of the day out of an already-ranked list.

    Returns
    -------
    dict
    """

    if not ranked:

        return {
            "Best Trade": None,
            "Reason": "No candidate cleared BUY/SELL/BUY CE/BUY PE with usable confidence today.",
            "Ranked": [],
        }

    best = ranked[0]

    return {
        "Best Trade": best,
        "Reason": (
            f"{best['Name']} ({best['Type']}) ranked highest at "
            f"{best['Final Confidence']}% confidence."
        ),
        "Ranked": ranked[:top_n],
    }
