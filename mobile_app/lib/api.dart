import 'dart:convert';
import 'package:http/http.dart' as http;

const _repoRawBase =
    'https://raw.githubusercontent.com/TuRaing/TURION_AI_Trader/main';

const portfolioUrl = '$_repoRawBase/reports/paper_portfolio.json';
const bestTradeShortlistUrl = '$_repoRawBase/reports/best_trade_shortlist.json';
const bestTradePortfolioUrl = '$_repoRawBase/reports/best_trade_portfolio.json';
const bestTradePickUrl = '$_repoRawBase/reports/best_trade_pick.json';

/// Fetches and JSON-decodes a repo file, cache-busted with the current
/// time so a phone's HTTP cache never shows stale data. Returns null (not
/// an exception) for a 404 - some files (e.g. best_trade_portfolio.json)
/// legitimately don't exist yet until the first real trade happens.
Future<Map<String, dynamic>?> fetchJson(String url) async {
  final uri = Uri.parse('$url?t=${DateTime.now().millisecondsSinceEpoch}');
  final response = await http.get(uri);

  if (response.statusCode == 404) {
    return null;
  }

  if (response.statusCode != 200) {
    throw Exception('GitHub returned ${response.statusCode}');
  }

  return json.decode(response.body) as Map<String, dynamic>;
}
