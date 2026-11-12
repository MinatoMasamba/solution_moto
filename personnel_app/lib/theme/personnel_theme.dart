import 'package:flutter/material.dart';
import 'app_theme.dart';
import 'app_colors.dart';

/// Shared palette adapted from /home/minato/project/flutter_app.
class PersonnelTheme {
  static final mode = ValueNotifier<ThemeMode>(ThemeMode.light);
  static ThemeData light() => finish(AppTheme.light());
  static ThemeData dark() => finish(
    ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      fontFamily: 'Inter',
      scaffoldBackgroundColor: const Color(0xff06060c),
      colorScheme: const ColorScheme.dark(
        primary: AppColors.rdcBlue,
        onPrimary: Colors.white,
        surface: Color(0xff0c0c14),
        onSurface: Color(0xffe2e8f0),
        outline: Color(0xff334155),
      ),
    ),
  );
  static ThemeData finish(ThemeData base) {
    final dark = base.brightness == Brightness.dark;
    final line = dark ? const Color(0xff334155) : AppColors.border;
    return base.copyWith(
      dividerColor: line,
      cardTheme: CardThemeData(
        color: base.colorScheme.surface,
        surfaceTintColor: Colors.transparent,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: dark ? const Color(0xff101019) : AppColors.surfaceAlt,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 15,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: line),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
      dataTableTheme: DataTableThemeData(
        headingTextStyle: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: dark ? const Color(0xff94a3b8) : AppColors.muted,
        ),
        dataTextStyle: TextStyle(
          fontSize: 12,
          color: base.colorScheme.onSurface,
        ),
      ),
    );
  }

  static void apply(String value) {
    mode.value =
        {
          'dark': ThemeMode.dark,
          'light': ThemeMode.light,
          'system': ThemeMode.system,
        }[value] ??
        ThemeMode.light;
  }
}
