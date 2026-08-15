import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import 'theme.dart';
import 'screens/portfolio_screen.dart';
import 'screens/best_trade_screen.dart';
import 'screens/watchlist_screen.dart';
import 'screens/news_screen.dart';
import 'screens/history_screen.dart';
import 'screens/fyers_portfolio_screen.dart';
import 'screens/fyers_multi_strategy_options_screen.dart';
import 'screens/fyers_threshold_options_screen.dart';
import 'screens/fyers_options_summary_screen.dart';
import 'screens/fyers_options_grouped_screen.dart';

// Topic-based push - every install subscribes to the same topic, so the
// backend (report/push_notifier.py) never needs to track individual device
// tokens. Trade alerts still go to Telegram too (see report/notifier.py) -
// this is an additional channel, not a replacement.
const _tradeAlertsTopic = 'trade_alerts';

Future<void> _setupPushNotifications() async {
  await Firebase.initializeApp();

  final messaging = FirebaseMessaging.instance;
  await messaging.requestPermission();
  await messaging.subscribeToTopic(_tradeAlertsTopic);
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    await _setupPushNotifications();
  } catch (e) {
    // Missing/misconfigured google-services.json shouldn't block the app -
    // it just means push notifications won't arrive, same graceful-
    // degradation philosophy as the rest of the project.
    debugPrint('Push notification setup skipped: $e');
  }

  runApp(const TurionApp());
}

class TurionApp extends StatelessWidget {
  const TurionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TURION AI Trader',
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

class _HomeShellState extends State<HomeShell> {
  int _index = 0;

  static const _screens = [
    PortfolioScreen(),
    BestTradeScreen(),
    WatchlistScreen(),
    NewsScreen(),
    HistoryScreen(),
    FyersPortfolioScreen(),
    FyersMultiStrategyOptionsScreen(),
    FyersThresholdOptionsScreen(),
    FyersOptionsSummaryScreen(),
    FyersOptionsGroupedScreen(),
  ];

  static const _titles = [
    'Turion AI trader',
    'Best Trade (Intraday)',
    'Watchlist (Swing)',
    'News',
    'History',
    'Fyers (Test)',
    'Options (Test)',
    'Threshold Options (Test)',
    'Options Summary (Test)',
    'Options Grouped (Test)',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_titles[_index])),
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _index,
        onTap: (i) => setState(() => _index = i),
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.account_balance_wallet_outlined), label: 'yfinance'),
          BottomNavigationBarItem(icon: Icon(Icons.track_changes_outlined), label: 'Intraday'),
          BottomNavigationBarItem(icon: Icon(Icons.list_alt_outlined), label: 'Swing'),
          BottomNavigationBarItem(icon: Icon(Icons.newspaper_outlined), label: 'News'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: 'History'),
          BottomNavigationBarItem(icon: Icon(Icons.bolt_outlined), label: 'Fyers'),
          BottomNavigationBarItem(icon: Icon(Icons.candlestick_chart_outlined), label: 'Options'),
          BottomNavigationBarItem(icon: Icon(Icons.lock_clock_outlined), label: 'Threshold'),
          BottomNavigationBarItem(icon: Icon(Icons.table_chart_outlined), label: 'Summary'),
          BottomNavigationBarItem(icon: Icon(Icons.dashboard_customize_outlined), label: 'Grouped'),
        ],
      ),
    );
  }
}
