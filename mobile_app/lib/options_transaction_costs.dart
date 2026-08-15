// Added 14-Aug-2026 - Dart mirror of strategy/options_transaction_
// costs.py, for the in-app per-trade cost breakdown (Options trade-
// detail view). The backend's Closed Trades records only store the
// final Net PnL (already cost-adjusted), not an itemized breakdown -
// rather than change every strategy module's _close_position() to
// additionally persist a breakdown (touching ~10 "working modules",
// against this repo's own rule), the SAME well-defined, already-
// documented formula is replicated here and computed client-side from
// fields every trade record already has (Entry/Exit Premium, Lots) +
// the index's known lot size (NIFTY 75 / BANKNIFTY 30, same as
// strategy/fyers_options_engine.py's INDEX_CONFIG). Historical trades
// work too, since nothing new needs to have been recorded for them.

const brokeragePerOrder = 20.0; // flat per executed order (buy, sell)
const sttSellPct = 0.1 / 100; // options SELL side, on premium turnover
const exchangeTxnPct = 0.03503 / 100; // NSE F&O, on premium turnover
const stampDutyBuyPct = 0.003 / 100; // options BUY side, on premium turnover
const sebiChargesPct = 10 / 1e7; // Rs 10 per crore of premium turnover
const gstPct = 18 / 100; // on brokerage + exchange + SEBI charges

const lotSizeByIndex = {'NIFTY': 75, 'BANKNIFTY': 30};

/// Itemized round-trip transaction cost, mirroring calculate_options_
/// round_trip_cost() exactly. `entryPremium`/`exitPremium` are per-unit
/// premiums, `quantity` is lots x lot_size (total units).
class OptionsCostBreakdown {
  final double brokerage;
  final double stt;
  final double exchangeCharges;
  final double stampDuty;
  final double sebiCharges;
  final double gst;

  const OptionsCostBreakdown({
    required this.brokerage,
    required this.stt,
    required this.exchangeCharges,
    required this.stampDuty,
    required this.sebiCharges,
    required this.gst,
  });

  double get total => brokerage + stt + exchangeCharges + stampDuty + sebiCharges + gst;

  factory OptionsCostBreakdown.compute({
    required double entryPremium,
    required double exitPremium,
    required int quantity,
  }) {
    final buyValue = entryPremium * quantity;
    final sellValue = exitPremium * quantity;

    final brokerage = brokeragePerOrder * 2;
    final stt = sellValue * sttSellPct;
    final exchangeCharges = (buyValue + sellValue) * exchangeTxnPct;
    final stampDuty = buyValue * stampDutyBuyPct;
    final sebiCharges = (buyValue + sellValue) * sebiChargesPct;
    final gst = (brokerage + exchangeCharges + sebiCharges) * gstPct;

    return OptionsCostBreakdown(
      brokerage: brokerage,
      stt: stt,
      exchangeCharges: exchangeCharges,
      stampDuty: stampDuty,
      sebiCharges: sebiCharges,
      gst: gst,
    );
  }
}
