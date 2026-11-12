import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import '../../core/api.dart';
import 'road_map.dart';

/// The polling lifecycle belongs exclusively to this map, never to the shell.
class LiveRoadMap extends StatefulWidget {
  const LiveRoadMap({
    super.key,
    required this.api,
    required this.initialPositions,
    this.initialSimulation,
    required this.control,
    this.tileProvider,
  });
  final PersonnelApi api;
  final List<Map<String, dynamic>> initialPositions;
  final Map<String, dynamic>? initialSimulation;
  final Future<void> Function(String, int) control;
  final TileProvider? tileProvider;
  @override
  State<LiveRoadMap> createState() => _LiveRoadMapState();
}

class _LiveRoadMapState extends State<LiveRoadMap> {
  late List<Map<String, dynamic>> positions;
  Map<String, dynamic>? simulation;
  Timer? timer;
  bool fetching = false;
  String? error;
  DateTime? updated;
  @override
  void initState() {
    super.initState();
    positions = widget.initialPositions;
    simulation = widget.initialSimulation;
    timer = Timer.periodic(const Duration(seconds: 2), (_) => refresh());
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  Future<void> refresh() async {
    if (fetching) return;
    fetching = true;
    try {
      final result = await widget.api.request('/api/personnel/direction/map/');
      if (mounted) {
        setState(() {
          positions = List<Map<String, dynamic>>.from(
            result['positions'] ?? [],
          );
          simulation = result['simulation'] == null
              ? null
              : Map<String, dynamic>.from(result['simulation']);
          updated = DateTime.tryParse(result['updated_at'] ?? '')?.toLocal();
          error = null;
        });
      }
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      fetching = false;
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Row(
        children: [
          Expanded(
            child: Text(
              updated == null
                  ? 'Suivi cartographique · actualisation indépendante'
                  : 'Carte mise à jour à ${updated!.hour.toString().padLeft(2, '0')}:${updated!.minute.toString().padLeft(2, '0')}:${updated!.second.toString().padLeft(2, '0')}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
          IconButton(
            tooltip: 'Actualiser uniquement la carte',
            onPressed: refresh,
            icon: const Icon(Icons.refresh, size: 18),
          ),
        ],
      ),
      if (error != null)
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(
            'Carte : $error',
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        ),
      RoadMap(
        positions: positions,
        simulation: simulation,
        tileProvider: widget.tileProvider,
        control: (action, id) async {
          await widget.control(action, id);
          await refresh();
        },
      ),
    ],
  );
}
