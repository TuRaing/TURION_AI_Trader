import 'package:flutter/material.dart';

import 'theme.dart';
import 'screens/portfolio_screen.dart';
import 'screens/best_trade_screen.dart';
import 'screens/watchlist_screen.dart';
import 'screens/news_screen.dart';
import 'screens/history_screen.dart';

void main() {
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
  ];

  static const _titles = ['Turion AI trader', 'Best trade', 'Watchlist', 'News', 'History'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_titles[_index])),
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _index,
        onTap: (i) => setState(() => _index = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.account_balance_wallet_outlined), label: 'Portfolio'),
          BottomNavigationBarItem(icon: Icon(Icons.track_changes_outlined), label: 'Best trade'),
          BottomNavigationBarItem(icon: Icon(Icons.list_alt_outlined), label: 'Watchlist'),
          BottomNavigationBarItem(icon: Icon(Icons.newspaper_outlined), label: 'News'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: 'History'),
        ],
      ),
    );
  }
}
