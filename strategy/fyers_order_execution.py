import requests

from strategy.fyers_auth import _app_id, get_access_token
from strategy.options_transaction_costs import calculate_options_round_trip_cost

# Added 14-Aug-2026 - broker-side Stop-Loss order support, built after
# the retrospective replay in doc/PROJECT_STATUS.md's "oi_footprint
# EXIT-MECHANISM DEEP DIVE" entry showed capping ONLY the Stop-Loss
# side of a trade at Rs 2,000 (leaving Target/profit exits exactly as
# they are today - see that entry, letting profit run has been net-
# beneficial historically) would have improved oi_footprint/NIFTY's
# real 31-trade total by 81% (Rs 41,479 -> Rs 75,032) and BANKNIFTY's
# by a smaller but still real margin. The root problem: today's Stop-
# Loss check is periodic (~1-min external cron-job.org trigger, see
# strategy/fyers_options_engine.py / fyers_options_oi_footprint.py),
# so real losses overshoot the intended -Rs 1,500 cap by 2x-10x before
# the next check even runs. A broker-side Stop order sits with the
# exchange itself and fires the instant the trigger price is touched -
# no dependency on script/VPS check cadence at all.
#
# NOT WIRED INTO ANYTHING - this module is deliberately dormant. No
# strategy module imports place_stop_loss_order(); nothing calls it on
# any schedule, workflow, or trigger. Per this repo's standing rule
# (see doc/PROJECT_STATUS.md's Development Rules and CLAUDE.md),
# Claude never executes a real trade - this function, if ever called
# with a real access token, WOULD place a real order on the user's
# Fyers account for real money. Building it now is explicitly at the
# user's request ("save karun thev, nantar karu" - build and hold, use
# later) as prep work for the Stage 3 Live Trading milestone, not an
# activation of anything. Wiring this into a live strategy is a
# separate, later decision - and per this repo's rules, the user still
# places/approves every real order even once this exists; this is
# meant to protect an ALREADY-USER-APPROVED open position, not to open
# one.
#
# UNTESTED against Fyers' real order endpoint (compute_stop_loss_
# trigger_price() below IS tested - it's pure arithmetic, no network
# call). place_stop_loss_order() itself has only been checked against
# Fyers' v3 API documentation, never fired against a real or sandbox
# account - the very first real call to it (even a tiny 1-lot test)
# should be treated as a live-money action requiring the user's
# explicit go-ahead, not assumed to work first time.

ORDERS_BASE_URL = "https://api-t1.fyers.in/api/v3"

ORDER_TYPE_STOP_MARKET = 3   # Fyers SL-M - fires as a market order once stopPrice is touched
SIDE_SELL = -1
SIDE_BUY = 1


def compute_stop_loss_trigger_price(entry_premium, lots, lot_size, max_loss_rupees=2000, tolerance=0.01, max_iterations=100):
    """
    Pure function - bisection search for the exit premium at which
    closing a long option position (bought at entry_premium) realizes
    a net loss of approximately max_loss_rupees, INCLUDING real round-
    trip transaction costs (strategy/options_transaction_costs.py) -
    the same cost model the live paper-trading engines already use, so
    this trigger price lines up with how Net PnL is computed elsewhere
    in this codebase.

    Returns
    -------
    float - the premium level to set as the broker-side Stop order's
    trigger price. None if no solution was found within the search
    bounds (shouldn't happen for a sane entry_premium).
    """

    low = 0.05
    high = entry_premium

    def net_pnl_at(exit_premium):
        gross = (exit_premium - entry_premium) * lots * lot_size
        cost = calculate_options_round_trip_cost(entry_premium, exit_premium, lot_size, lots)
        return gross - cost

    target = -abs(max_loss_rupees)

    if net_pnl_at(low) > target:
        # Even a near-worthless option doesn't lose max_loss_rupees at
        # this size - the position is too small for this cap to bind.
        return None

    for _ in range(max_iterations):
        mid = (low + high) / 2
        pnl = net_pnl_at(mid)

        if abs(pnl - target) <= tolerance:
            return round(mid, 2)

        if pnl < target:
            low = mid
        else:
            high = mid

    return round((low + high) / 2, 2)


def place_stop_loss_order(symbol, quantity, trigger_price, product_type="INTRADAY"):
    """
    Places a real broker-side SL-M (Stop Market) SELL order on the
    user's Fyers account, to close an existing long option position.

    NOT CALLED ANYWHERE IN THIS CODEBASE - see the module docstring
    above. Calling this with a real, valid access token places a real
    order for real money. Never call this from an automated/scheduled
    path without the user's explicit, current-session approval.

    Parameters
    ----------
    symbol : str - the exact Fyers option symbol already held long
        (e.g. "NSE:NIFTY2681824300PE").
    quantity : int - lots x lot_size, matching the open position.
    trigger_price : float - typically from compute_stop_loss_trigger_
        price() above.
    product_type : str - must match the product type the position was
        actually opened with (Fyers rejects a mismatched close order).

    Returns
    -------
    dict - Fyers' raw JSON response.
    """

    app_id = _app_id()
    token = get_access_token()

    payload = {
        "symbol": symbol,
        "qty": quantity,
        "type": ORDER_TYPE_STOP_MARKET,
        "side": SIDE_SELL,
        "productType": product_type,
        "limitPrice": 0,
        "stopPrice": trigger_price,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": False,
    }

    response = requests.post(
        f"{ORDERS_BASE_URL}/orders/sync",
        json=payload,
        headers={"Authorization": f"{app_id}:{token}"},
        timeout=15,
    )

    return response.json()
