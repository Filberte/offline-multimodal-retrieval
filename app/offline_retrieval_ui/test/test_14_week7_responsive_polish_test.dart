import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/app.dart';
import 'package:offline_retrieval_ui/models/release_info.dart';
import 'package:offline_retrieval_ui/state/app_controller.dart';

import 'week6_test_support.dart';

void main() {
  Future<AppController> pumpSettings(
    WidgetTester tester, {
    required Size size,
    double fontScale = 1,
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final controller = AppController(FakeWeek6RetrievalClient());
    controller.selectDestination(2);
    controller.setFontScale(fontScale);
    await tester.pumpWidget(OfflineRetrievalApp(controller: controller));
    await tester.pumpAndSettle();
    return controller;
  }

  group('Week 8 正式版响应式与平台发布元数据', () {
    testWidgets('TC-481 三百二十像素设置中心无渲染异常', (tester) async {
      await pumpSettings(tester, size: const Size(320, 1200));
      expect(
        find.byKey(const ValueKey<String>('mobile-shell')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('TC-482 三百二十像素二倍字体发布卡无溢出', (tester) async {
      await pumpSettings(tester, size: const Size(320, 1600), fontScale: 2);
      expect(
        find.byKey(const ValueKey<String>('release-about-card')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('TC-483 移动端帮助主题保持单列完整卡片', (tester) async {
      await pumpSettings(tester, size: const Size(390, 1600));
      final first = tester.getTopLeft(
        find.byKey(const ValueKey<String>('help-install')),
      );
      final second = tester.getTopLeft(
        find.byKey(const ValueKey<String>('help-operate')),
      );
      expect(first.dx, second.dx);
      expect(second.dy, greaterThan(first.dy));
    });

    testWidgets('TC-484 桌面端帮助主题使用两列布局', (tester) async {
      await pumpSettings(tester, size: const Size(1280, 1600));
      final first = tester.getTopLeft(
        find.byKey(const ValueKey<String>('help-install')),
      );
      final second = tester.getTopLeft(
        find.byKey(const ValueKey<String>('help-operate')),
      );
      expect(second.dx, greaterThan(first.dx));
    });

    testWidgets('TC-485 平板端发布事实按单列重排', (tester) async {
      await pumpSettings(tester, size: const Size(700, 1600));
      final privacy = tester.getTopLeft(find.text(ReleaseInfo.privacyMode));
      final protocol = tester.getTopLeft(find.text(ReleaseInfo.protocol));
      expect(privacy.dx, protocol.dx);
      expect(protocol.dy, greaterThan(privacy.dy));
    });

    testWidgets('TC-486 桌面端发布事实形成三列概览', (tester) async {
      await pumpSettings(tester, size: const Size(1280, 1600));
      final privacy = tester.getTopLeft(find.text(ReleaseInfo.privacyMode));
      final protocol = tester.getTopLeft(find.text(ReleaseInfo.protocol));
      expect(privacy.dy, protocol.dy);
      expect(protocol.dx, greaterThan(privacy.dx));
    });

    testWidgets('TC-487 高对比度下发布声明仍可布局', (tester) async {
      final controller = await pumpSettings(
        tester,
        size: const Size(390, 1600),
      );
      controller.setHighContrast(true);
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey<String>('release-version-banner')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('TC-488 减少动画下帮助区仍完整', (tester) async {
      final controller = await pumpSettings(
        tester,
        size: const Size(700, 1600),
      );
      controller.setReduceMotion(true);
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey<String>('help-topic-grid')),
        findsOneWidget,
      );
    });

    testWidgets('TC-489 MaterialApp 标题与产品名称一致', (tester) async {
      tester.view.physicalSize = const Size(1280, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final controller = AppController(FakeWeek6RetrievalClient());
      await tester.pumpWidget(OfflineRetrievalApp(controller: controller));
      final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
      expect(app.title, ReleaseInfo.productName);
    });

    test('TC-490 生产 Dart 源码不调用 Material Icons', () {
      final sources = Directory(
        'lib',
      ).listSync(recursive: true).whereType<File>();
      expect(
        sources.where((file) => file.readAsStringSync().contains('Icons.')),
        isEmpty,
      );
    });

    test('TC-491 生产 Dart 源码不直接实例化默认 Icon', () {
      final sources = Directory(
        'lib',
      ).listSync(recursive: true).whereType<File>();
      expect(
        sources.where(
          (file) => RegExp(r'\bIcon\s*\(').hasMatch(file.readAsStringSync()),
        ),
        isEmpty,
      );
    });

    test('TC-492 发布配置保留框架资源并注册本地 CJK 字体', () {
      final pubspec = File('pubspec.yaml').readAsStringSync();
      expect(pubspec, contains('uses-material-design: true'));
      expect(pubspec, contains('OfflineRetrievalCJK-Regular.ttf'));
    });

    test('TC-493 发布配置保留框架图标和本地字体许可', () {
      final pubspec = File('pubspec.yaml').readAsStringSync();
      expect(pubspec, contains('cupertino_icons:'));
      expect(File('assets/fonts/OFL-NotoSansSC.txt').existsSync(), isTrue);
    });

    test('TC-494 Web manifest 使用正式产品名称', () {
      final manifest =
          jsonDecode(File('web/manifest.json').readAsStringSync())
              as Map<String, dynamic>;
      expect(manifest['name'], ReleaseInfo.platformDisplayName);
    });

    test('TC-495 Web manifest 允许独立响应式方向', () {
      final manifest =
          jsonDecode(File('web/manifest.json').readAsStringSync())
              as Map<String, dynamic>;
      expect(manifest['orientation'], 'any');
    });

    test('TC-496 Web 页面标题使用正式产品名称', () {
      expect(
        File('web/index.html').readAsStringSync(),
        contains('<title>${ReleaseInfo.platformDisplayName}</title>'),
      );
    });

    test('TC-497 Windows 窗口标题使用正式产品名称', () {
      expect(
        File('windows/runner/main.cpp').readAsStringSync(),
        contains('L"${ReleaseInfo.platformDisplayName}"'),
      );
    });

    test('TC-498 Android 应用标签使用正式产品名称', () {
      expect(
        File('android/app/src/main/AndroidManifest.xml').readAsStringSync(),
        contains('android:label="${ReleaseInfo.platformDisplayName}"'),
      );
    });

    test('TC-499 Flutter 包版本与 Week8 正式版本一致', () {
      expect(
        File('pubspec.yaml').readAsStringSync(),
        contains('version: 1.0.0+8'),
      );
    });

    test('TC-500 四个平台入口延续 Week6 工程命名', () {
      final paths = <String>[
        'web/manifest.json',
        'web/index.html',
        'windows/runner/main.cpp',
        'android/app/src/main/AndroidManifest.xml',
      ];
      expect(
        paths.every(
          (path) => File(path).readAsStringSync().contains(
            ReleaseInfo.platformDisplayName,
          ),
        ),
        isTrue,
      );
    });
  });
}
