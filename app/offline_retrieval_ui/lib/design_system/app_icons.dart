import 'dart:math' as math;

import 'package:flutter/material.dart';

/// 项目自有的本地矢量图标语义，避免依赖在线资源或系统图标字体。
enum AppGlyph {
  library,
  search,
  searchEmpty,
  settings,
  lock,
  offline,
  verified,
  info,
  addFolder,
  inventory,
  category,
  image,
  filterOff,
  success,
  folder,
  document,
  pdf,
  text,
  external,
  article,
  tune,
  close,
  contrast,
  reduceMotion,
  refresh,
  fontSize,
  accessibility,
  arrowForward,
  restart,
}

/// 统一绘制圆角线性图标；选中态通过加粗与局部填充提高辨识度。
class AppIcon extends StatelessWidget {
  const AppIcon(
    this.glyph, {
    this.size = 24,
    this.color,
    this.selected = false,
    this.semanticLabel,
    super.key,
  });

  final AppGlyph glyph;
  final double size;
  final Color? color;
  final bool selected;
  final String? semanticLabel;

  @override
  Widget build(BuildContext context) {
    final icon = CustomPaint(
      size: Size.square(size),
      painter: _AppIconPainter(
        glyph: glyph,
        color: color ?? IconTheme.of(context).color ?? Colors.black,
        selected: selected,
      ),
    );
    if (semanticLabel == null) {
      return ExcludeSemantics(child: icon);
    }
    return Semantics(label: semanticLabel, image: true, child: icon);
  }
}

class _AppIconPainter extends CustomPainter {
  const _AppIconPainter({
    required this.glyph,
    required this.color,
    required this.selected,
  });

  final AppGlyph glyph;
  final Color color;
  final bool selected;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(size.width / 24, size.height / 24);
    final stroke = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = selected ? 2.25 : 1.85
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final fill = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    void line(double x1, double y1, double x2, double y2) =>
        canvas.drawLine(Offset(x1, y1), Offset(x2, y2), stroke);
    void circle(double x, double y, double radius) =>
        canvas.drawCircle(Offset(x, y), radius, stroke);
    void rounded(
      double left,
      double top,
      double right,
      double bottom, [
      double radius = 2,
    ]) => canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTRB(left, top, right, bottom),
        Radius.circular(radius),
      ),
      stroke,
    );
    void path(List<Offset> points, {bool close = false}) {
      final value = Path()..moveTo(points.first.dx, points.first.dy);
      for (final point in points.skip(1)) {
        value.lineTo(point.dx, point.dy);
      }
      if (close) value.close();
      canvas.drawPath(value, stroke);
    }

    switch (glyph) {
      case AppGlyph.library:
        path(const [Offset(3, 7), Offset(8, 7), Offset(10, 9), Offset(21, 9)]);
        rounded(3, 7, 21, 19, 2.2);
        line(7, 4, 18, 4);
        line(7, 22, 18, 22);
      case AppGlyph.search:
        circle(10.5, 10.5, 5.5);
        line(14.5, 14.5, 20.5, 20.5);
        if (selected) canvas.drawCircle(const Offset(10.5, 10.5), 1.5, fill);
      case AppGlyph.searchEmpty:
        circle(10.5, 10.5, 5.5);
        line(14.5, 14.5, 20.5, 20.5);
        line(4.5, 4.5, 17.5, 17.5);
      case AppGlyph.settings:
        circle(12, 12, 3.2);
        for (var i = 0; i < 8; i++) {
          final angle = i * math.pi / 4;
          line(
            12 + math.cos(angle) * 6,
            12 + math.sin(angle) * 6,
            12 + math.cos(angle) * 9,
            12 + math.sin(angle) * 9,
          );
        }
      case AppGlyph.lock:
        rounded(5, 10, 19, 21, 2.2);
        final shackle = Path()
          ..moveTo(8, 10)
          ..lineTo(8, 7.5)
          ..cubicTo(8, 2.8, 16, 2.8, 16, 7.5)
          ..lineTo(16, 10);
        canvas.drawPath(shackle, stroke);
        line(12, 14, 12, 17);
      case AppGlyph.offline:
        path(const [
          Offset(13, 2.5),
          Offset(5.5, 13),
          Offset(11, 13),
          Offset(9.8, 21.5),
          Offset(18.5, 10),
          Offset(13, 10),
        ], close: true);
      case AppGlyph.verified || AppGlyph.success:
        circle(12, 12, 8.5);
        path(const [Offset(7.5, 12.2), Offset(10.5, 15.2), Offset(16.8, 8.8)]);
      case AppGlyph.info:
        circle(12, 12, 8.5);
        line(12, 10.5, 12, 16);
        canvas.drawCircle(const Offset(12, 7.2), 1, fill);
      case AppGlyph.addFolder:
        path(const [Offset(3, 7), Offset(8, 7), Offset(10, 9), Offset(21, 9)]);
        rounded(3, 7, 21, 19, 2.2);
        line(15, 11.5, 15, 16.5);
        line(12.5, 14, 17.5, 14);
      case AppGlyph.inventory:
        rounded(4, 5, 20, 20, 2.2);
        line(4, 9, 20, 9);
        line(9, 13, 15, 13);
      case AppGlyph.category:
        rounded(3.5, 4, 10.5, 11, 1.6);
        circle(16.5, 7.5, 3.5);
        path(const [Offset(7, 14), Offset(11, 21), Offset(3, 21)], close: true);
        rounded(14, 14, 21, 21, 1.6);
      case AppGlyph.image:
        rounded(3, 4, 21, 20, 2.2);
        circle(8, 9, 2);
        path(const [
          Offset(5, 17),
          Offset(10, 12),
          Offset(13, 15),
          Offset(16, 11.5),
          Offset(20, 17),
        ]);
      case AppGlyph.filterOff:
        path(const [
          Offset(4, 5),
          Offset(20, 5),
          Offset(14, 12),
          Offset(14, 19),
          Offset(10, 21),
          Offset(10, 12),
          Offset(4, 5),
        ]);
        line(4, 3, 21, 21);
      case AppGlyph.folder:
        path(const [Offset(3, 7), Offset(8, 7), Offset(10, 9), Offset(21, 9)]);
        rounded(3, 7, 21, 19, 2.2);
      case AppGlyph.document ||
          AppGlyph.pdf ||
          AppGlyph.text ||
          AppGlyph.article:
        path(const [
          Offset(6, 3),
          Offset(15, 3),
          Offset(20, 8),
          Offset(20, 21),
          Offset(6, 21),
          Offset(6, 3),
        ], close: true);
        path(const [Offset(15, 3), Offset(15, 8), Offset(20, 8)]);
        if (glyph == AppGlyph.image) break;
        line(9, 12, 17, 12);
        line(9, 16, glyph == AppGlyph.pdf ? 14 : 17, 16);
      case AppGlyph.external:
        rounded(4, 7, 17, 20, 2);
        path(const [Offset(11, 4), Offset(20, 4), Offset(20, 13)]);
        line(20, 4, 10, 14);
      case AppGlyph.tune:
        line(4, 7, 20, 7);
        line(4, 17, 20, 17);
        canvas.drawCircle(const Offset(9, 7), 2, fill);
        canvas.drawCircle(const Offset(15, 17), 2, fill);
      case AppGlyph.close:
        line(5, 5, 19, 19);
        line(19, 5, 5, 19);
      case AppGlyph.contrast:
        circle(12, 12, 9);
        final half = Path()
          ..moveTo(12, 3)
          ..arcTo(
            const Rect.fromLTWH(3, 3, 18, 18),
            -math.pi / 2,
            math.pi,
            false,
          )
          ..close();
        canvas.drawPath(half, fill);
      case AppGlyph.reduceMotion:
        circle(12, 12, 8.5);
        line(4.5, 4.5, 19.5, 19.5);
        line(8, 12, 16, 12);
      case AppGlyph.refresh || AppGlyph.restart:
        final arc = Path()
          ..arcTo(const Rect.fromLTWH(4, 4, 16, 16), -0.35, 5.1, false);
        canvas.drawPath(arc, stroke);
        path(const [Offset(18.5, 4), Offset(20, 9), Offset(15, 8)]);
      case AppGlyph.fontSize:
        line(5, 19, 10, 5);
        line(10, 5, 15, 19);
        line(7, 14, 13, 14);
        line(15, 19, 18, 10);
        line(18, 10, 21, 19);
      case AppGlyph.accessibility:
        circle(12, 4.5, 2);
        line(5, 8, 19, 8);
        line(12, 8, 12, 14);
        line(12, 14, 7, 21);
        line(12, 14, 17, 21);
      case AppGlyph.arrowForward:
        line(4, 12, 20, 12);
        path(const [Offset(14, 6), Offset(20, 12), Offset(14, 18)]);
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _AppIconPainter oldDelegate) =>
      oldDelegate.glyph != glyph ||
      oldDelegate.color != color ||
      oldDelegate.selected != selected;
}
