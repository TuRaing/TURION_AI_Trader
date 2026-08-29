import 'package:flutter_test/flutter_test.dart';

import 'package:turion_crypto/main.dart';

void main() {
  testWidgets('App renders BTC and ETH tabs', (WidgetTester tester) async {
    await tester.pumpWidget(const TurionCryptoApp());
    await tester.pump();

    expect(find.text('TURION Crypto'), findsOneWidget);
    expect(find.text('BTC'), findsOneWidget);
    expect(find.text('ETH'), findsOneWidget);
  });
}
