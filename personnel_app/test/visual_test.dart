// Opt-in live acceptance: flutter test test/visual_test.dart --dart-define=LIVE_DG=true
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/services.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_mboka/main.dart';
import 'package:go_mboka/core/api.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const live = bool.fromEnvironment('LIVE_DG');
  late PersonnelApi api;
  setUpAll(() async {
    if (!live) return;
    HttpOverrides.global = null;
    final secret = File(
      '../.local/personnel-recette.txt',
    ).readAsStringSync().split('Mot de passe : ')[1].split('\n')[0];
    api = PersonnelApi('http://127.0.0.1:8000');
    await api.login('+243000900001', secret);
    await (FontLoader(
      'Inter',
    )..addFont(rootBundle.load('assets/Inter.ttf'))).load();
    await (FontLoader(
      'MaterialIcons',
    )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
  });
  for (final size in [const Size(1440, 1000), const Size(412, 915)]) {
    testWidgets('Live DG server tabs $size', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final key = GlobalKey();
      await tester.runAsync(() async {
        await tester.pumpWidget(
          RepaintBoundary(
            key: key,
            child: PersonnelApp(api: api),
          ),
        );
        await Future<void>.delayed(const Duration(seconds: 2));
      });
      await tester.pumpAndSettle();
      expect(find.text('Connexion requise'), findsNothing);
      expect(tester.takeException(), isNull);
      final desktop = size.width >= 1000;
      for (final label in [
        "Vue d'ensemble",
        "Carte temps réel",
        "Motards",
        "Clients",
        "Gérants",
        "Commissions",
        "Notifications",
        "Support",
        "Réglages",
      ]) {
        if (!desktop) {
          await tester.tap(find.byIcon(Icons.menu));
          await tester.pumpAndSettle();
        }
        final nav = find.widgetWithText(ListTile, label);
        await tester.ensureVisible(nav);
        await tester.tap(nav);
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        await tester.runAsync(() async {
          final boundary =
              key.currentContext!.findRenderObject() as RenderRepaintBoundary;
          final image = await boundary.toImage();
          final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
          await Directory('verification/live').create(recursive: true);
          final index = [
            "Vue d'ensemble",
            "Carte temps réel",
            "Motards",
            "Clients",
            "Gérants",
            "Commissions",
            "Notifications",
            "Support",
            "Réglages",
          ].indexOf(label);
          await File(
            'verification/live/dg-${size.width.toInt()}-$index.png',
          ).writeAsBytes(bytes!.buffer.asUint8List());
          image.dispose();
        });
      }
      await tester.pumpWidget(const SizedBox());
    }, skip: !live);
  }
}
