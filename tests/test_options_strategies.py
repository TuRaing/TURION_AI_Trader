from strategy.options_strategies import ALL_STRATEGIES


def test_all_strategies_has_20_books():
    # 5 original strategies + 5 threshold variants, x 2 indices each.
    assert len(ALL_STRATEGIES) == 20


def test_original_books_have_no_daily_profit_lock():
    originals = [cfg for _, cfg in ALL_STRATEGIES if cfg.get("group") != "threshold"]

    assert len(originals) == 10
    assert all(cfg["daily_profit_lock"] is False for cfg in originals)


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
