import 'package:flutter/material.dart';

/// 项目统一使用的 Amazon 风格衍生颜色。
///
/// 这些颜色只用于本项目界面，不代表 Amazon 官方品牌令牌。
abstract final class AppColors {
  static const navPrimary = Color(0xFF131921);
  static const navSecondary = Color(0xFF232F3E);
  static const accent = Color(0xFFFF9900);
  static const accentHover = Color(0xFFE47911);
  static const page = Color(0xFFF3F4F5);
  static const surface = Color(0xFFFFFFFF);
  static const surfaceSubtle = Color(0xFFF7F8F8);
  static const border = Color(0xFFD5D9D9);
  static const borderStrong = Color(0xFF888C8C);
  static const textPrimary = Color(0xFF0F1111);
  static const textSecondary = Color(0xFF565959);
  static const link = Color(0xFF007185);
  static const success = Color(0xFF067D62);
  static const warning = Color(0xFFB12704);
}

/// 采用 4 像素基准网格的统一间距。
abstract final class AppSpacing {
  static const xxs = 4.0;
  static const xs = 8.0;
  static const s = 12.0;
  static const m = 16.0;
  static const l = 20.0;
  static const xl = 24.0;
  static const xxl = 32.0;
  static const xxxl = 40.0;
}

/// 构建普通模式与高对比度模式的应用主题。
abstract final class AppTheme {
  static ThemeData light({String? fontFamily}) {
    const scheme = ColorScheme.light(
      primary: AppColors.accent,
      onPrimary: AppColors.textPrimary,
      secondary: AppColors.link,
      onSecondary: Colors.white,
      surface: AppColors.surface,
      onSurface: AppColors.textPrimary,
      error: AppColors.warning,
      onError: Colors.white,
      outline: AppColors.borderStrong,
      outlineVariant: AppColors.border,
    );
    return _build(
      scheme: scheme,
      scaffoldBackground: AppColors.page,
      appBarBackground: AppColors.navPrimary,
      navigationBackground: AppColors.surface,
      fontFamily: fontFamily,
      highContrast: false,
    );
  }

  static ThemeData highContrast({String? fontFamily}) {
    const scheme = ColorScheme.dark(
      primary: Color(0xFFFFFF00),
      onPrimary: Colors.black,
      secondary: Color(0xFF00FFFF),
      onSecondary: Colors.black,
      surface: Colors.black,
      onSurface: Colors.white,
      error: Color(0xFFFF6B6B),
      onError: Colors.black,
      outline: Colors.white,
      outlineVariant: Color(0xFFBDBDBD),
    );
    return _build(
      scheme: scheme,
      scaffoldBackground: Colors.black,
      appBarBackground: Colors.black,
      navigationBackground: const Color(0xFF111111),
      fontFamily: fontFamily,
      highContrast: true,
    );
  }

  static ThemeData _build({
    required ColorScheme scheme,
    required Color scaffoldBackground,
    required Color appBarBackground,
    required Color navigationBackground,
    required String? fontFamily,
    required bool highContrast,
  }) {
    final base = ThemeData(
      useMaterial3: true,
      brightness: scheme.brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: scaffoldBackground,
      fontFamily: fontFamily,
      visualDensity: VisualDensity.standard,
    );
    final textTheme = base.textTheme.copyWith(
      headlineMedium: base.textTheme.headlineMedium?.copyWith(
        fontSize: 28,
        height: 1.2,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.3,
      ),
      titleLarge: base.textTheme.titleLarge?.copyWith(
        fontSize: 20,
        height: 1.25,
        fontWeight: FontWeight.w700,
      ),
      titleMedium: base.textTheme.titleMedium?.copyWith(
        fontSize: 16,
        height: 1.35,
        fontWeight: FontWeight.w600,
      ),
      bodyLarge: base.textTheme.bodyLarge?.copyWith(fontSize: 15, height: 1.45),
      bodyMedium: base.textTheme.bodyMedium?.copyWith(
        fontSize: 14,
        height: 1.45,
      ),
      bodySmall: base.textTheme.bodySmall?.copyWith(fontSize: 12, height: 1.4),
    );

    return base.copyWith(
      textTheme: textTheme,
      focusColor: highContrast ? scheme.primary : AppColors.link,
      appBarTheme: AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        backgroundColor: appBarBackground,
        foregroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: textTheme.titleLarge?.copyWith(color: Colors.white),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        margin: EdgeInsets.zero,
        color: scheme.surface,
        surfaceTintColor: Colors.transparent,
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: BorderSide(color: scheme.outlineVariant),
        ),
      ),
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: navigationBackground,
        indicatorColor: highContrast ? scheme.primary : const Color(0xFFFFE6BF),
        indicatorShape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(6),
        ),
        selectedIconTheme: IconThemeData(
          color: highContrast ? scheme.onPrimary : AppColors.textPrimary,
        ),
        selectedLabelTextStyle: textTheme.labelLarge?.copyWith(
          fontWeight: FontWeight.w700,
          color: scheme.onSurface,
        ),
        unselectedIconTheme: IconThemeData(color: scheme.onSurfaceVariant),
        unselectedLabelTextStyle: textTheme.labelLarge?.copyWith(
          color: scheme.onSurfaceVariant,
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 72,
        elevation: 0,
        backgroundColor: navigationBackground,
        indicatorColor: highContrast ? scheme.primary : const Color(0xFFFFE6BF),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          return textTheme.labelMedium?.copyWith(
            color: scheme.onSurface,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w700
                : FontWeight.w500,
          );
        }),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(48, 44),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
          textStyle: textTheme.labelLarge?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(48, 44),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          side: BorderSide(color: scheme.outline),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
          textStyle: textTheme.labelLarge?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          minimumSize: const Size(44, 40),
          foregroundColor: highContrast ? scheme.secondary : AppColors.link,
          textStyle: textTheme.labelLarge?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: scheme.surface,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 14,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: BorderSide(color: scheme.outlineVariant),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: BorderSide(color: scheme.outline),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: BorderSide(color: scheme.secondary, width: 2),
        ),
      ),
      chipTheme: ChipThemeData(
        side: BorderSide(color: scheme.outlineVariant),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
        selectedColor: highContrast ? scheme.primary : const Color(0xFFFFE6BF),
        checkmarkColor: highContrast ? scheme.onPrimary : AppColors.textPrimary,
        labelStyle: textTheme.labelLarge,
      ),
      dividerTheme: DividerThemeData(
        color: scheme.outlineVariant,
        thickness: 1,
        space: 1,
      ),
      tooltipTheme: TooltipThemeData(
        waitDuration: const Duration(milliseconds: 400),
        decoration: BoxDecoration(
          color: highContrast ? Colors.white : AppColors.navPrimary,
          borderRadius: BorderRadius.circular(4),
        ),
        textStyle: TextStyle(
          color: highContrast ? Colors.black : Colors.white,
          fontSize: 12,
        ),
      ),
    );
  }
}
