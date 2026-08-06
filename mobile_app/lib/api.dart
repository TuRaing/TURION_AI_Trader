import 'dart:convert';
import 'package:http/http.dart' as http;

const _repoRawBase =
    'https://raw.githubusercontent.com/TuRaing/TURION_AI_Trader/main';

const portfolioUrl = '$_repoRawBase/reports/paper_portfolio.json';
const bestTradeShortlistUrl = '$_repoRawBase/reports/best_trade_shortlist.json';
const bestTradePortfolioUrl = '$_repoRawBase/reports/best_trade_portfolio.json';
const bestTradePickUrl = '$_repoRawBase/reports/best_trade_pick.json';
const candlesUrl = '$_repoRawBase/reports/candles.json';

// Added 04-Aug-2026 - Fyers-sourced TEST portfolios (strategy/fyers_
// paper_trading.py, strategy/fyers_best_trade_paper_trading.py), kept
// fully separate from the live yfinance ones above - own files, own
// screen (see fyers_portfolio_screen.dart), never mixed.
const fyersPortfolioUrl = '$_repoRawBase/reports/fyers_test_portfolio.json';
const fyersBestTradePortfolioUrl = '$_repoRawBase/reports/fyers_best_trade_portfolio.json';
const fyersOptionsPortfolioUrl = '$_repoRawBase/reports/fyers_options_portfolio.json';

/// Added 06-Aug-2026 - one portfolio file per (strategy, index) pair
/// for the multi-strategy options engine (strategy/fyers_options_
/// engine.py / fyers_options_st4.py - simple_st1/st2/st3/st4 x
/// NIFTY/BANKNIFTY, 8 files total). `index` is lowercase ("nifty" /
/// "banknifty") matching the report filenames.
String fyersOptionsStrategyUrl(String strategy, String index) =>
    '$_repoRawBase/reports/fyers_options_${strategy}_${index}_portfolio.json';

/// Fetches and JSON-decodes a repo file, cache-busted with the current
/// time so a phone's HTTP cache never shows stale data. Returns null (not
/// an exception) for a 404 - some files (e.g. best_trade_portfolio.json)
/// legitimately don't exist yet until the first real trade happens.
Future<Map<String, dynamic>?> fetchJson(String url) async {
  final uri = Uri.parse('$url?t=${DateTime.now().millisecondsSinceEpoch}');
  final response = await http.get(uri).timeout(const Duration(seconds: 15));

  if (response.statusCode == 404) {
    return null;
  }

  if (response.statusCode != 200) {
    throw Exception('GitHub returned ${response.statusCode}');
  }

  return json.decode(response.body) as Map<String, dynamic>;
}
