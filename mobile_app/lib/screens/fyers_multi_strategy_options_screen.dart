import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/live_clock.dart';
import 'chart_screen.dart';
import 'fyers_login_screen.dart';

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

const _strategyNames = ['simple_st1', 'st2', 'st3', 'st4', 'gapfill', 'vix_filter', 'oi_footprint', 'credit_spread', 'pcr_momentum', 'max_pain_drift'];

// Added 06-Aug-2026 - one-line plain-language summary per strategy,
// shown under its index tabs so it's clear what each is actually
// doing without needing to read the backend code.
const _strategyDescriptions = {
  'simple_st1': 'RSI दिशा (CE/PE), ATM strike, समान 3% Target / 3% Stop-Loss.',
  'st2': 'RSI दिशा, ATM strike, 5% Target / 2% Stop-Loss (backtest मध्ये सर्वोत्तम ठरलेला ratio).',
  'st3': 'RSI दिशा, ATM strike, 5% Target / 5% Stop-Loss.',
  'st4': 'दिवसातून फक्त १ high-confidence trade - 15m/5m/1m alignment + ADX>25 झाल्यावरच entry, ₹1,000 नफ्यानंतर ATR-आधारित trailing stop.',
  'gapfill': 'सकाळचा gap मागे prev close कडे परत येईल या अंदाजावर - gap up वर PE, gap down वर CE, फक्त सकाळी 10 वाजेपर्यंत entry.',
  'vix_filter': 'RSI>60/<40 + India VIX त्याच्याच 30-70 percentile band मध्ये असेल तरच entry (फक्त BANKNIFTY - 22-Jul च्या research मध्ये validated).',
  'oi_footprint': 'ATM strike वरचा Open Interest बदल (institutional footprint) बघून CE/PE - छोटा, पटकन ₹1,500 Target/Stop-Loss.',
  'credit_spread': 'Premium विकतो (theta) - VIX high असतानाच, RSI दिशेने Bull Put/Bear Call spread (defined-risk, 2 legs). 50% credit वर बाहेर, 2x वर Stop-Loss.',
  'pcr_momentum': 'संपूर्ण option chain चा Put-Call OI Ratio किती वेगाने बदलतोय (+ volume confirmation) यावरून CE/PE.',
  'max_pain_drift': 'Max Pain strike (जिथे option विक्रेत्यांचं सर्वात कमी नुकसान) कुठल्या दिशेने सरकतोय त्यावरून CE/PE - फक्त expiry च्या 2 दिवस आधीच entry.',
};

// Added 08-Aug-2026 - vix_filter is BANKNIFTY-only (NIFTY was already
// tested and rejected for that exact combo - see strategy/fyers_
// options_vix_filter.py) - unlike every other strategy here, which
// runs both indices. Default (any name not listed) is both.
const _strategyIndices = {
  'vix_filter': ['banknifty'],
};

List<String> _indicesFor(String strategyName) => _strategyIndices[strategyName] ?? ['nifty', 'banknifty'];

// Made generic 08-Aug-2026 - the user asked for a SECOND tab
// ("Threshold Options") showing the same 5 strategies but with a
// daily profit-lock gate on (see strategy/options_strategies.py's
// THRESHOLD group), without touching the originals. Rather than
// duplicate this whole tab/list/portfolio-fetch UI, the widget now
// takes its strategy names/descriptions/banner text as constructor
// params (defaulting to the original 5) - fyers_threshold_options_
// screen.dart just instantiates this with the threshold group's
// names instead.
class FyersMultiStrategyOptionsScreen extends StatefulWidget {
  final List<String> strategyNames;
  final Map<String, String> strategyDescriptions;
  final String bannerText;

  const FyersMultiStrategyOptionsScreen({
    super.key,
    this.strategyNames = _strategyNames,
    this.strategyDescriptions = _strategyDescriptions,
    this.bannerText =
        '7 strategies, each with its own ₹1,00,000 (vix_filter is BANKNIFTY-only) - real live premium quotes, paper trades only.',
  });

  @override
  State<FyersMultiStrategyOptionsScreen> createState() => _FyersMultiStrategyOptionsScreenState();
}

class _FyersMultiStrategyOptionsScreenState extends State<FyersMultiStrategyOptionsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _strategyTabController;

  @override
  void initState() {
    super.initState();
    _strategyTabController = TabController(length: widget.strategyNames.length, vsync: this);
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
          child: Text(
            widget.bannerText,
            style: const TextStyle(fontSize: 12, color: accentColor),
          ),
        ),
        // Added 07-Aug-2026 - the login button was only ever on the
        // "Fyers" tab; the one shared FYERS_ACCESS_TOKEN it produces
        // already covers every Fyers workflow including these
        // strategies, but not having a visible login entry point HERE
        // was confusing (user asked "where do I log in for Options?").
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Align(alignment: Alignment.centerLeft, child: FyersLoginButton()),
        ),
        TabBar(
          controller: _strategyTabController,
          isScrollable: true,
          labelColor: accentColor,
          unselectedLabelColor: mutedColor,
          tabs: widget.strategyNames.map((s) => Tab(text: s)).toList(),
        ),
        Expanded(
          child: TabBarView(
            controller: _strategyTabController,
            children: widget.strategyNames
                .map((s) => _IndexTabs(strategyName: s, description: widget.strategyDescriptions[s] ?? ''))
                .toList(),
          ),
        ),
      ],
    );
  }
}

class _IndexTabs extends StatefulWidget {
  final String strategyName;
  final String description;

  const _IndexTabs({required this.strategyName, required this.description});

  @override
  State<_IndexTabs> createState() => _IndexTabsState();
}

class _IndexTabsState extends State<_IndexTabs> with SingleTickerProviderStateMixin {
  late final TabController _indexTabController;
  late final List<String> _indices;

  @override
  void initState() {
    super.initState();
    _indices = _indicesFor(widget.strategyName);
    _indexTabController = TabController(length: _indices.length, vsync: this);
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
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: Text(
            widget.description,
            style: const TextStyle(fontSize: 12, color: mutedColor),
          ),
        ),
        const SizedBox(height: 4),
        TabBar(
          controller: _indexTabController,
          labelColor: successColor,
          unselectedLabelColor: mutedColor,
          tabs: _indices.map((i) => Tab(text: i.toUpperCase())).toList(),
        ),
        Expanded(
          child: TabBarView(
            controller: _indexTabController,
            // Own State per (strategy, index) tab, so switching tabs
            // doesn't lose each one's independently-fetched data.
            children: _indices
                .map((i) => _StrategyIndexPortfolio(
                      key: ValueKey('${widget.strategyName}_$i'),
                      strategyName: widget.strategyName,
                      index: i,
                      label: i.toUpperCase(),
                    ))
                .toList(),
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
