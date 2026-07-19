import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/live_clock.dart';

class WatchlistScreen extends StatefulWidget {
  const WatchlistScreen({super.key});

  @override
  State<WatchlistScreen> createState() => _WatchlistScreenState();
}

class _WatchlistScreenState extends State<WatchlistScreen> {
  Map<String, dynamic>? _shortlist;
  bool _loading = true;
  String? _error;
  DateTime? _lastFetched;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final data = await fetchJson(bestTradeShortlistUrl);
      setState(() {
        _shortlist = data;
        _lastFetched = DateTime.now();
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        LiveClockHeader(lastUpdated: _lastFetched),
        const DisclaimerBanner(),
        Expanded(
          child: LoadingErrorWrapper(
            loading: _loading,
            error: _error,
            hasData: _shortlist != null,
            onRetry: _fetch,
            child: RefreshIndicator(onRefresh: _fetch, child: _buildBody()),
          ),
        ),
      ],
    );
  }

  Widget _buildBody() {
    final stocks = List<Map<String, dynamic>>.from(
        (_shortlist?['Stocks'] ?? []).map((s) => Map<String, dynamic>.from(s)));

    final bullish = stocks.where((s) => s['Bias'] == 'Bullish').toList();
    final bearish = stocks.where((s) => s['Bias'] == 'Bearish').toList();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Today\'s shortlisted candidates (NIFTY 50, filtered to BUY/SELL)',
          style: TextStyle(fontSize: 12, color: mutedColor),
        ),
        const SizedBox(height: 16),
        Text('Bullish', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: successColor)),
        const SizedBox(height: 8),
        if (bullish.isEmpty)
          const Padding(padding: EdgeInsets.only(bottom: 12), child: Text('None today', style: TextStyle(color: mutedColor)))
        else
          ...bullish.map((s) => _WatchlistRow(stock: s)),
        const SizedBox(height: 16),
        Text('Bearish', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: dangerColor)),
        const SizedBox(height: 8),
        if (bearish.isEmpty)
          const Padding(padding: EdgeInsets.only(bottom: 12), child: Text('None today', style: TextStyle(color: mutedColor)))
        else
          ...bearish.map((s) => _WatchlistRow(stock: s)),
      ],
    );
  }
}

class _WatchlistRow extends StatelessWidget {
  final Map<String, dynamic> stock;

  const _WatchlistRow({required this.stock});

  @override
  Widget build(BuildContext context) {
    final bias = stock['Bias'] as String? ?? '';
    final color = bias == 'Bullish' ? successColor : dangerColor;

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(8)),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${stock['Name']}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                Text('${formatRupees((stock['Price'] as num).toDouble())} · ${stock['Candle Pattern']}',
                    style: const TextStyle(fontSize: 11, color: mutedColor)),
              ],
            ),
          ),
          Text('${stock['Decision']} · ${stock['Confidence']}%',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: color)),
        ],
      ),
    );
  }
}
