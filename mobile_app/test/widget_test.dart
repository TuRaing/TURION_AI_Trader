import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:turion_ai_trader/theme.dart';
import 'package:turion_ai_trader/widgets/common.dart';
import 'package:turion_ai_trader/widgets/disclaimer_banner.dart';

// These test the pure/stateless widgets in isolation, with no network
// involved - the screens themselves fetch from GitHub in initState(),
// which the Flutter test HTTP client always 400s, making a full-app
// smoke test unreliable without a mocked HttpClient. Not worth the
// setup for what's otherwise covered by `flutter analyze` (no compile
// errors) and manual on-device testing.

void main() {
  testWidgets('StatPill shows its label and value', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(body: StatPill(label: 'Cash', value: '1,00,000')),
    ));

    expect(find.text('Cash'), findsOneWidget);
    expect(find.text('1,00,000'), findsOneWidget);
  });

  testWidgets('HeroStat shows its label and value', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(body: HeroStat(label: 'Total pnl', value: '+240', color: successColor)),
    ));

    expect(find.text('Total pnl'), findsOneWidget);
    expect(find.text('+240'), findsOneWidget);
  });

  testWidgets('DisclaimerBanner shows the paper-trading notice', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: DisclaimerBanner())));

    expect(find.textContaining('Paper trading only'), findsOneWidget);
  });

  test('formatRupees formats with Indian grouping', () {
    expect(formatRupees(100240), '1,00,240');
  });

  test('formatSignedRupees prefixes a plus sign for non-negative values', () {
    expect(formatSignedRupees(240), '+240');
    expect(formatSignedRupees(-95), '-95');
  });

  test('formatBackendTimestamp falls back to the raw string on bad input', () {
    expect(formatBackendTimestamp('not-a-date'), 'not-a-date');
    expect(formatBackendTimestamp(null), '');
  });
}
