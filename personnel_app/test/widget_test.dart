import 'package:flutter_test/flutter_test.dart';
import 'package:go_mboka/main.dart';

void main() {
  testWidgets('DG dashboard renders on phone without overflow', (tester) async {
    await tester.pumpWidget(const PersonnelApp());
    await tester.pumpAndSettle();
    expect(find.text('Connectez-vous au serveur GO-MBOKA'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
