import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/app.dart';
import 'package:offline_retrieval_ui/design_system/app_icons.dart';
import 'package:offline_retrieval_ui/models/retrieval_models.dart';
import 'package:offline_retrieval_ui/services/platform_retrieval_client.dart';
import 'package:offline_retrieval_ui/services/retrieval_client.dart';
import 'package:offline_retrieval_ui/state/app_controller.dart';

import 'week6_test_support.dart';

void main() {
  Future<AppController> pumpWeek6(
    WidgetTester tester, {
    FakeWeek6RetrievalClient? client,
    Size size = const Size(1200, 800),
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final controller = AppController(client ?? FakeWeek6RetrievalClient());
    await tester.pumpWidget(OfflineRetrievalApp(controller: controller));
    await tester.pumpAndSettle();
    return controller;
  }

  Future<void> openSettings(WidgetTester tester) async {
    await tester.tap(find.text('设置').first);
    await tester.pumpAndSettle();
  }

  group('Week 6 Flutter 集成、恢复与多设备回归', () {
    testWidgets('TC-286 资料库提供本地路径索引入口', (tester) async {
      await pumpWeek6(tester);
      expect(
        find.byKey(const ValueKey<String>('index-local-path')),
        findsOneWidget,
      );
    });

    testWidgets('TC-287 点击索引入口打开本地路径对话框', (tester) async {
      await pumpWeek6(tester);
      await tester.tap(find.byKey(const ValueKey<String>('index-local-path')));
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey<String>('index-path-dialog')),
        findsOneWidget,
      );
    });

    testWidgets('TC-288 空索引路径显示就地校验信息', (tester) async {
      await pumpWeek6(tester);
      await tester.tap(find.byKey(const ValueKey<String>('index-local-path')));
      await tester.pumpAndSettle();
      await tester.tap(
        find.byKey(const ValueKey<String>('confirm-index-path')),
      );
      await tester.pump();
      expect(find.text('请输入本地路径'), findsOneWidget);
    });

    testWidgets('TC-289 有效路径触发索引并显示成功结果', (tester) async {
      final client = FakeWeek6RetrievalClient();
      await pumpWeek6(tester, client: client);
      await tester.tap(find.byKey(const ValueKey<String>('index-local-path')));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const ValueKey<String>('index-path-field')),
        r'C:\library',
      );
      await tester.tap(
        find.byKey(const ValueKey<String>('confirm-index-path')),
      );
      await tester.pumpAndSettle();
      expect(client.indexCalls, 1);
      expect(find.textContaining('索引完成'), findsOneWidget);
    });

    testWidgets('TC-290 设置页展示系统与本地隐私状态', (tester) async {
      await pumpWeek6(tester);
      await openSettings(tester);
      expect(find.text('系统与本地隐私状态'), findsOneWidget);
      expect(find.text('数据边界'), findsOneWidget);
    });

    testWidgets('TC-291 后端状态刷新按钮调用健康接口', (tester) async {
      final client = FakeWeek6RetrievalClient();
      await pumpWeek6(tester, client: client);
      await openSettings(tester);
      await tester.tap(
        find.byKey(const ValueKey<String>('refresh-backend-health')),
      );
      await tester.pumpAndSettle();
      expect(client.healthCalls, 1);
    });

    testWidgets('TC-292 降级原因在设置页明确显示', (tester) async {
      final client = FakeWeek6RetrievalClient(
        healthResponse: const BackendHealth(
          status: 'degraded',
          mode: 'demo-fallback',
          offlineOnly: true,
          backendName: 'fallback',
          vectorStore: 'memory',
          indexedRecords: 0,
          uptimeSeconds: 0,
          issues: <String>['后端测试降级原因'],
        ),
      );
      final controller = await pumpWeek6(tester, client: client);
      await controller.initialize();
      await tester.pumpAndSettle();
      await openSettings(tester);
      expect(find.text('后端测试降级原因'), findsOneWidget);
    });

    testWidgets('TC-293 桌面端集成改动保持独立桌面骨架', (tester) async {
      await pumpWeek6(tester, size: const Size(1280, 800));
      expect(
        find.byKey(const ValueKey<String>('desktop-shell')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey<String>('navigation-bar')),
        findsNothing,
      );
    });

    testWidgets('TC-294 平板端系统状态采用重排布局', (tester) async {
      await pumpWeek6(tester, size: const Size(700, 900));
      expect(
        find.byKey(const ValueKey<String>('tablet-shell')),
        findsOneWidget,
      );
      await openSettings(tester);
      expect(find.text('系统与本地隐私状态'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('TC-295 移动端保留底部导航和索引入口', (tester) async {
      await pumpWeek6(tester, size: const Size(390, 844));
      expect(
        find.byKey(const ValueKey<String>('mobile-shell')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey<String>('navigation-bar')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey<String>('index-local-path')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey<String>('mobile-metric-grid')),
        findsOneWidget,
      );
      expect(find.byType(AppIcon), findsWidgets);
      expect(tester.takeException(), isNull);

      // 对全部本地自绘图标的普通态与选中态做一次完整绘制冒烟测试。
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Wrap(
              children: <Widget>[
                for (final glyph in AppGlyph.values) AppIcon(glyph),
                for (final glyph in AppGlyph.values)
                  AppIcon(glyph, selected: true),
              ],
            ),
          ),
        ),
      );
      await tester.pump();
      expect(find.byType(AppIcon), findsNWidgets(AppGlyph.values.length * 2));
    });

    testWidgets('TC-296 320px 与 200% 字体下索引对话框无溢出', (tester) async {
      final controller = await pumpWeek6(tester, size: const Size(320, 800));
      controller.setFontScale(2);
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey<String>('index-local-path')));
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey<String>('index-path-dialog')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('TC-297 检索异常转换为可读界面警告', (tester) async {
      final client = FakeWeek6RetrievalClient()..throwOnSearch = true;
      await pumpWeek6(tester, client: client);
      await tester.tap(find.text('搜索').first);
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const ValueKey<String>('search-field')),
        'vector',
      );
      await tester.tap(find.byKey(const ValueKey<String>('run-search')));
      await tester.pumpAndSettle();
      expect(find.textContaining('planned search failure'), findsOneWidget);
    });

    test('TC-298 控制器初始化具有幂等性', () async {
      final client = FakeWeek6RetrievalClient();
      final controller = AppController(client);
      await controller.initialize();
      await controller.initialize();
      expect((client.healthCalls, client.libraryCalls), (1, 1));
    });

    test('TC-299 控制器释放时关闭本地客户端', () async {
      final client = FakeWeek6RetrievalClient();
      final controller = AppController(client);
      controller.dispose();
      await Future<void>.delayed(Duration.zero);
      expect(client.closeCalls, 1);
    });

    test('TC-300 平台工厂返回稳定 RetrievalClient 接口', () async {
      final RetrievalClient client = createPlatformRetrievalClient();
      expect(client, isA<RetrievalClient>());
      await client.close();
    });
  });
}
