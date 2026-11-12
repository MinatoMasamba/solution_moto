import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_mboka/core/api.dart';
import 'package:go_mboka/main.dart';
import 'package:go_mboka/features/direction/live_road_map.dart';
import 'package:go_mboka/theme/personnel_theme.dart';
import 'road_map_test.dart' show LocalTiles;

class CountingApi extends PersonnelApi {
  CountingApi() : super('http://test.invalid');
  final calls = <String, int>{};
  @override
  Future<Map<String, dynamic>> request(
    String path, {
    Map<String, dynamic>? body,
    String? method,
  }) async {
    calls.update(path, (v) => v + 1, ifAbsent: () => 1);
    if (path == '/api/personnel/profile/') {
      return {
        'name': 'Marie Kalonji',
        'first_name': 'Marie',
        'last_name': 'Kalonji',
        'post_nom': '',
        'email': 'marie@example.invalid',
        'phone_number': '+243000000000',
        'role': 'Opérateur',
        'is_active': true,
        'is_verified': true,
        'theme': 'light',
        'date_joined': '2026-01-01T00:00:00Z',
      };
    }
    if (path == '/api/personnel/direction/map/') {
      return {
        'positions': <Map<String, dynamic>>[],
        'simulation': null,
        'updated_at': '2026-11-12T10:00:00Z',
      };
    }
    return {
      'me': {'name': 'Marie Kalonji'},
      'positions': <Map<String, dynamic>>[],
      'simulation': null,
      'updated_at': '2026-11-12T10:00:00Z',
    };
  }
}

void main() {
  testWidgets('Profile edits survive time passing without global polling', (
    tester,
  ) async {
    final api = CountingApi();
    PersonnelTheme.apply('light');
    await tester.pumpWidget(PersonnelApp(api: api, initialPage: 8));
    await tester.pumpAndSettle();
    final before = Map<String, int>.from(api.calls);
    await tester.enterText(
      find.byType(TextFormField).first,
      'Saisie préservée',
    );
    await tester.pump(const Duration(seconds: 10));
    await tester.pump();
    expect(
      tester
          .widget<TextFormField>(find.byType(TextFormField).first)
          .controller!
          .text,
      'Saisie préservée',
    );
    expect(api.calls, before);
    expect(
      Theme.of(tester.element(find.byType(Scaffold).first)).brightness,
      Brightness.light,
    );
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'Only the map endpoint polls and polling stops when map is disposed',
    (tester) async {
      final api = CountingApi();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: LiveRoadMap(
                api: api,
                initialPositions: const [],
                control: (_, _) async {},
                tileProvider: LocalTiles(),
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      for (int i = 0; i < 2; i++) {
        await tester.pump(const Duration(seconds: 2));
        await tester.pump();
      }
      expect(api.calls.keys, contains('/api/personnel/direction/map/'));
      expect(api.calls.length, 1);
      expect(api.calls.values.single, 2);
      await tester.pumpWidget(const SizedBox());
      await tester.pump(const Duration(seconds: 6));
      expect(api.calls.values.single, 2);
      expect(tester.takeException(), isNull);
    },
  );
}
