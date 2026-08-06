import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/live_clock.dart';
import 'chart_screen.dart';

// Added 06-Aug-2026 - shows the 4 named options strategies (simple_
// st1, st2, st3, st4 - strategy/fyers_options_engine.py / fyers_
// options_st4.py) x 2 indices (NIFTY, BANKNIFTY) = 8 independent
// paper portfolios, one strategy-tab x index-subtab per config. The
// ORIGINAL single live strategy (strategy/fyers_options_paper_
// trading.py, fyers_options_screen.dart) is untouched and keeps
// running its own automation - it's just not one of these 4 tabs
// (simple_st1 is its retuned successor, not a replacement of the
// file itself).
//
// TEST DATA ONLY - every price here is a real Fyers quote, but these
// are paper trades only, not live trading.

const _strategyNames = ['simple_st1', 'st2', 'st3', 'st4'];

class FyersMultiStrategyOptionsScreen extends StatefulWidget {
  const FyersMultiStrategyOptionsScreen({super.key});

  @override
  State<FyersMultiStrategyOptionsScreen> createState() => _FyersMultiStrategyOptionsScreenState();
}

class _FyersMultiStrategyOptionsScreenState extends State<FyersMultiStrategyOptionsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _strategyTabController;

  @override
  void initState() {
    super.initState();
    _strategyTabController = TabController(length: _strategyNames.length, vsync: this);
  }

  @override
  void dispose() {
    _strategyTabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const LiveClockHeader(),
        const DisclaimerBanner(),
        Container(
          width: double.infinity,
          margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: accentColor.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
          child: const Text(
            '4 strategies, each on NIFTY + BANKNIFTY with its own ₹1,00,000 - real live premium quotes, paper trades only.',
            style: TextStyle(fontSize: 12, color: accentColor),
          ),
        ),
        TabBar(
          controller: _strategyTabController,
          isScrollable: true,
          labelColor: accentColor,
          unselectedLabelColor: mutedColor,
          tabs: _strategyNames.map((s) => Tab(text: s)).toList(),
        ),
        Expanded(
          child: TabBarView(
            controller: _strategyTabController,
            children: _strategyNames.map((s) => _IndexTabs(strategyName: s)).toList(),
          ),
        ),
      ],
    );
  }
}

class _IndexTabs extends StatefulWidget {
  final String strategyName;

  const _IndexTabs({required this.strategyName});

  @override
  State<_IndexTabs> createState() => _IndexTabsState();
}

class _IndexTabsState extends State<_IndexTabs> with SingleTickerProviderStateMixin {
  late final TabController _indexTabController;

  @override
  void initState() {
    super.initState();
    _indexTabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _indexTabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        TabBar(
          controller: _indexTabController,
          labelColor: successColor,
          unselectedLabelColor: mutedColor,
          tabs: const [Tab(text: 'NIFTY'), Tab(text: 'BANKNIFTY')],
        ),
        Expanded(
          child: TabBarView(
            controller: _indexTabController,
            // Own State per (strategy, index) tab, so switching tabs
            // doesn't lose each one's independently-fetched data.
            children: [
              _StrategyIndexPortfolio(
                key: ValueKey('${widget.strategyName}_nifty'),
                strategyName: widget.strategyName,
                index: 'nifty',
                label: 'NIFTY',
              ),
              _StrategyIndexPortfolio(
                key: ValueKey('${widget.strategyName}_banknifty'),
                strategyName: widget.strategyName,
                index: 'banknifty',
                label: 'BANKNIFTY',
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _StrategyIndexPortfolio extends StatefulWidget {
  final String strategyName;
  final String index; // 'nifty' / 'banknifty' - matches the report filename
  final String label; // 'NIFTY' / 'BANKNIFTY' - for display

  const _StrategyIndexPortfolio({
    super.key,
    required this.strategyName,
    required this.index,
    required this.label,
  });

  @override
  State<_StrategyIndexPortfolio> createState() => _StrategyIndexPortfolioState();
}

class _StrategyIndexPortfolioState extends State<_StrategyIndexPortfolio> {
  Map<String, dynamic>? _portfolio;
  bool _loading = true;
  String? _error;

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
      final result = await fetchJson(fyersOptionsStrategyUrl(widget.strategyName, widget.index));
      setState(() {
        _portfolio = result ?? {'Cash': 100000, 'Position': null, 'Closed Trades': []};
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
    return LoadingErrorWrapper(
      loading: _loading,
      error: _error,
      hasData: _portfolio != null,
      onRetry: _fetch,
      child: _portfolio == null
          ? const SizedBox.shrink()
          : RefreshIndicator(onRefresh: _fetch, child: _buildBody()),
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
        HeroStat(
          label: '${widget.label} Total Net PnL',
          value: formatSignedRupees(totalPnl),
          color: pnlColor(totalPnl),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: StatPill(label: 'Cash', value: formatRupees(cash))),
            const SizedBox(width: 10),
            Expanded(
              child: StatPill(
                label: 'Win rate',
                value: winRate == null ? '—' : '${winRate.toStringAsFixed(0)}%',
              ),
            ),
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
              Text('${widget.label} Position',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: accentColor)),
              const SizedBox(height: 8),
              if (position == null)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('No open option position', style: TextStyle(color: mutedColor)),
                )
              else
                OptionPositionCard(
                  position: position,
                  underlyingLabel: widget.label,
                  onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => ChartScreen(
                                symbol: widget.label,
                                candleDataUrl: fyersCandlesUrl,
                                // Charts the UNDERLYING's spot price, not the
                                // option premium (different scale, and Fyers
                                // has no reliable per-contract candle history
                                // anyway) - Entry Spot is what the entry
                                // decision was actually based on.
                                entryPrice: (position['Entry Spot'] as num?)?.toDouble(),
                                direction: position['Option Type'] == 'PE' ? 'SELL' : 'BUY',
                              ))),
                ),
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
          ...closedTrades.reversed.map((t) => OptionClosedTradeCard(
                trade: t,
                underlyingLabel: widget.label,
                onViewChart: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) => ChartScreen(
                              symbol: widget.label,
                              candleDataUrl: fyersCandlesUrl,
                              entryPrice: (t['Entry Spot'] as num?)?.toDouble(),
                              direction: t['Option Type'] == 'PE' ? 'SELL' : 'BUY',
                            ))),
              )),
      ],
    );
  }
}
