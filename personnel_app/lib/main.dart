import 'package:flutter/material.dart';
import 'features/direction/dashboard.dart';
import 'core/api.dart';

void main() => runApp(const PersonnelApp());

class PersonnelApp extends StatelessWidget {
  const PersonnelApp({super.key, this.api, this.initialPage = 0});
  final PersonnelApi? api;
  final int initialPage;
  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'GO-MBOKA · Personnel',
    theme: ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xff161826),
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xff9184d9),
        brightness: Brightness.dark,
      ),
      fontFamily: 'Inter',
      useMaterial3: true,
    ),
    home: DirectionDashboard(initialApi: api, initialPage: initialPage),
  );
}
