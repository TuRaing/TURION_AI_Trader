import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/live_clock.dart';

class NewsScreen extends StatefulWidget {
  const NewsScreen({super.key});

  @override
  State<NewsScreen> createState() => _NewsScreenState();
}

class _NewsScreenState extends State<NewsScreen> {
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
    final headlines = List<Map<String, dynamic>>.from(
        (_shortlist?['Market Headlines'] ?? []).map((h) => Map<String, dynamic>.from(h)));

    if (headlines.isEmpty) {
      return ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          SizedBox(height: 40),
          Center(child: Text('No headlines fetched yet.', style: TextStyle(color: mutedColor))),
        ],
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: headlines.map((h) => _HeadlineRow(headline: h)).toList(),
    );
  }
}

class _HeadlineRow extends StatelessWidget {
  final Map<String, dynamic> headline;

  const _HeadlineRow({required this.headline});

  @override
  Widget build(BuildContext context) {
    final sentiment = headline['Sentiment'] as String? ?? 'Neutral';
    final color = sentiment == 'Bullish' ? successColor : (sentiment == 'Bearish' ? dangerColor : mutedColor);

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 1),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(color: color.withValues(alpha: 0.18), borderRadius: BorderRadius.circular(6)),
            child: Text(sentiment, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w500, color: color)),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text('${headline['Headline']}', style: const TextStyle(fontSize: 13, height: 1.3)),
          ),
        ],
      ),
    );
  }
}
