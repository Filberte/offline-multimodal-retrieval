import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/app.dart';
import 'package:offline_retrieval_ui/services/retrieval_client.dart';
import 'package:offline_retrieval_ui/state/app_controller.dart';

void main() {
  AppController createController() => AppController(LocalDemoRetrievalClient());

  Future<AppController> pumpApp(
    WidgetTester tester, {
    Size size = const Size(1200, 800),
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final controller = createController();
    await tester.pumpWidget(OfflineRetrievalApp(controller: controller));
    await tester.pumpAndSettle();
    return controller;
  }

  group('Week 5 Flutter 界面与无障碍工作流', () {
    testWidgets('TC-136 应用显示离线检索标题', (tester) async {
      await pumpApp(tester);
      expect(find.text('离线多模态内容检索'), findsOneWidget);
    });

    testWidgets('TC-137 资料库页具有明确标题', (tester) async {
      await pumpApp(tester);
      expect(find.text('本地资料库'), findsOneWidget);
    });

    testWidgets('TC-138 平板端和桌面端使用独立界面骨架', (tester) async {
      await pumpApp(tester, size: const Size(600, 800));
      expect(find.byKey(const ValueKey('tablet-shell')), findsOneWidget);
      expect(find.byKey(const ValueKey('navigation-rail')), findsOneWidget);
      expect(
        tester
            .widget<NavigationRail>(
              find.byKey(const ValueKey('navigation-rail')),
            )
            .extended,
        isFalse,
      );
      expect(find.byKey(const ValueKey('navigation-bar')), findsNothing);
      tester.view.physicalSize = const Size(1024, 768);
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('desktop-shell')), findsOneWidget);
      expect(
        tester
            .widget<NavigationRail>(
              find.byKey(const ValueKey('navigation-rail')),
            )
            .extended,
        isTrue,
      );
    });

    testWidgets('TC-139 移动端使用底部导航和触控筛选面板', (tester) async {
      await pumpApp(tester, size: const Size(599, 800));
      expect(find.byKey(const ValueKey('mobile-shell')), findsOneWidget);
      expect(find.byKey(const ValueKey('navigation-bar')), findsOneWidget);
      expect(find.byKey(const ValueKey('mobile-search-entry')), findsOneWidget);
      expect(tester.takeException(), isNull);
      tester.view.physicalSize = const Size(320, 800);
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('navigation-bar')), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('mobile-search-entry')));
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey('mobile-filter-button')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('TC-140 点击导航可以打开搜索页', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.text('搜索'));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('search-screen')), findsOneWidget);
    });

    testWidgets('TC-141 搜索页包含可聚焦搜索框', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.text('搜索'));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('search-field')), findsOneWidget);
    });

    testWidgets('TC-142 运行搜索后显示匹配结果', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.text('搜索'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const ValueKey('search-field')),
        'vector database',
      );
      await tester.tap(find.byKey(const ValueKey('run-search')));
      await tester.pumpAndSettle();
      expect(find.text('vector_database.txt'), findsOneWidget);
    });

    testWidgets('TC-143 清除按钮可以清空查询', (tester) async {
      final controller = await pumpApp(tester);
      await tester.tap(find.text('搜索'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const ValueKey('search-field')),
        'vector',
      );
      await tester.tap(find.byKey(const ValueKey('clear-search')));
      await tester.pump();
      expect(controller.query, isEmpty);
    });

    testWidgets('TC-144 搜索页提供文件类型过滤器', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.text('搜索'));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('extension-filter')), findsOneWidget);
    });

    testWidgets('TC-145 搜索页提供图片结果开关', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.text('搜索'));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('include-images')), findsOneWidget);
    });

    testWidgets('TC-146 点击导航可以打开无障碍设置', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.text('设置'));
      await tester.pumpAndSettle();
      expect(find.text('无障碍设置'), findsOneWidget);
    });

    testWidgets('TC-147 高对比度开关立即更新状态', (tester) async {
      final controller = await pumpApp(tester);
      await tester.tap(find.text('设置'));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('high-contrast-toggle')));
      await tester.pumpAndSettle();
      expect(controller.accessibility.highContrast, isTrue);
    });

    testWidgets('TC-148 减少动画开关立即更新状态', (tester) async {
      final controller = await pumpApp(tester);
      await tester.tap(find.text('设置'));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('reduce-motion-toggle')));
      await tester.pumpAndSettle();
      expect(controller.accessibility.reduceMotion, isTrue);
    });

    testWidgets('TC-149 200% 字体在 320px 设置页自动重排', (tester) async {
      final controller = await pumpApp(tester);
      tester.view.physicalSize = const Size(320, 800);
      controller.selectDestination(2);
      controller.setFontScale(2.0);
      await tester.pumpAndSettle();
      final context = tester.element(find.byType(RetrievalShell));
      expect(MediaQuery.of(context).textScaler.scale(10), 20);
      expect(find.text('200%'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('TC-150 Ctrl+K 打开搜索页并聚焦输入框', (tester) async {
      final controller = await pumpApp(tester);
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyK);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pumpAndSettle();
      expect(controller.selectedIndex, 1);
      final editable = tester.widget<EditableText>(
        find.byType(EditableText).first,
      );
      expect(editable.focusNode.hasFocus, isTrue);
    });
  });
}
