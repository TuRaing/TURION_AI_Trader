import 'package:flutter/material.dart';

import '../event_driven_realtime_service.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/disclaimer_banner.dart';
import 'fyers_login_screen.dart';
import 'live_chart_screen.dart';
import 'strategy_premium_chart_screen.dart';

// Added 20-Aug-2026 - the VPS's own event-driven paper-trading books
// (strategy/event_driven_runner.py's STRATEGY_NAMES), separated into
// their own tab per the user's own explicit ask.
//
// REDESIGNED same day, THIRD pass - user's own explicit correction:
// NOT the Summary/Passbook two-tab pattern (fyers_options_summary_
// screen.dart) - that was the wrong reference. The right one is
// fyers_multi_strategy_options_screen.dart's layout: one top-level tab
// PER STRATEGY, each tab showing everything directly (login button,
// PnL, Cash/Win rate, Closed count, Position, Closed Trades) in one
// scroll - no separate aggregate table, no dropdown-based passbook.
// Matches EXACTLY what every other strategy tab in this app already
// looks like, per the user's own screenshots of the Threshold Options
// tab.

// Book cfg constants below mirror strategy/event_driven_engine.py's own
// cfg builders EXACTLY (make_st2_threshold_event_cfg/make_simple_st1_
// threshold_event_cfg/make_oi_footprint_event_cfg) - added 21-Aug-2026
// alongside StrategyPremiumChartScreen, which needs them to compute
// Target/Stop-Loss premium lines. Static, not fetched - these values
// only ever change via a backend redeploy, which needs an app rebuild
// anyway to add/relabel a book at all (same as label/underlying below,
// already hardcoded per book before this).
// `description` - added 22-Aug-2026, at the user's own explicit ask -
// one-line Marathi summary of what each book actually does, shown at
// the top of its own tab (_BookPortfolio.build() below). Kept here,
// not fetched, same "static, mirrors the Python cfg" reasoning as
// every other field on this record.
const _books = [
  (key: 'st2_threshold_eventdriven', label: 'ST2 Threshold', underlying: 'NIFTY',
    lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 5.0, stopLossPct: 2.0, targetRupees: null, stopLossRupees: null,
    description: 'RSI वरून CE/PE निवडतो · Target 5% / Stop-Loss 2% · 2 सलग तोट्यानंतर आजसाठी थांबतो'),
  (key: 'simple_st1_threshold_eventdriven', label: 'Simple ST1 Threshold', underlying: 'NIFTY',
    lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 3.0, stopLossPct: 3.0, targetRupees: null, stopLossRupees: null,
    description: 'RSI वरून CE/PE निवडतो · Target 3% / Stop-Loss 3% · 2 सलग तोट्यानंतर आजसाठी थांबतो'),
  (key: 'oi_footprint_eventdriven_nifty', label: 'OI Footprint', underlying: 'NIFTY',
    lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: null, stopLossPct: null, targetRupees: 1500.0, stopLossRupees: 1500.0,
    description: 'Open Interest मधल्या बदलावरून buildup ओळखतो · Target/Stop-Loss ₹1,500 (fixed)'),
  (key: 'oi_footprint_eventdriven_banknifty', label: 'OI Footprint', underlying: 'BANKNIFTY',
    lotSize: 30, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: null, stopLossPct: null, targetRupees: 1500.0, stopLossRupees: 1500.0,
    description: 'Open Interest मधल्या बदलावरून buildup ओळखतो · Target/Stop-Loss ₹1,500 (fixed)'),
  // Added 21-Aug-2026 - the two new daily-profit-lock variant books
  // (strategy/event_driven_runner.py's STRATEGY_NAMES, same day) -
  // separate books running alongside the plain ones above, not a
  // replacement of them. Same target/SL cfg as their un-locked
  // siblings - only daily_profit_lock differs, which doesn't affect
  // a single trade's own Target/SL premium.
  (key: 'st2_threshold_lock_eventdriven', label: 'ST2 Threshold (2% Lock)', underlying: 'NIFTY',
    lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 5.0, stopLossPct: 2.0, targetRupees: null, stopLossRupees: null,
    description: 'ST2 Threshold सारखंच · दिवसाचा एकूण नफा 2% गाठला की आजसाठी नवीन trade बंद'),
  (key: 'simple_st1_threshold_lock_eventdriven', label: 'Simple ST1 Threshold (2% Lock)', underlying: 'NIFTY',
    lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 3.0, stopLossPct: 3.0, targetRupees: null, stopLossRupees: null,
    description: 'Simple ST1 Threshold सारखंच · दिवसाचा एकूण नफा 2% गाठला की आजसाठी नवीन trade बंद'),
  // Added 21-Aug-2026, same day - 6 more variants (2 per daily-profit-
  // lock tier: 2%/1%/0.5%) of the two "_lock" books above, running
  // rsi_momentum_quote_decide_fn instead of rsi_momentum_decide_fn
  // (strategy/event_driven_engine.py) - Target/Stop-Loss trigger off
  // real bid/ask, not LTP. Same target/SL cfg as their un-locked
  // siblings (only decide_fn and daily_profit_lock_pct differ, neither
  // of which changes a single trade's own Target/SL premium line).
  (key: 'st2_threshold_lock_quote2pct_eventdriven', label: 'ST2 Threshold (2% Lock, Quote)', underlying: 'NIFTY',
    lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 5.0, stopLossPct: 2.0, targetRupees: null, stopLossRupees: null,
    description: '2% Lock सारखंच, पण Target/Stop-Loss खऱ्या bid/ask किमतीवर ठरतो (LTP नाही) - जास्त वास्तववादी PnL'),
  (key: 'simple_st1_threshold_lock_quote2pct_eventdriven', label: 'Simple ST1 Threshold (2% Lock, Quote)',
    underlying: 'NIFTY', lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 3.0, stopLossPct: 3.0, targetRupees: null, stopLossRupees: null,
    description: '2% Lock सारखंच, पण Target/Stop-Loss खऱ्या bid/ask किमतीवर ठरतो (LTP नाही) - जास्त वास्तववादी PnL'),
  (key: 'st2_threshold_lock_quote1pct_eventdriven', label: 'ST2 Threshold (1% Lock, Quote)', underlying: 'NIFTY',
    lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 5.0, stopLossPct: 2.0, targetRupees: null, stopLossRupees: null,
    description: 'bid/ask-based Target/Stop-Loss · दिवसाचा नफा 1% गाठला की आजसाठी नवीन trade बंद'),
  (key: 'simple_st1_threshold_lock_quote1pct_eventdriven', label: 'Simple ST1 Threshold (1% Lock, Quote)',
    underlying: 'NIFTY', lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 3.0, stopLossPct: 3.0, targetRupees: null, stopLossRupees: null,
    description: 'bid/ask-based Target/Stop-Loss · दिवसाचा नफा 1% गाठला की आजसाठी नवीन trade बंद'),
  (key: 'st2_threshold_lock_quote0pt5pct_eventdriven', label: 'ST2 Threshold (0.5% Lock, Quote)',
    underlying: 'NIFTY', lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 5.0, stopLossPct: 2.0, targetRupees: null, stopLossRupees: null,
    description: 'bid/ask-based Target/Stop-Loss · दिवसाचा नफा 0.5% गाठला की आजसाठी नवीन trade बंद (सर्वात लवकर थांबणारा)'),
  (key: 'simple_st1_threshold_lock_quote0pt5pct_eventdriven', label: 'Simple ST1 Threshold (0.5% Lock, Quote)',
    underlying: 'NIFTY', lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: 3.0, stopLossPct: 3.0, targetRupees: null, stopLossRupees: null,
    description: 'bid/ask-based Target/Stop-Loss · दिवसाचा नफा 0.5% गाठला की आजसाठी नवीन trade बंद (सर्वात लवकर थांबणारा)'),
  // Added 24-Aug-2026 - quote-based (bid/ask, not LTP) siblings of the
  // two plain oi_footprint books above - see strategy/event_driven_
  // runner.py's STRATEGY_NAMES own matching note. Real depth-slippage
  // analysis today found oi_footprint_nifty's LTP-based recorded PnL
  // overstates realistic PnL badly enough that individual trades' sign
  // even flips - same target/SL cfg as the plain books, only decide_fn
  // differs.
  (key: 'oi_footprint_quote_eventdriven_nifty', label: 'OI Footprint (Quote)', underlying: 'NIFTY',
    lotSize: 75, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: null, stopLossPct: null, targetRupees: 1500.0, stopLossRupees: 1500.0,
    description: 'OI Footprint सारखंच, पण Target/Stop-Loss खऱ्या bid/ask किमतीवर ठरतो (LTP नाही) - जास्त वास्तववादी PnL'),
  (key: 'oi_footprint_quote_eventdriven_banknifty', label: 'OI Footprint (Quote)', underlying: 'BANKNIFTY',
    lotSize: 30, initialCapital: 100000.0, hybridSlCapPct: 2.0,
    targetNetPct: null, stopLossPct: null, targetRupees: 1500.0, stopLossRupees: 1500.0,
    description: 'OI Footprint सारखंच, पण Target/Stop-Loss खऱ्या bid/ask किमतीवर ठरतो (LTP नाही) - जास्त वास्तववादी PnL'),
];

class VpsScreen extends StatefulWidget {
  const VpsScreen({super.key});

  @override
  State<VpsScreen> createState() => _VpsScreenState();
}

class _VpsScreenState extends State<VpsScreen> with SingleTickerProviderStateMixin {
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
    return Column(
      children: [
        const DisclaimerBanner(),
        Container(
          width: double.infinity,
          margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: accent2Color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
          child: const Text(
            'VPS - event-driven (WebSocket, tick-by-tick) engine, each with its own ₹1,00,000 - real live premium quotes, paper trades only.',
            style: TextStyle(fontSize: 12, color: accent2Color),
          ),
        ),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Align(alignment: Alignment.centerLeft, child: FyersLoginButton()),
        ),
        TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: accent2Color,
          unselectedLabelColor: mutedColor,
          tabs: _books.map((b) => Tab(text: '${b.label} · ${b.underlying}')).toList(),
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: _books.map((b) => _BookPortfolio(book: b)).toList(),
          ),
        ),
      ],
    );
  }
}

class _BookPortfolio extends StatelessWidget {
  final ({
    String key, String label, String underlying,
    int lotSize, double initialCapital, double hybridSlCapPct,
    double? targetNetPct, double? stopLossPct, double? targetRupees, double? stopLossRupees,
    String description,
  }) book;

  const _BookPortfolio({required this.book});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<Map<String, dynamic>?>(
      stream: watchEventDrivenPortfolio(book.key),
      builder: (context, snapshot) {
        // Same fallback every other strategy screen in this app already
        // uses (fetchJson(...) ?? {...}) - show the FULL structure with
        // starting-capital defaults rather than hiding it behind a
        // "no data yet" message. The VPS hasn't traded yet today (or
        // ever, until B18's first real live run), which is a real,
        // expected, temporary state - not a reason to hide the layout.
        final portfolio = snapshot.data ?? {'Cash': 100000, 'Position': null, 'Closed Trades': []};

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
            // Added 22-Aug-2026, at the user's own explicit ask - a
            // small one-line Marathi summary of what THIS book actually
            // does, right under its own tab, so it doesn't take a code
            // read (or a chat with Claude) to remember which of the 12
            // books does what.
            Text(book.description, style: const TextStyle(fontSize: 12, color: mutedColor)),
            const SizedBox(height: 12),
            HeroStat(label: '${book.underlying} Total Net PnL', value: formatSignedRupees(totalPnl), color: pnlColor(totalPnl)),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(child: StatPill(label: 'Cash', value: formatRupees(cash))),
                const SizedBox(width: 10),
                Expanded(
                    child: StatPill(
                        label: 'Win rate', value: winRate == null ? '—' : '${winRate.toStringAsFixed(0)}%')),
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
                  Text('${book.underlying} Position',
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
                      underlyingLabel: book.underlying,
                      // Added 21-Aug-2026 - the option's own live
                      // PREMIUM chart with Entry/Target/Stop-Loss
                      // overlaid (see strategy_premium_chart_screen.
                      // dart's own module comment for why this is
                      // premium, not spot).
                      onViewChart: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                              builder: (_) => StrategyPremiumChartScreen(
                                    strategyKey: book.key,
                                    strategyLabel: book.label,
                                    position: position,
                                    lotSize: book.lotSize,
                                    initialCapital: book.initialCapital,
                                    hybridSlCapPct: book.hybridSlCapPct,
                                    targetNetPct: book.targetNetPct,
                                    stopLossPct: book.stopLossPct,
                                    targetRupees: book.targetRupees,
                                    stopLossRupees: book.stopLossRupees,
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
                    underlyingLabel: book.underlying,
                    onViewChart: () => Navigator.push(
                        context, MaterialPageRoute(builder: (_) => LiveChartScreen(index: book.underlying))),
                  )),
          ],
        );
      },
    );
  }
}
