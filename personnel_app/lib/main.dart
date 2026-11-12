import 'package:flutter/material.dart';
import 'features/direction/dashboard.dart';
import 'core/api.dart';
import 'theme/personnel_theme.dart';

void main() => runApp(const PersonnelApp());

class PersonnelApp extends StatelessWidget {
  const PersonnelApp({super.key, this.api, this.initialPage = 0});
  final PersonnelApi? api;
  final int initialPage;
  @override
  Widget build(BuildContext context) => ValueListenableBuilder<ThemeMode>(
    valueListenable: PersonnelTheme.mode,
    builder: (context, mode, _) => MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'GO-MBOKA · Personnel',
      theme: PersonnelTheme.light(),
      darkTheme: PersonnelTheme.dark(),
      themeMode: mode,
      home: DirectionDashboard(initialApi: api, initialPage: initialPage),
    ),
  );
}
