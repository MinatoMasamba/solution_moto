// Local acceptance helper. Reads ignored credentials; never embeds a password.
import 'dart:io';
import 'dart:async';
import 'dart:ui' as ui;
import 'package:flutter/rendering.dart';
import 'package:flutter/material.dart';
import 'package:go_mboka/main.dart';
import 'package:go_mboka/core/api.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final credentials = File(
    '../.local/personnel-recette.txt',
  ).readAsStringSync();
  final password = credentials.split('Mot de passe : ')[1].split('\n')[0];
  final api = PersonnelApi('http://127.0.0.1:8000');
  await api.login('+243000900001', password);
  final key = GlobalKey();
  runApp(
    RepaintBoundary(
      key: key,
      child: PersonnelApp(
        api: api,
        initialPage: const int.fromEnvironment('PREVIEW_PAGE', defaultValue: 1),
      ),
    ),
  );
  for (final seconds in [15, 30]) {
    Timer(Duration(seconds: seconds), () async {
      final boundary =
          key.currentContext!.findRenderObject() as RenderRepaintBoundary;
      final image = await boundary.toImage();
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      await Directory('verification/live').create(recursive: true);
      await File(
        'verification/live/native-road-$seconds.png',
      ).writeAsBytes(bytes!.buffer.asUint8List());
      image.dispose();
    });
  }
}
