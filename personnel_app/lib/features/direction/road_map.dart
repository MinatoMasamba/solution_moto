import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

/// All moving coordinates and road geometries come from Django.
class RoadMap extends StatefulWidget {
  const RoadMap({
    super.key,
    required this.positions,
    required this.simulation,
    required this.control,
    this.tileProvider,
  });
  final TileProvider? tileProvider;
  final List<Map<String, dynamic>> positions;
  final Map<String, dynamic>? simulation;
  final Future<void> Function(String, int) control;
  @override
  State<RoadMap> createState() => _RoadMapState();
}

class _RoadMapState extends State<RoadMap> {
  bool showSimulation = true;
  bool tileError = false;
  int? selected;
  int? selectedGps;
  List<Map<String, dynamic>> visibleRows(String key) => selectedGps != null
      ? []
      : rows(
          key,
        ).where((row) => selected == null || row['id'] == selected).toList();
  void selectMoto(int id) => setState(() {
    selected = id;
    selectedGps = null;
  });
  void resetSelection() => setState(() {
    selected = null;
    selectedGps = null;
  });
  List<Map<String, dynamic>> rows(String key) =>
      List<Map<String, dynamic>>.from(widget.simulation?[key] ?? []);
  LatLng point(Map<String, dynamic> p) => LatLng(
    (p['latitude'] as num).toDouble(),
    (p['longitude'] as num).toDouble(),
  );
  List<LatLng> line(dynamic geometry) => [
    for (final p in geometry)
      LatLng((p[1] as num).toDouble(), (p[0] as num).toDouble()),
  ];
  String phase(dynamic value) =>
      {
        'approche': 'Approche du client',
        'attente_moto': 'Client en attente',
        'prise_en_charge': 'Prise en charge · arrêt',
        'en_course': 'En course',
        'embouteillage': 'Embouteillage simulé',
        'arret': 'Arrêt simulé',
        'arrivee': 'Arrivée',
      }[value] ??
      '$value';
  @override
  Widget build(BuildContext context) {
    final sim = widget.simulation;
    final vehicles = showSimulation
        ? visibleRows('vehicles')
        : <Map<String, dynamic>>[];
    final routes = showSimulation
        ? visibleRows('routes')
        : <Map<String, dynamic>>[];
    return Material(
      type: MaterialType.transparency,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Wrap(
            spacing: 12,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              const Text(
                'Carte routière · Kinshasa',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
              if (sim != null)
                FilterChip(
                  label: Text('SIMULATION · ${sim['status']}'),
                  selected: showSimulation,
                  onSelected: (v) => setState(() {
                    showSimulation = v;
                    selected = null;
                    selectedGps = null;
                  }),
                ),
              if (selected != null || selectedGps != null)
                TextButton.icon(
                  onPressed: resetSelection,
                  icon: const Icon(Icons.filter_alt_off, size: 16),
                  label: const Text('Afficher toutes les motos'),
                ),
              const Text(
                '● GPS enregistré   🏍 Moto   ● Client',
                style: TextStyle(fontSize: 11),
              ),
            ],
          ),
          if (tileError)
            const Padding(
              padding: EdgeInsets.all(8),
              child: Text(
                'Fond de carte indisponible : vérifier la connexion au fournisseur de tuiles.',
                style: TextStyle(color: Colors.orange),
              ),
            ),
          const SizedBox(height: 12),
          SizedBox(
            height: 420,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: FlutterMap(
                options: const MapOptions(
                  initialCenter: LatLng(-4.355, 15.345),
                  initialZoom: 12,
                  minZoom: 9,
                  maxZoom: 18,
                ),
                children: [
                  TileLayer(
                    tileProvider: widget.tileProvider,
                    urlTemplate: const String.fromEnvironment(
                      'MAP_TILE_URL',
                      defaultValue:
                          'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    ),
                    userAgentPackageName: 'org.gomboka.personnel',
                    errorTileCallback: (tile, error, stack) {
                      if (!tileError && mounted) {
                        WidgetsBinding.instance.addPostFrameCallback((_) {
                          if (mounted) setState(() => tileError = true);
                        });
                      }
                    },
                  ),
                  PolylineLayer(
                    polylines: [
                      for (final r in routes) ...[
                        Polyline(
                          points: line(r['approach']),
                          strokeWidth: selected == r['id'] ? 5 : 2,
                          color: Colors.blueAccent.withValues(alpha: .7),
                        ),
                        Polyline(
                          points: line(r['trip']),
                          strokeWidth: selected == r['id'] ? 6 : 3,
                          color: Colors.deepPurpleAccent.withValues(alpha: .75),
                        ),
                      ],
                    ],
                  ),
                  if (showSimulation)
                    PolylineLayer(
                      polylines: [
                        for (final trail in visibleRows('trails'))
                          if ((trail['coordinates'] as List).length > 1)
                            Polyline(
                              points: line(trail['coordinates']),
                              strokeWidth: 4,
                              color: Colors.green,
                            ),
                      ],
                    ),
                  if (selectedGps != null)
                    PolylineLayer(
                      polylines: [
                        for (final p in widget.positions.where(
                          (p) => p['user_id'] == selectedGps,
                        ))
                          if ((p['trajectory'] as List? ?? []).length > 1)
                            Polyline(
                              points: line(p['trajectory']),
                              strokeWidth: 3,
                              color: Colors.green,
                            ),
                      ],
                    ),
                  MarkerLayer(
                    markers: [
                      for (final p in widget.positions.where(
                        (p) =>
                            selected == null &&
                            (selectedGps == null ||
                                p['user_id'] == selectedGps),
                      ))
                        Marker(
                          point: point(p),
                          width: 26,
                          height: 26,
                          child: Tooltip(
                            message:
                                'GPS enregistré · ${p['name']}\n${p['recorded_at']}',
                            child: GestureDetector(
                              key: ValueKey('gps-moto-${p['user_id']}'),
                              onTap: () => setState(() {
                                selectedGps = p['user_id'] as int;
                                selected = null;
                              }),
                              child: const Icon(
                                Icons.two_wheeler,
                                color: Colors.green,
                                size: 20,
                              ),
                            ),
                          ),
                        ),
                      for (final r in routes)
                        Marker(
                          point: line(r['trip']).last,
                          width: 28,
                          height: 28,
                          child: Tooltip(
                            message: 'Arrivée · ${r['label']}',
                            child: const Icon(
                              Icons.flag,
                              color: Colors.black,
                              size: 17,
                            ),
                          ),
                        ),
                      if (showSimulation)
                        for (final p in visibleRows('clients'))
                          Marker(
                            point: point(p),
                            width: 22,
                            height: 34,
                            alignment: Alignment.topCenter,
                            child: Tooltip(
                              message:
                                  'SIMULATION · ${p['name']} · ${phase(p['phase'])}',
                              child: const Align(
                                alignment: Alignment.topCenter,
                                child: Icon(
                                  Icons.person_pin_circle,
                                  color: Colors.blue,
                                  size: 20,
                                ),
                              ),
                            ),
                          ),
                      for (final p in vehicles)
                        Marker(
                          point: point(p),
                          width: 26,
                          height: 24,
                          child: Tooltip(
                            message:
                                'SIMULATION · ${p['name']}\n${phase(p['phase'])} · ${p['speed_kmh']} km/h',
                            child: InkWell(
                              key: ValueKey('sim-moto-${p['id']}'),
                              onTap: () => selectMoto(p['id'] as int),
                              child: Container(
                                decoration: BoxDecoration(
                                  color: p['phase'] == 'embouteillage'
                                      ? Colors.orange
                                      : Colors.deepPurple,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color: Colors.white,
                                    width: 1.3,
                                  ),
                                ),
                                child: const Icon(
                                  Icons.two_wheeler,
                                  color: Colors.white,
                                  size: 17,
                                ),
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SimpleAttributionWidget(
                    source: Text(
                      '© OpenStreetMap contributors · ODbL',
                      style: TextStyle(fontSize: 10, color: Colors.white),
                    ),
                    alignment: Alignment.bottomRight,
                  ),
                ],
              ),
            ),
          ),
          if (sim != null && showSimulation) ...[
            const SizedBox(height: 8),
            Text(
              'SIMULATION SERVEUR #${sim['id']} · ${(sim['elapsed'] as num).toStringAsFixed(0)} s simulées · OSRM / OSM · trafic synthétique',
              style: const TextStyle(fontSize: 11, color: Colors.orange),
            ),
            Wrap(
              spacing: 8,
              children: [
                TextButton.icon(
                  onPressed: sim['status'] == 'completed'
                      ? null
                      : () => widget.control(
                          sim['status'] == 'running'
                              ? 'simulation_pause'
                              : 'simulation_resume',
                          sim['id'] as int,
                        ),
                  icon: Icon(
                    sim['status'] == 'running' ? Icons.pause : Icons.play_arrow,
                  ),
                  label: Text(
                    sim['status'] == 'running'
                        ? 'Pause'
                        : 'Reprendre (worker serveur)',
                  ),
                ),
                TextButton(
                  onPressed: sim['status'] == 'completed'
                      ? null
                      : () =>
                            widget.control('simulation_step', sim['id'] as int),
                  child: const Text('Avancer de 10 s'),
                ),
              ],
            ),
            for (final v in vehicles)
              ListTile(
                dense: true,
                onTap: () => selectMoto(v['id'] as int),
                leading: Icon(
                  v['phase'] == 'embouteillage'
                      ? Icons.traffic
                      : Icons.two_wheeler,
                  color: v['phase'] == 'embouteillage'
                      ? Colors.orange
                      : Colors.deepPurpleAccent,
                ),
                title: Text(
                  '${v['name']} · ${v['route']}',
                  style: const TextStyle(fontSize: 12),
                ),
                subtitle: Text(
                  '${phase(v['phase'])} · ${v['speed_kmh']} km/h',
                  style: const TextStyle(fontSize: 11),
                ),
              ),
          ],
        ],
      ),
    );
  }
}
