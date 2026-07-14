import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

const portfolioUrl =
    'https://raw.githubusercontent.com/TuRaing/TURION_AI_Trader/main/reports/paper_portfolio.json';

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
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF1E1E2E),
        cardColor: const Color(0xFF313244),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF89B4FA),
          brightness: Brightness.dark,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF181825),
        ),
      ),
      home: const PortfolioScreen(),
    );
  }
}

class PortfolioScreen extends StatefulWidget {
  const PortfolioScreen({super.key});

  @override
  State<PortfolioScreen> createState() => _PortfolioScreenState();
}

class _PortfolioScreenState extends State<PortfolioScreen> {
  Map<String, dynamic>? _portfolio;
  bool _loading = true;
  String? _error;
  DateTime? _lastFetched;

  @override
  void initState() {
    super.initState();
    _fetchPortfolio();
  }

  Future<void> _fetchPortfolio() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final uri = Uri.parse(
          '$portfolioUrl?t=${DateTime.now().millisecondsSinceEpoch}');
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        setState(() {
          _portfolio = json.decode(response.body);
          _lastFetched = DateTime.now();
          _loading = false;
        });
      } else {
        setState(() {
          _error = 'GitHub returned ${response.statusCode}';
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Color _pnlColor(num pnl) =>
      pnl > 0 ? const Color(0xFFA6E3A1) : const Color(0xFFF38BA8);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('TURION AI Trader'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loading ? null : _fetchPortfolio,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchPortfolio,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading && _portfolio == null) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null && _portfolio == null) {
      return ListView(
        children: [
          const SizedBox(height: 100),
          Icon(Icons.error_outline, size: 48, color: Colors.red[300]),
          const SizedBox(height: 12),
          Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Text(
                'Could not load portfolio:\n$_error',
                textAlign: TextAlign.center,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Center(
            child: TextButton(
              onPressed: _fetchPortfolio,
              child: const Text('Retry'),
            ),
          ),
        ],
      );
    }

    final portfolio = _portfolio!;
    final cash = (portfolio['Cash'] as num).toDouble();
    final positions = Map<String, dynamic>.from(portfolio['Positions'] ?? {});
    final closedTrades = List<Map<String, dynamic>>.from(
        (portfolio['Closed Trades'] ?? []).map((t) => Map<String, dynamic>.from(t)));

    final totalPnl = closedTrades.fold<double>(
        0, (sum, t) => sum + (t['PnL'] as num).toDouble());

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (_lastFetched != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text(
              'Updated: ${_lastFetched!.toLocal().toString().substring(0, 19)}',
              style: TextStyle(color: Colors.grey[400], fontSize: 12),
            ),
          ),
        _SummaryCard(cash: cash, positions: positions.length, closed: closedTrades.length, totalPnl: totalPnl, pnlColor: _pnlColor(totalPnl)),
        const SizedBox(height: 16),
        Text('Open Positions (${positions.length})',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (positions.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text('No open positions'),
          )
        else
          ...positions.entries.map((e) => _PositionTile(symbol: e.key, position: e.value)),
        const SizedBox(height: 24),
        Text('Closed Trades (${closedTrades.length})',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (closedTrades.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text('No closed trades yet'),
          )
        else
          ...closedTrades.reversed.map((t) => _TradeTile(trade: t, pnlColor: _pnlColor((t['PnL'] as num)))),
      ],
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final double cash;
  final int positions;
  final int closed;
  final double totalPnl;
  final Color pnlColor;

  const _SummaryCard({
    required this.cash,
    required this.positions,
    required this.closed,
    required this.totalPnl,
    required this.pnlColor,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _row('Cash', cash.toStringAsFixed(2)),
            _row('Open Positions', '$positions'),
            _row('Closed Trades', '$closed'),
            _row('Total PnL', totalPnl.toStringAsFixed(2), valueColor: pnlColor),
          ],
        ),
      ),
    );
  }

  Widget _row(String label, String value, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: valueColor,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }
}

class _PositionTile extends StatelessWidget {
  final String symbol;
  final Map<String, dynamic> position;

  const _PositionTile({required this.symbol, required this.position});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text(symbol, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(
          'Entry ${(position['Entry Price'] as num).toStringAsFixed(2)}  '
          'SL ${(position['Stop Loss'] as num).toStringAsFixed(2)}  '
          'Target ${(position['Target'] as num).toStringAsFixed(2)}',
        ),
      ),
    );
  }
}

class _TradeTile extends StatelessWidget {
  final Map<String, dynamic> trade;
  final Color pnlColor;

  const _TradeTile({required this.trade, required this.pnlColor});

  @override
  Widget build(BuildContext context) {
    final symbol = trade['Symbol'] ?? 'NIFTY 50';
    final pnl = (trade['PnL'] as num).toDouble();

    return Card(
      child: ListTile(
        title: Text('$symbol  ${trade['Exit Reason']}'),
        subtitle: Text(
          'Entry ${(trade['Entry Price'] as num).toStringAsFixed(2)} -> '
          'Exit ${(trade['Exit Price'] as num).toStringAsFixed(2)}\n'
          '${trade['Exit Time']}',
        ),
        isThreeLine: true,
        trailing: Text(
          pnl.toStringAsFixed(2),
          style: TextStyle(color: pnlColor, fontWeight: FontWeight.bold, fontSize: 16),
        ),
      ),
    );
  }
}
