def get_options_decision(index_bias, index_confidence, option_chain_analysis, confidence_threshold=60):
    """
    Decide BUY CE / BUY PE / NO TRADE for index options (NIFTY /
    BANKNIFTY intraday).

    Kept fully separate from the equity signal_engine / ai_decision_engine
    / paper_trading logic - this is the only place option (CALL/PUT)
    decisions are made, per project rule that options logic must not mix
    with normal stock/index signal logic.

    Parameters
    ----------
    index_bias : str
        "Bullish" / "Bearish" / "Neutral" - from ai_decision_engine run
        on the index price action (^NSEI / ^NSEBANK).
    index_confidence : float
        Confidence (0-100) from that same ai_decision_engine call.
    option_chain_analysis : dict
        Output of option_chain_engine.get_option_chain_analysis(). May
        have "Available": False if NSE blocked the request - the
        decision then falls back to price action alone, with a
        confidence penalty since it lacks OI confirmation.

    Returns
    -------
    dict
    """

    option_available = option_chain_analysis.get("Available", False)

    if option_available:

        option_bias = option_chain_analysis["Bias"]
        option_confidence = option_chain_analysis["Confidence"]

        agrees = (
            option_bias == index_bias
            or option_bias == "Neutral"
            or index_bias == "Neutral"
        )

        if not agrees:

            return {
                "Decision": "NO TRADE",
                "Confidence": 0.0,
                "Reason": (
                    f"Price action is {index_bias} but option chain OI is "
                    f"{option_bias} - conflicting signals, skipping."
                ),
            }

        confidence = round((index_confidence + option_confidence) / 2, 1)
        reason = f"Price action {index_bias} confirmed by option chain PCR/OI ({option_bias})."

    else:

        # No OI confirmation available (NSE blocked this network) -
        # trade price action alone, but penalize confidence since one
        # signal source is missing.
        confidence = round(index_confidence * 0.7, 1)
        reason = f"Price action {index_bias} only - option chain data unavailable ({option_chain_analysis.get('Reason', 'unknown')})."

    if index_bias == "Bullish" and confidence >= confidence_threshold:
        decision = "BUY CE"

    elif index_bias == "Bearish" and confidence >= confidence_threshold:
        decision = "BUY PE"

    elif index_bias == "Neutral":

        decision = "NO TRADE"
        confidence = 0.0
        reason = "Index price action is Neutral - no directional bias to trade."

    else:

        decision = "NO TRADE"
        reason = f"{reason} Confidence {confidence}% is below the {confidence_threshold}% threshold."

    return {
        "Decision": decision,
        "Confidence": confidence,
        "Reason": reason,
    }
