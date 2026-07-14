import 'package:flutter_test/flutter_test.dart';

import 'package:turion_ai_trader/main.dart';

void main() {
  testWidgets('App builds and shows title', (WidgetTester tester) async {
    await tester.pumpWidget(const TurionApp());

    expect(find.text('TURION AI Trader'), findsOneWidget);
  });
}
