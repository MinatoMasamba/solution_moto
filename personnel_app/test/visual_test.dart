// Opt-in live acceptance: flutter test test/visual_test.dart --dart-define=LIVE_DG=true
import 'dart:io';
import 'dart:ui' as ui;
import 'package:http/http.dart' as http;
import 'package:flutter/services.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_mboka/main.dart';
import 'package:go_mboka/core/api.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  WidgetController.hitTestWarningShouldBeFatal = true;
  Future<void> settle(WidgetTester tester) async {
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 600));
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 1500)),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
  }

  const live = bool.fromEnvironment('LIVE_DG');
  late PersonnelApi api;
  setUpAll(() async {
    if (!live) return;
    HttpOverrides.global = null;
    // Only the platform cache directory is adapted; HTTP, tiles and DG data are real.
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/path_provider'),
          (call) async => '/tmp/go-mboka-map-test-cache',
        );
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
      final originalError = FlutterError.onError;
      var tileFailures = 0;
      FlutterError.onError = (details) {
        if (details.library == 'image resource service' &&
            details.exception is http.ClientException) {
          tileFailures++;
          debugPrint(
            'External tile request failed in widget engine; native map QA is separate.',
          );
        } else {
          originalError?.call(details);
        }
      };
      addTearDown(() => FlutterError.onError = originalError);
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
      await settle(tester);
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
        "Mon profil",
      ]) {
        if (!desktop) {
          await tester.tap(find.byIcon(Icons.menu));
          await settle(tester);
        }
        final nav = find.widgetWithText(ListTile, label);
        await tester.ensureVisible(nav);
        await tester.tap(nav);
        await settle(tester);
        expect(tester.takeException(), isNull);
        expect(find.byType(MaterialBanner), findsNothing);
        expect(
          find
              .text(label)
              .evaluate()
              .any(
                (element) =>
                    element.findAncestorWidgetOfExactType<ListTile>() == null,
              ),
          isTrue,
          reason: 'Header must reflect actual navigation',
        );
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
            "Mon profil",
          ].indexOf(label);
          await File(
            'verification/live/dg-${size.width.toInt()}-$index.png',
          ).writeAsBytes(bytes!.buffer.asUint8List());
          image.dispose();
        });
      }
      if (tileFailures > 0) {
        debugPrint(
          'Tile failures: $tileFailures. No basemap success is inferred from this widget test.',
        );
      }
      await tester.pumpWidget(const SizedBox());
    }, skip: !live);
  }
}
