import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_mboka/main.dart';
import 'package:go_mboka/core/api.dart';
import 'package:go_mboka/theme/personnel_theme.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const live = bool.fromEnvironment('LIVE_DG');
  late PersonnelApi api;
  setUpAll(() async {
    if (!live) return;
    HttpOverrides.global = null;
    final password = File(
      '../.local/personnel-recette.txt',
    ).readAsStringSync().split('Mot de passe : ')[1].split('\n')[0];
    api = PersonnelApi(const String.fromEnvironment('LIVE_API_URL',defaultValue:'http://127.0.0.1:8000'));
    await api.login('+243000900001', password);
    await (FontLoader(
      'Inter',
    )..addFont(rootBundle.load('assets/Inter.ttf'))).load();
    await (FontLoader(
      'MaterialIcons',
    )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
  });
  for (final width in [1440, 412]) {
    testWidgets('Live profile light/dark $width', (tester) async {
      tester.view.physicalSize = Size(width.toDouble(), 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final key = GlobalKey();
      await tester.runAsync(() async {
        await tester.pumpWidget(
          RepaintBoundary(
            key: key,
            child: PersonnelApp(api: api, initialPage: 8),
          ),
        );
        await Future<void>.delayed(const Duration(milliseconds: 500));
      });
      for (int i = 0; i < 3; i++) {
        await tester.pump();
        await tester.runAsync(
          () => Future<void>.delayed(const Duration(milliseconds: 500)),
        );
      }
      expect(find.byType(TextFormField), findsNWidgets(5));
      for (final mode in ['light', 'dark']) {
        PersonnelTheme.apply(mode);
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        await tester.runAsync(() async {
          final image =
              await (key.currentContext!.findRenderObject()
                      as RenderRepaintBoundary)
                  .toImage();
          final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
          await Directory('verification/live').create(recursive: true);
          await File(
            'verification/live/profile-$width-$mode.png',
          ).writeAsBytes(bytes!.buffer.asUint8List());
          image.dispose();
        });
        await tester.ensureVisible(find.text('Enregistrer le profil'));
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        await tester.runAsync(() async {
          final image =
              await (key.currentContext!.findRenderObject()
                      as RenderRepaintBoundary)
                  .toImage();
          final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
          await File(
            'verification/live/profile-$width-$mode-bottom.png',
          ).writeAsBytes(bytes!.buffer.asUint8List());
          image.dispose();
        });
        await tester.drag(
          find.byType(SingleChildScrollView).first,
          const Offset(0, 3000),
        );
        await tester.pumpAndSettle();
      }
      await tester.pumpWidget(const SizedBox());
    }, skip: !live);
  }
}
