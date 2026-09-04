import 'dart:async';

import 'package:flutter/material.dart';

import 'api.dart';
import 'screens/premium_chart_screen.dart';
import 'theme.dart';
import 'widgets/candlestick_chart.dart';
import 'widgets/common.dart';
import 'widgets/disclaimer_banner.dart';
import 'widgets/mesh_background.dart';

// Standalone companion app to TURION AI Trader, per the user's
// explicit 29-Aug-2026 ask - "same app style, but only this one
// trade" - showing just the crypto RSI-momentum paper-trading books
// (BTC + ETH, strategy/event_driven_engine.py's rsi_momentum_decide_fn
// run against real Deribit data by run_crypto_options_engine.py on
// the standalone crypto VM - see doc/CRYPTO_PROJECT_STATUS.md), none
// of the ~60 NIFTY/BankNifty books the main app also shows. Same dark
// neon theme/mesh background as the main app (copied, not shared -
// this is a genuinely separate Flutter project/APK), but its own
// lean widget set (api.dart/widgets/common.dart) so USD formatting
// never runs through the main app's Rupee-specific helpers.

const _books = [
  (key: 'rsi_momentum_crypto_btc', label: 'BTC', initialCapital: 10000.0),
  (key: 'rsi_momentum_crypto_eth', label: 'ETH', initialCapital: 1047.89),
  // Added 30-Aug-2026 - the two new profit-lock books (see
  // run_crypto_options_engine.py's own CRYPTO_PROFIT_LOCK_PCT note) -
  // separate books/tabs alongside the originals above, not a
  // replacement, per the user's own explicit "old strategy चालू राहू
  // द्या" ask.
  (key: 'rsi_momentum_crypto_btc_profitlock', label: 'BTC (Profit Lock)', initialCapital: 10000.0),
  (key: 'rsi_momentum_crypto_eth_profitlock', label: 'ETH (Profit Lock)', initialCapital: 1047.89),
  // Added 31-Aug-2026 - the two new RSI-70/30-threshold books (see
  // run_crypto_options_engine.py's own CRYPTO_RSI_CE_THRESHOLD note) -
  // same "separate books, old ones untouched" rule as the profit-lock
  // pair above.
  (key: 'rsi_momentum_crypto_btc_rsi70', label: 'BTC (RSI 70/30)', initialCapital: 10000.0),
  (key: 'rsi_momentum_crypto_eth_rsi70', label: 'ETH (RSI 70/30)', initialCapital: 1047.89),
  // Added 01-Sep-2026 - RSI-70/30 + daily_loss_lock, BTC only (ETH
  // didn't show the same backtest benefit - see run_crypto_options_
  // engine.py's own CRYPTO_DAILY_LOSS_LOCK note).
  (key: 'rsi_momentum_crypto_btc_rsi70_lock', label: 'BTC (RSI 70/30 + Lock)', initialCapital: 10000.0),
];

// Matches strategy/event_driven_engine.py's make_st2_threshold_event_
// cfg() defaults - both crypto books use these unchanged (see
// run_crypto_options_engine.py's build_runner(), no override passed) -
// needed here only to draw the Target/Stop-Loss reference lines on the
// live position's own chart, same formula as StrategyPremiumChartScreen
// in the main app.
const _targetNetPct = 5.0;
const _hybridSlCapPct = 2.0;

void main() {
  runApp(const TurionCryptoApp());
}

class TurionCryptoApp extends StatelessWidget {
  const TurionCryptoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TURION Crypto',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: const HomeShell(),
    );
  }
}

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _books.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('TURION Crypto'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: _books.map((b) => Tab(text: b.label)).toList(),
        ),
      ),
      body: MeshBackground(
        child: Column(
          children: [
            const DisclaimerBanner(),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: _books.map((b) => _CryptoBookTab(book: b)).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CryptoBookTab extends StatefulWidget {
  final ({String key, String label, double initialCapital}) book;

  const _CryptoBookTab({required this.book});

  @override
  State<_CryptoBookTab> createState() => _CryptoBookTabState();
}

class _CryptoBookTabState extends State<_CryptoBookTab> {
  Map<String, dynamic>? _portfolio;
  bool _loading = true;
  String? _error;
  DateTime? _lastFetched;
  Timer? _autoRefresh;

  @override
  void initState() {
    super.initState();
    _fetch();
    // Auto-refresh, not a live Firebase Stream - see api.dart's own
    // module comment for why this app uses plain REST polling instead
    // of the main app's firebase_database SDK. 8s comfortably beats a
    // human noticing a stale screen without hammering the free RTDB
    // read quota.
    _autoRefresh = Timer.periodic(const Duration(seconds: 8), (_) => _fetch());
  }

  @override
  void dispose() {
    _autoRefresh?.cancel();
    super.dispose();
  }

  Future<void> _fetch() async {
    if (!_loading) setState(() => _loading = true);

    try {
      final result = await fetchPortfolio(widget.book.key);
      if (!mounted) return;
      setState(() {
        _portfolio = result ?? {'Cash': widget.book.initialCapital, 'Position': null, 'Closed Trades': []};
        _lastFetched = DateTime.now();
        _loading = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return LoadingErrorWrapper(
      loading: _loading,
      error: _error,
      hasData: _portfolio != null,
      onRetry: _fetch,
      child: _portfolio == null ? const SizedBox.shrink() : RefreshIndicator(onRefresh: _fetch, child: _buildBody()),
    );
  }

  Widget _buildBody() {
    final portfolio = _portfolio!;
    final cash = (portfolio['Cash'] as num).toDouble();
    final position = portfolio['Position'] as Map<String, dynamic>?;
    final closedTrades = List<Map<String, dynamic>>.from(
        (portfolio['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));

    final totalPnl = closedTrades.fold<double>(0, (sum, t) => sum + (t['Net PnL'] as num).toDouble());
    final wins = closedTrades.where((t) => (t['Net PnL'] as num) > 0).length;
    final winRate = closedTrades.isEmpty ? null : (wins / closedTrades.length * 100);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (_lastFetched != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text('Updated ${TimeOfDay.fromDateTime(_lastFetched!).format(context)}',
                style: const TextStyle(fontSize: 11, color: mutedColor)),
          ),
        HeroStat(label: '${widget.book.label} Total Net PnL', value: formatSignedUsd(totalPnl), color: pnlColor(totalPnl)),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: StatPill(label: 'Cash', value: formatUsd(cash))),
            const SizedBox(width: 10),
            Expanded(
                child: StatPill(label: 'Win rate', value: winRate == null ? '—' : '${winRate.toStringAsFixed(0)}%')),
          ],
        ),
        const SizedBox(height: 10),
        StatPill(label: 'Closed trades', value: '${closedTrades.length}'),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: surfaceColor, borderRadius: BorderRadius.circular(12)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${widget.book.label} Position',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: accentColor)),
              const SizedBox(height: 8),
              if (position == null)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('No open position', style: TextStyle(color: mutedColor)),
                )
              else
                CryptoPositionCard(position: position, onViewChart: () => _openPositionChart(context, position)),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text('Closed Trades (${closedTrades.length})',
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: mutedColor)),
        const SizedBox(height: 8),
        if (closedTrades.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text('No closed trades yet', style: TextStyle(color: mutedColor)),
          )
        else
          ...closedTrades.reversed.map(
            (t) => CryptoClosedTradeCard(trade: t, onViewChart: () => _openClosedTradeChart(context, t)),
          ),
      ],
    );
  }

  void _openPositionChart(BuildContext context, Map<String, dynamic> position) {
    final entryPremium = (position['Entry Premium'] as num).toDouble();
    final lots = (position['Lots'] as num).toInt();
    final capitalDeployed = (position['Capital Deployed'] as num).toDouble();
    final leg = position['Option Type'] == 'PE' ? 'PE' : 'CE';

    final targetPremium = entryPremium + (_targetNetPct / 100 * widget.book.initialCapital) / lots;
    final flatCap = widget.book.initialCapital * _hybridSlCapPct / 100;
    final pctCap = capitalDeployed * _hybridSlCapPct / 100;
    final hybridCap = flatCap < pctCap ? flatCap : pctCap;
    final slPremium = entryPremium - hybridCap / lots;

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => PremiumChartScreen(
          strategyKey: widget.book.key,
          bookLabel: widget.book.label,
          leg: leg,
          symbol: position['Symbol'] as String? ?? '',
          referenceLines: [
            ChartReferenceLine(price: entryPremium, label: 'Entry', color: accentColor),
            ChartReferenceLine(price: targetPremium, label: 'Target', color: successColor),
            ChartReferenceLine(price: slPremium, label: 'SL', color: dangerColor),
          ],
        ),
      ),
    );
  }

  void _openClosedTradeChart(BuildContext context, Map<String, dynamic> trade) {
    final entryPremium = (trade['Entry Premium'] as num).toDouble();
    final exitPremium = (trade['Exit Premium'] as num).toDouble();
    final leg = trade['Option Type'] == 'PE' ? 'PE' : 'CE';

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => PremiumChartScreen(
          strategyKey: widget.book.key,
          bookLabel: widget.book.label,
          leg: leg,
          symbol: trade['Symbol'] as String? ?? '',
          referenceLines: [
            ChartReferenceLine(price: entryPremium, label: 'Entry', color: accentColor),
            ChartReferenceLine(
                price: exitPremium, label: 'Exit', color: exitPremium >= entryPremium ? successColor : dangerColor),
          ],
        ),
      ),
    );
  }
}
