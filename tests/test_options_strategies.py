from strategy.options_strategies import ALL_STRATEGIES


def test_all_strategies_has_59_books():
    # 5 original strategies + 5 threshold variants (x 2 indices each) +
    # 1 BANKNIFTY-only vix_filter book + 2 oi_footprint books + 2
    # credit_spread books + 2 pcr_momentum books + 2 max_pain_drift
    # books + 2 pcr_vix_combo books + 2 oi_iv_combo books (all deployed
    # 13-Aug, same day built) + 8 _slcap books (14-Aug, hybrid Stop-
    # Loss cap on the first 8 previously-weak RSI-family books - see
    # PROJECT_STATUS.md's "MAJOR CORRECTION" + "HYBRID SL CAP" entries)
    # + 12 oi_footprint variant books (14-Aug, 6 exit-mechanism ideas x
    # 2 indices each - see fyers_options_oi_footprint_variants.py) +
    # 6 more threshold _slcap books (14-Aug, later the same day -
    # simple_st1_threshold x2, st2_threshold/NIFTY, st3_threshold/
    # BANKNIFTY, st4_threshold x2 - completing hybrid-cap coverage on
    # every threshold book that was retrospectively tested).
    assert len(ALL_STRATEGIES) == 59


def test_original_books_have_no_daily_profit_lock():
    # vix_filter, oi_footprint, credit_spread, pcr_momentum, max_pain_
    # drift, pcr_vix_combo, oi_iv_combo, and the 6 oi_footprint variant
    # names have no daily_profit_lock key at all (standalone strategies,
    # not part of the make_strategy()/make_st4_config()/make_gapfill_
    # config() family that offers that flag) - excluded here rather
    # than asserting on a key they were never given.
    standalone_names = {"vix_filter", "oi_footprint", "credit_spread", "pcr_momentum", "max_pain_drift",
                         "pcr_vix_combo", "oi_iv_combo", "oi_hybrid_sl", "oi_hybrid_sl_trailing",
                         "oi_hybrid_sl_atr", "oi_hybrid_sl_breakeven", "oi_hybrid_sl_laddered",
                         "oi_hybrid_sl_indicator"}
    originals = [
        cfg for _, cfg in ALL_STRATEGIES
        if cfg.get("group") != "threshold" and cfg["name"] not in standalone_names
    ]

    # 10 original (non-threshold, non-standalone) books + 6 non-
    # threshold _slcap books (simple_st1_slcap/st2_slcap/st3_slcap x 2
    # indices each - the other 2 _slcap books are threshold-group).
    assert len(originals) == 16
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


def test_pcr_vix_combo_runs_on_both_indices():
    books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] == "pcr_vix_combo"]

    assert len(books) == 2
    assert {cfg["index"] for cfg in books} == {"NIFTY", "BANKNIFTY"}


def test_oi_iv_combo_runs_on_both_indices():
    books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] == "oi_iv_combo"]

    assert len(books) == 2
    assert {cfg["index"] for cfg in books} == {"NIFTY", "BANKNIFTY"}


def test_threshold_books_all_have_daily_profit_lock_on():
    threshold = [cfg for _, cfg in ALL_STRATEGIES if cfg.get("group") == "threshold"]

    # 10 original threshold books + 8 threshold _slcap books (st3_
    # threshold_slcap x2, st2_threshold_slcap x2, simple_st1_threshold_
    # slcap x2, st4_threshold_slcap x2 - every threshold book that was
    # retrospectively tested with the hybrid cap now has one).
    assert len(threshold) == 18
    assert all(cfg["daily_profit_lock"] is True for cfg in threshold)


ALL_SLCAP_NAMES = {
    "simple_st1_slcap", "st2_slcap", "st3_slcap",
    "st3_threshold_slcap", "st2_threshold_slcap", "simple_st1_threshold_slcap", "st4_threshold_slcap",
}


def test_slcap_books_have_hybrid_sl_cap_set():
    slcap_books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] in ALL_SLCAP_NAMES]

    # 6 non-threshold (simple_st1_slcap/st2_slcap/st3_slcap x2) + 8
    # threshold (st3_threshold_slcap x2, st2_threshold_slcap x2,
    # simple_st1_threshold_slcap x2, st4_threshold_slcap x2) = 14.
    assert len(slcap_books) == 14
    assert all(cfg["hybrid_sl_cap_pct"] == 2.0 for cfg in slcap_books)


def test_non_slcap_books_have_no_hybrid_sl_cap():
    # oi_footprint variant books also use hybrid_sl_cap_pct (see
    # fyers_options_oi_footprint_variants.py) - excluded here alongside
    # the _slcap RSI-family/st4 books, all are legitimate hybrid-cap
    # users.
    excluded_names = ALL_SLCAP_NAMES | {
        "oi_hybrid_sl", "oi_hybrid_sl_trailing", "oi_hybrid_sl_atr", "oi_hybrid_sl_breakeven",
        "oi_hybrid_sl_laddered", "oi_hybrid_sl_indicator",
    }
    non_slcap_books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] not in excluded_names]

    for cfg in non_slcap_books:
        assert cfg.get("hybrid_sl_cap_pct") is None


def test_oi_footprint_variant_books_run_on_both_indices():
    variant_names = {"oi_hybrid_sl", "oi_hybrid_sl_trailing", "oi_hybrid_sl_atr", "oi_hybrid_sl_breakeven",
                      "oi_hybrid_sl_laddered", "oi_hybrid_sl_indicator"}

    for name in variant_names:
        books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] == name]
        assert len(books) == 2
        assert {cfg["index"] for cfg in books} == {"NIFTY", "BANKNIFTY"}


def test_oi_footprint_variants_have_distinct_extra_exit_tags():
    expected = {
        "oi_hybrid_sl": None,
        "oi_hybrid_sl_trailing": "trailing",
        "oi_hybrid_sl_atr": "atr",
        "oi_hybrid_sl_breakeven": "breakeven",
        "oi_hybrid_sl_laddered": "laddered",
        "oi_hybrid_sl_indicator": "indicator",
    }

    for name, extra_exit in expected.items():
        books = [cfg for _, cfg in ALL_STRATEGIES if cfg["name"] == name]
        assert all(cfg["extra_exit"] == extra_exit for cfg in books)


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
