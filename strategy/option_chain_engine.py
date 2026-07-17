import requests

BASE_URL = "https://www.nseindia.com"
CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_option_chain(symbol="NIFTY", timeout=10):
    """
    Pull the raw NSE option chain JSON for an index.

    NSE 403s requests coming from datacenter/cloud IPs (a documented,
    long-standing block) - this only returns real data from a
    non-blocked network (e.g. run locally at home). Any failure
    (403, timeout, malformed response) is caught here and returns
    None instead of raising, so callers degrade gracefully.

    Returns
    -------
    dict or None
    """

    try:

        session = requests.Session()
        session.headers.update(HEADERS)

        # Warm up: NSE requires cookies from the homepage before the API call.
        session.get(BASE_URL, timeout=timeout)

        response = session.get(CHAIN_URL.format(symbol=symbol), timeout=timeout)

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as error:

        print(f"Option chain fetch failed for {symbol}: {error}")
        return None


def analyze_option_chain(raw_json, top_n=3):
    """
    Pure analysis of an already-fetched NSE option chain JSON.

    Returns
    -------
    dict
    """

    records = raw_json.get("records", {})
    rows = records.get("data", [])

    if not rows:

        return {
            "Available": False,
            "Reason": "Option chain response had no strike data",
        }

    total_call_oi = 0
    total_put_oi = 0
    iv_values = []
    pain_by_strike = {}

    for row in rows:

        strike = row.get("strikePrice")
        ce = row.get("CE")
        pe = row.get("PE")

        if ce:

            total_call_oi += ce.get("openInterest", 0)

            if ce.get("impliedVolatility"):
                iv_values.append(ce["impliedVolatility"])

        if pe:

            total_put_oi += pe.get("openInterest", 0)

            if pe.get("impliedVolatility"):
                iv_values.append(pe["impliedVolatility"])

        pain_by_strike[strike] = row

    pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi else 0.0

    max_pain = _calculate_max_pain(pain_by_strike)

    call_writing = sorted(
        (r for r in rows if r.get("CE")),
        key=lambda r: r["CE"].get("changeinOpenInterest", 0),
        reverse=True,
    )[:top_n]

    put_writing = sorted(
        (r for r in rows if r.get("PE")),
        key=lambda r: r["PE"].get("changeinOpenInterest", 0),
        reverse=True,
    )[:top_n]

    avg_iv = round(sum(iv_values) / len(iv_values), 2) if iv_values else 0.0

    if pcr > 1.2:
        bias = "Bullish"

    elif pcr < 0.8:
        bias = "Bearish"

    else:
        bias = "Neutral"

    confidence = round(min(abs(pcr - 1.0), 1.0) * 100, 1)

    return {
        "Available": True,
        "PCR": pcr,
        "Max Pain": max_pain,
        "Call Writing": [r["strikePrice"] for r in call_writing],
        "Put Writing": [r["strikePrice"] for r in put_writing],
        "IV": avg_iv,
        "Bias": bias,
        "Confidence": confidence,
    }


def _calculate_max_pain(pain_by_strike):
    """
    Max Pain = the strike at which total payout to option holders
    (across every other strike) is smallest, i.e. most option buyers
    lose the most - price tends to gravitate here near expiry.
    """

    strikes = list(pain_by_strike.keys())

    if not strikes:
        return None

    best_strike = None
    lowest_payout = None

    for candidate in strikes:

        payout = 0

        for row in pain_by_strike.values():

            strike = row.get("strikePrice")
            ce = row.get("CE")
            pe = row.get("PE")

            if ce and candidate > strike:
                payout += ce.get("openInterest", 0) * (candidate - strike)

            if pe and candidate < strike:
                payout += pe.get("openInterest", 0) * (strike - candidate)

        if lowest_payout is None or payout < lowest_payout:

            lowest_payout = payout
            best_strike = candidate

    return best_strike


def get_option_chain_analysis(symbol="NIFTY"):
    """
    I/O convenience wrapper: fetch + analyze in one call.

    Returns
    -------
    dict (see analyze_option_chain), or {"Available": False, "Reason": ...}
    if the fetch failed (e.g. blocked datacenter IP).
    """

    raw_json = fetch_option_chain(symbol)

    if raw_json is None:

        return {
            "Available": False,
            "Reason": "NSE blocked this network (datacenter IP) or request failed",
        }

    return analyze_option_chain(raw_json)
