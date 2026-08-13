from strategy.options_strategies import ALL_STRATEGIES


def test_all_strategies_has_29_books():
    # 5 original strategies + 5 threshold variants (x 2 indices each) +
    # 1 BANKNIFTY-only vix_filter book + 2 oi_footprint books + 2
    # credit_spread books + 2 pcr_momentum books + 2 max_pain_drift
    # books (both deployed 13-Aug, same day they were built).
    assert len(ALL_STRATEGIES) == 29


def test_original_books_have_no_daily_profit_lock():
    # vix_filter, oi_footprint, credit_spread, pcr_momentum, and
    # max_pain_drift have no daily_profit_lock key at all (standalone
    # strategies, not part of the make_strategy()/make_st4_config()/
    # make_gapfill_config() family that offers that flag) - excluded
    # here rather than asserting on a key they were never given.
    standalone_names = {"vix_filter", "oi_footprint", "credit_spread", "pcr_momentum", "max_pain_drift"}
    originals = [
        cfg for _, cfg in ALL_STRATEGIES
        if cfg.get("group") != "threshold" and cfg["name"] not in standalone_names
    ]

    assert len(originals) == 10
    assert all(cfg["daily_profit_lock"] is False for cfg in originals)


def test_vix_filter_book_is_banknifty_only():
    vix_books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] == "vix_filter"]

    assert len(vix_books) == 1
    assert vix_books[0]["index"] == "BANKNIFTY"


def test_oi_footprint_runs_on_both_indices():
    oi_books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] == "oi_footprint"]

    assert len(oi_books) == 2
    assert {cfg["index"] for cfg in oi_books} == {"NIFTY", "BANKNIFTY"}


def test_credit_spread_runs_on_both_indices():
    cs_books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] == "credit_spread"]

    assert len(cs_books) == 2
    assert {cfg["index"] for cfg in cs_books} == {"NIFTY", "BANKNIFTY"}


def test_pcr_momentum_runs_on_both_indices():
    books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] == "pcr_momentum"]

    assert len(books) == 2
    assert {cfg["index"] for cfg in books} == {"NIFTY", "BANKNIFTY"}


def test_max_pain_drift_runs_on_both_indices():
    books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] == "max_pain_drift"]

    assert len(books) == 2
    assert {cfg["index"] for cfg in books} == {"NIFTY", "BANKNIFTY"}


def test_threshold_books_all_have_daily_profit_lock_on():
    threshold = [cfg for _, cfg in ALL_STRATEGIES if cfg.get("group") == "threshold"]

    assert len(threshold) == 10
    assert all(cfg["daily_profit_lock"] is True for cfg in threshold)


def test_every_book_has_a_unique_portfolio_file():
    files = [cfg["portfolio_file"] for _, cfg in ALL_STRATEGIES]

    assert len(files) == len(set(files))


def test_every_book_has_a_unique_name_index_pair():
    # Each strategy `name` repeats once per index (NIFTY/BANKNIFTY) by
    # design - portfolio_file is the true uniqueness key, checked above.
    # This checks the (name, index) pair itself has no accidental dupes.
    pairs = [(cfg["name"], cfg["index"]) for _, cfg in ALL_STRATEGIES]

    assert len(pairs) == len(set(pairs))


def test_threshold_names_differ_from_their_original_counterpart():
    names = {cfg["name"] for _, cfg in ALL_STRATEGIES}

    for base in ("simple_st1", "st2", "st3", "st4", "gapfill"):
        assert base in names
        assert f"{base}_threshold" in names
