# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260717-001

--------------------------------------------------

Date

17-Jul-2026

--------------------------------------------------

Version

v0.0.7 → v0.0.8

==================================================

Today's Achievements

✅ News Engine (strategy/news_engine.py) - free RSS
   feeds (Moneycontrol + Economic Times, no API key),
   keyword-lexicon sentiment scoring (same transparent
   rule-based philosophy as the AI Decision Engine)

✅ Option Chain Engine (strategy/option_chain_engine.py)
   - implements Engine 9 from the spec doc (PCR, Max
   Pain, Call/Put Writing, IV, Confidence) against the
   NSE public option-chain API. Degrades gracefully -
   returns {"Available": False, "Reason": ...} instead
   of crashing when NSE blocks the request (the
   long-documented datacenter-IP 403 block)

✅ Options Decision Engine (strategy/options_decision_engine.py)
   - decides BUY CE / BUY PE / NO TRADE for NIFTY /
   BANKNIFTY intraday by combining index price-action
   bias with the Option Chain Engine. Kept fully
   separate from equity signal_engine / paper_trading,
   per the project's options-isolation rule

✅ Best Trade Engine (strategy/best_trade_engine.py) -
   ranks every cleared Nifty 50 stock candidate and
   both index options candidates on one confidence
   scale (with a news-agreement bonus/penalty), then
   locks the single highest-probability intraday pick
   for the day, plus a top-5 shortlist for context

✅ daily_best_trade.py - new orchestration script
   wiring Watchlist Scanner + News Engine + Option
   Chain Engine + Options Decision Engine + Best
   Trade Engine → Report Engine → Telegram / Excel
   ("Best Trade" sheet, report/excel_report.save_best_trade)

✅ .github/workflows/best_trade_report.yml - new
   scheduled workflow, 10:00 IST Mon-Fri (45 min
   after NSE open)

✅ 29 new pytest unit tests (news_engine,
   option_chain_engine, options_decision_engine,
   best_trade_engine - all pure logic, fixture-driven,
   no network) - 74 total tests passing (was 45)

✅ Verified daily_best_trade.py runs end-to-end
   without crashing when both yfinance and the news/
   option-chain sources are blocked (this dev sandbox's
   proxy 403s Yahoo Finance, NSE, and the RSS feeds) -
   confirms the graceful-degradation design works as
   intended rather than assuming it would

==================================================

Known Issues / Blockers

• Option Chain Engine still only gets real PCR/Max
  Pain/OI data from a non-blocked network (NSE 403s
  datacenter/cloud IPs, including this dev sandbox and
  likely GitHub Actions too) - unconfirmed until the
  first scheduled cloud run.

• News Engine's RSS feeds (Moneycontrol/ET) were
  blocked in this dev sandbox during testing - GitHub
  Actions runners have open internet by default so
  this is expected to work there, but unconfirmed
  until the first scheduled run. Watch for "Headlines
  fetched: 0" in the Action log.

• TATAMOTORS.NS / LTIM.NS still return no data from
  Yahoo Finance - carried over, unresolved.

• Broker not yet selected - once chosen, its data API
  may be a more reliable Option Chain source than the
  free NSE scrape.

==================================================

Development Rule

No engine should directly make trading decisions in
isolation. Every engine returns structured data.
Report Engine displays. Excel Engine stores history.
Options logic (Option Chain Engine, Options Decision
Engine) kept fully separate from normal NIFTY / stock
trading logic - only the Best Trade Engine reads both,
and only to rank/compare, never to alter either
engine's own math.

Claude never executes a real trade - the Best Trade
Engine only recommends; final action is always the
user's.

==================================================

Next Session

1. Watch the first few scheduled Daily Best Trade
   Report runs (10:00 IST) - confirm whether GitHub
   Actions can reach the RSS feeds and whether NSE
   still blocks the option chain from that network

2. Commit Desktop App (PySide6) and Android App
   (Flutter, mobile_app/) to the repo (carried over)

3. Fix TATAMOTORS / LTIM ticker symbols (carried over)

4. Select broker (Upstox / Angel One) → Broker
   Integration (carried over)

5. Tune the News Engine keyword lexicon and Best
   Trade Engine weighting once real daily picks can
   be compared against outcomes

==================================================

END OF SESSION
