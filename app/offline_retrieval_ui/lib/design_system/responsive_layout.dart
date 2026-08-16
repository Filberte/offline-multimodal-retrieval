import 'package:flutter/material.dart';

import 'app_theme.dart';

/// 界面按照设备形态重组，而不是仅按比例缩放。
enum AppDeviceClass { mobile, tablet, desktop }

/// 集中定义手机、平板和桌面端使用的响应式断点。
abstract final class AppBreakpoints {
  static const minimum = 320.0;
  static const compact = 600.0;
  static const medium = 1024.0;
  static const wide = 1440.0;

  static const navigationRail = 760.0;
  static const extendedNavigationRail = 1080.0;
  static const stackedHeader = 720.0;
  static const threeColumnMetrics = 720.0;
  static const stackedMetrics = 780.0;
  static const stackedSearchControls = 680.0;
  static const stackedResultCard = 620.0;
  static const twoColumnSettings = 700.0;
}

/// 根据可用宽度和字体比例提供统一的布局尺寸。
abstract final class ResponsiveLayout {
  static AppDeviceClass deviceClassFor(double width) {
    if (width < AppBreakpoints.compact) {
      return AppDeviceClass.mobile;
    }
    if (width < AppBreakpoints.medium) {
      return AppDeviceClass.tablet;
    }
    return AppDeviceClass.desktop;
  }

  static double textScaleOf(BuildContext context) {
    return MediaQuery.textScalerOf(context).scale(16) / 16;
  }

  static bool usesLargeText(BuildContext context) {
    return textScaleOf(context) >= 1.3;
  }

  static EdgeInsets pagePaddingFor(double width) {
    if (width < 360) {
      return const EdgeInsets.fromLTRB(
        AppSpacing.m,
        AppSpacing.l,
        AppSpacing.m,
        AppSpacing.xxl,
      );
    }
    if (width < AppBreakpoints.compact) {
      return const EdgeInsets.fromLTRB(
        AppSpacing.l,
        AppSpacing.xl,
        AppSpacing.l,
        AppSpacing.xxxl,
      );
    }
    return const EdgeInsets.fromLTRB(
      AppSpacing.xl,
      AppSpacing.xl,
      AppSpacing.xl,
      AppSpacing.xxxl,
    );
  }

  static EdgeInsets sectionPaddingFor(double width) {
    return EdgeInsets.all(
      width < AppBreakpoints.compact ? AppSpacing.m : AppSpacing.l,
    );
  }

  static double toolbarHeight(BuildContext context) {
    final scale = textScaleOf(context);
    return (68 + (scale - 1) * 16).clamp(68, 84).toDouble();
  }

  static double mobileToolbarHeight(BuildContext context) {
    final scale = textScaleOf(context);
    return (56 + (scale - 1) * 16).clamp(56, 76).toDouble();
  }

  static double statusBarHeight(BuildContext context) {
    final scale = textScaleOf(context);
    return (38 + (scale - 1) * 12).clamp(38, 50).toDouble();
  }

  static double bottomNavigationHeight(BuildContext context) {
    final scale = textScaleOf(context);
    return (72 + (scale - 1) * 20).clamp(72, 92).toDouble();
  }
}
