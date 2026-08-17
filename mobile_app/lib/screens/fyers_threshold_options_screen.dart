import 'package:flutter/material.dart';

import 'fyers_multi_strategy_options_screen.dart';

// Added 08-Aug-2026 - a SEPARATE tab from Options, at the user's
// direct request: same 5 strategies (simple_st1/st2/st3/st4/gapfill),
// same entry/exit logic, but each with a daily profit-lock gate on -
// once a book's already-REALIZED profit for the day hits Rs 2,000+,
// it stops opening new trades for the rest of that day (an already-
// open position still runs to its own Target/Stop-Loss/Square-Off).
// See strategy/options_strategies.py's THRESHOLD group and fyers_
// options_engine.py's DAILY_PROFIT_LOCK_RS. Reuses FyersMultiStrategy
// OptionsScreen (made generic the same day) instead of duplicating
// the tab/list/portfolio-fetch UI - only the strategy names/
// descriptions/banner differ.
//
// TEST DATA ONLY - every price here is a real Fyers quote, but these
// are paper trades only, not live trading.

const _thresholdStrategyNames = [
  'simple_st1_threshold',
  'st2_threshold',
  'st3_threshold',
  'st4_threshold',
  'gapfill_threshold',
  'st3_threshold_slcap',
  'st2_threshold_slcap',
  // Added 17-Aug-2026 - hybrid SL + dynamic 2%-of-capital profit lock
  // (backtest-verified) and hybrid SL + minimum-2%-profit trailing
  // stop with unlimited upside (live-only, could not be backtested).
  // NIFTY-only.
  'st2_threshold_slcap2pctlock',
  'simple_st1_threshold_slcap2pctlock',
  'st2_threshold_trailing2pct',
  'simple_st1_threshold_trailing2pct',
];

const _thresholdStrategyDescriptions = {
  'simple_st1_threshold':
      'simple_st1 सारखंच (RSI दिशा, ATM, 3%/3%), पण आजचा profit ₹2,000+ झाला की नवीन trade बंद.',
  'st2_threshold': 'st2 सारखंच (RSI दिशा, ATM, 5%/2%), पण आजचा profit ₹2,000+ झाला की नवीन trade बंद.',
  'st3_threshold': 'st3 सारखंच (RSI दिशा, ATM, 5%/5%), पण आजचा profit ₹2,000+ झाला की नवीन trade बंद.',
  'st4_threshold':
      'st4 सारखंच (MTF+ADX, दिवसातून १ trade, trailing stop), पण आजचा profit ₹2,000+ झाला की नवीन trade बंद.',
  'gapfill_threshold':
      'gapfill सारखंच (gap-reversion, PE/CE), पण आजचा profit ₹2,000+ झाला की नवीन trade बंद.',
  'st3_threshold_slcap':
      'st3_threshold सारखंच, पण Stop-Loss आता hybrid cap (flat 2% वि. deployed-capital चा 2%, जे लहान ते).',
  'st2_threshold_slcap':
      'st2_threshold सारखंच, पण Stop-Loss hybrid cap (flat 2% वि. deployed-capital चा 2%, जे लहान ते).',
  'st2_threshold_slcap2pctlock':
      'st2_threshold_slcap सारखंच, पण profit-lock आता ₹2,000 fixed ऐवजी capital च्या 2% - फक्त NIFTY.',
  'simple_st1_threshold_slcap2pctlock':
      'simple_st1_threshold_slcap सारखंच, पण profit-lock आता ₹2,000 fixed ऐवजी capital च्या 2% - फक्त NIFTY.',
  'st2_threshold_trailing2pct':
      'st2_threshold सारखंच (hybrid SL सह), पण fixed Target नाही - profit +2% झाल्यावर trailing सुरू, वरची मर्यादा नाही - फक्त NIFTY.',
  'simple_st1_threshold_trailing2pct':
      'simple_st1_threshold सारखंच (hybrid SL सह), पण fixed Target नाही - profit +2% झाल्यावर trailing सुरू, वरची मर्यादा नाही - फक्त NIFTY.',
};

class FyersThresholdOptionsScreen extends StatelessWidget {
  const FyersThresholdOptionsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const FyersMultiStrategyOptionsScreen(
      strategyNames: _thresholdStrategyNames,
      strategyDescriptions: _thresholdStrategyDescriptions,
      bannerText:
          'Options tab सारख्याच strategies (+ 6 नवीन hybrid-SL-cap variants), पण रोजचा profit ₹2,000+ (किंवा 2 _slcap2pctlock books साठी capital च्या 2%) झाला की त्या दिवसासाठी नवीन trade बंद - नफा लॉक करण्यासाठी. 2 _trailing2pct books ला त्याऐवजी fixed Target नाही.',
    );
  }
}
