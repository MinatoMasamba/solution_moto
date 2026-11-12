import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_mboka/features/direction/road_map.dart';

// Isolate marker selection from external tiles; native tile loading is verified separately.
class LocalTiles extends TileProvider {
  @override
  ImageProvider getImage(
    TileCoordinates coordinates,
    TileLayer options,
  ) => MemoryImage(
    base64Decode(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l1sAAAAASUVORK5CYII=',
    ),
  );
}

void main() {
  testWidgets(
    'Selecting a motorcycle isolates its route and reset restores all',
    (tester) async {
      final sim = {
        'id': 1,
        'status': 'paused',
        'elapsed': 10,
        'vehicles': [
          for (int i = 1; i <= 2; i++)
            {
              'id': i,
              'name': 'SIM-$i',
              'latitude': -4.35,
              'longitude': 15.32 + i * .02,
              'phase': 'approche',
              'speed_kmh': 24,
              'route': 'Route $i',
            },
        ],
        'clients': [
          for (int i = 1; i <= 2; i++)
            {
              'id': i,
              'name': 'Client $i',
              'latitude': -4.36,
              'longitude': 15.32 + i * .02,
              'phase': 'attente_moto',
            },
        ],
        'routes': [
          for (int i = 1; i <= 2; i++)
            {
              'id': i,
              'label': 'Route $i',
              'approach': [
                [15.34, -4.35],
                [15.36, -4.36],
              ],
              'trip': [
                [15.36, -4.36],
                [15.37, -4.37],
              ],
            },
        ],
        'trails': [],
      };
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: RoadMap(
                positions: const [],
                simulation: sim,
                control: (_, _) async {},
                tileProvider: LocalTiles(),
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      expect(
        tester.widget<MarkerLayer>(find.byType(MarkerLayer)).markers.length,
        6,
      );
      expect(
        tester
            .widgetList<PolylineLayer>(find.byType(PolylineLayer))
            .first
            .polylines
            .length,
        4,
      );
      await tester.tap(find.byKey(const ValueKey('sim-moto-1')));
      await tester.pump();
      expect(find.byKey(const ValueKey('sim-moto-2')), findsNothing);
      expect(
        tester.widget<MarkerLayer>(find.byType(MarkerLayer)).markers.length,
        3,
      );
      expect(
        tester
            .widgetList<PolylineLayer>(find.byType(PolylineLayer))
            .first
            .polylines
            .length,
        2,
      );
      await tester.tap(find.text('Afficher toutes les motos'));
      await tester.pump();
      expect(find.byKey(const ValueKey('sim-moto-2')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
