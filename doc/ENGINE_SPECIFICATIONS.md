# TURION AI Trader

ENGINE SPECIFICATIONS

==========================================

Project

TURION AI Trader

Version

v0.0.5

Purpose

This document defines the responsibility,
inputs,
outputs,
and future scope of every Engine.

Every engine must have only one responsibility.

No engine should directly make BUY or SELL decisions.

The AI Decision Engine will combine the outputs
of all engines.

==========================================

ENGINE 1

Live Market Data Engine

Purpose

Download live market data.

Input

None

Output

Open
High
Low
Close
Volume

Future

Multi Timeframe
Multiple Symbols
Live Streaming

------------------------------------------

ENGINE 2

Indicator Engine

Purpose

Calculate technical indicators.

Current

EMA
RSI

Future

MACD
VWAP
ATR
ADX
SuperTrend
Bollinger Bands

Output

Indicator Values

------------------------------------------

ENGINE 3

Market State Engine

Purpose

Understand the overall market trend.

Possible States

Bullish

Bearish

Sideways

Future

Strong Bullish

Weak Bullish

Strong Bearish

Weak Bearish

Transition

Output

State

Strength

Confidence

Reason

------------------------------------------

ENGINE 4

Market Structure Engine

Purpose

Understand price structure.

Current

Swing High

Swing Low

HH

HL

LH

LL

Future

Strong Swing

Break Of Structure (BOS)

Change Of Character (CHOCH)

Trend Quality

Output

Trend

Structure

Swing Levels

Confidence

------------------------------------------

ENGINE 5

Support Resistance Engine

Purpose

Detect important price levels.

Future

Swing Based Levels

Cluster Levels

Dynamic Levels

Strong Support

Strong Resistance

Breakout

Breakdown

Retest

Output

Support

Resistance

Strength

Distance

Confidence

------------------------------------------

ENGINE 6

Candlestick Engine

Purpose

Identify price action patterns.

Patterns

Hammer

Doji

Bullish Engulfing

Bearish Engulfing

Morning Star

Evening Star

Future

Multi Candle Analysis

Output

Pattern

Strength

Confidence

------------------------------------------

ENGINE 7

Volume Engine

Purpose

Understand buying and selling pressure.

Output

High Volume

Low Volume

Buying Pressure

Selling Pressure

Volume Trend

Confidence

------------------------------------------

ENGINE 8

Volatility Engine

Purpose

Measure market volatility.

Current

ATR

Future

India VIX

Historical Volatility

Output

Volatility

Risk

Confidence

------------------------------------------

ENGINE 9

Option Chain Engine

Status: Implemented (strategy/option_chain_engine.py) - 17-Jul-26

Purpose

Understand option market.

Output

Call Writing

Put Writing

OI Change

PCR

Max Pain

IV

Confidence

Note

NSE blocks datacenter/cloud IPs (403) - this
engine returns real PCR/Max Pain/OI data only
from a non-blocked network (e.g. run locally
at home). On blocked networks (GitHub Actions
included) it returns {"Available": False,
"Reason": ...} instead of raising, so callers
degrade gracefully.

------------------------------------------

ENGINE 13

News Engine

Status: Implemented (strategy/news_engine.py) - 17-Jul-26

Purpose

Read market sentiment from financial news
headlines.

Input

RSS feeds (Moneycontrol, Economic Times -
free, no API key)

Output

Headlines

Positive / Negative / Neutral counts

Sentiment (Bullish / Bearish / Neutral)

Score

Confidence

Note

Keyword-lexicon based, same transparent
rule-based philosophy as the AI Decision
Engine - not a trained NLP/ML model.

------------------------------------------

ENGINE 14

Options Decision Engine

Status: Implemented (strategy/options_decision_engine.py) - 17-Jul-26

Purpose

Decide BUY CE / BUY PE / NO TRADE for index
options (NIFTY / BANKNIFTY intraday), combining
index price-action bias with the Option Chain
Engine's signal.

Kept fully separate from equity
signal_engine / ai_decision_engine /
paper_trading, per project rule that options
logic must never mix with normal stock/index
signal logic.

Input

Index Bias + Confidence (from AI Decision
Engine run on the index)

Option Chain Engine output

Output

Decision (BUY CE / BUY PE / NO TRADE)

Confidence

Reason

------------------------------------------

ENGINE 15

Best Trade Engine

Status: Implemented (strategy/best_trade_engine.py) - 17-Jul-26

Purpose

Rank every cleared candidate of the day -
Nifty 50 stocks (equity, from the Watchlist
Scanner + AI Decision Engine) and index options
(from the Options Decision Engine) - on one
comparable confidence scale, adjusted by News
Engine sentiment, and lock the single highest-
probability intraday pick.

Input

Watchlist Scanner results (stocks)

Options Decision Engine result (per index)

News Engine sentiment (per symbol)

Output

Best Trade (Name, Type, Decision, Bias,
Final Confidence)

Reason

Ranked shortlist (top 5)

Orchestrated by daily_best_trade.py, scheduled
via .github/workflows/best_trade_report.yml
(10:00 IST, Mon-Fri). Presentation-only via
report_engine.print_best_trade_report /
format_best_trade_message and
excel_report.save_best_trade - this engine
itself only returns structured data, same as
every other engine.

------------------------------------------

ENGINE 10

Risk Management Engine

Purpose

Protect trading capital.

Output

Risk %

Stop Loss

Target

Risk Reward Ratio

Position Size

------------------------------------------

ENGINE 11

Reasoning Engine

Purpose

Combine outputs from all engines.

This engine never calculates indicators.

It only understands.

Input

Market State

Market Structure

Support Resistance

Candlestick

Volume

Volatility

Option Chain

Risk

Output

Reason

Confidence

Trade Quality

------------------------------------------

ENGINE 12

AI Decision Engine

Purpose

Generate final decision.

Possible Decisions

BUY CE

BUY PE

BUY STOCK

SELL

WAIT

NO TRADE

Output

Decision

Confidence

Reason

Risk

==========================================

Development Rule

Every engine must

Have one responsibility

Be reusable

Be independent

Be testable

Never depend on UI

Never directly execute trades

==========================================

END OF DOCUMENT