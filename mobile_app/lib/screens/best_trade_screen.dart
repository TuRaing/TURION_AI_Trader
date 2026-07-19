import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/live_clock.dart';

class BestTradeScreen extends StatefulWidget {
  const BestTradeScreen({super.key});

  @override
  State<BestTradeScreen> createState() => _BestTradeScreenState();
}

class _BestTradeScreenState extends State<BestTradeScreen> {
  Map<String, dynamic>? _pick;
  Map<String, dynamic>? _position;
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
      final pick = await fetchJson(bestTradePickUrl);
      final positionData = await fetchJson(bestTradePortfolioUrl);

      setState(() {
        _pick = pick;
        _position = positionData?['Position'] as Map<String, dynamic>?;
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
            hasData: _pick != null || !_loading,
            onRetry: _fetch,
            child: RefreshIndicator(onRefresh: _fetch, child: _buildBody()),
          ),
        ),
      ],
    );
  }

  Widget _buildBody() {
    if (_pick == null) {
      return ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          SizedBox(height: 40),
          Center(child: Text('No shortlist scan yet today.', style: TextStyle(color: mutedColor))),
        ],
      );
    }

    final best = _pick!['Best Trade'] as Map<String, dynamic>?;
    final ranked = List<Map<String, dynamic>>.from(
        (_pick!['Ranked'] ?? []).map((r) => Map<String, dynamic>.from(r)));

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Locked for today', style: const TextStyle(fontSize: 13, color: mutedColor)),
        const SizedBox(height: 10),
        if (best == null)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
            child: Text(
              _pick!['Reason'] ?? 'No trade cleared today\'s bar.',
              style: const TextStyle(color: mutedColor),
            ),
          )
        else
          _BestPickCard(best: best, reason: _pick!['Reason'] as String? ?? ''),
        if (_position != null) ...[
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(8)),
            child: Row(
              children: [
                const Text('Paper position', style: TextStyle(fontSize: 12, color: mutedColor)),
                const Spacer(),
                Text(
                  'Entry ${formatRupees((_position!['Entry Price'] as num).toDouble())}',
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 20),
        Text('Shortlist', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
        const SizedBox(height: 8),
        if (ranked.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Text('Nothing ranked yet', style: TextStyle(color: mutedColor)),
          )
        else
          ...ranked.map((r) => _ShortlistRow(item: r)),
      ],
    );
  }
}

class _BestPickCard extends StatelessWidget {
  final Map<String, dynamic> best;
  final String reason;

  const _BestPickCard({required this.best, required this.reason});

  @override
  Widget build(BuildContext context) {
    final bias = best['Bias'] as String? ?? '';
    final isBullish = bias == 'Bullish';
    final color = isBullish ? successColor : dangerColor;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.track_changes, size: 18, color: color),
              const SizedBox(width: 8),
              Text('${best['Name']}', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500, color: color)),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(color: bgColor, borderRadius: BorderRadius.circular(6)),
                child: Text('${best['Type']}', style: TextStyle(fontSize: 11, color: color)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            '${best['Decision']} · confidence ${(best['Final Confidence'] ?? best['Confidence'])}%',
            style: TextStyle(fontSize: 13, color: color),
          ),
          const SizedBox(height: 4),
          Text(reason, style: TextStyle(fontSize: 12, color: color)),
        ],
      ),
    );
  }
}

class _ShortlistRow extends StatelessWidget {
  final Map<String, dynamic> item;

  const _ShortlistRow({required this.item});

  @override
  Widget build(BuildContext context) {
    final bias = item['Bias'] as String? ?? '';
    final color = bias == 'Bullish' ? successColor : (bias == 'Bearish' ? dangerColor : mutedColor);

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(color: bgColor, border: Border.all(color: Colors.white12, width: 0.5), borderRadius: BorderRadius.circular(8)),
      child: Row(
        children: [
          Expanded(
            child: Text('${item['Name']} · ${item['Type']}', style: const TextStyle(fontSize: 12)),
          ),
          Text(
            '${item['Decision']} · ${item['Final Confidence'] ?? item['Confidence']}%',
            style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}
