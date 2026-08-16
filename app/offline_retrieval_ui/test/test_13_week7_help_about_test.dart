import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/app.dart';
import 'package:offline_retrieval_ui/models/release_info.dart';
import 'package:offline_retrieval_ui/state/app_controller.dart';

import 'week6_test_support.dart';

void main() {
  Future<AppController> pumpSettings(
    WidgetTester tester, {
    Size size = const Size(1280, 1600),
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final controller = AppController(FakeWeek6RetrievalClient());
    controller.selectDestination(2);
    await tester.pumpWidget(OfflineRetrievalApp(controller: controller));
    await tester.pumpAndSettle();
    return controller;
  }

  Future<void> reveal(WidgetTester tester, Finder finder) async {
    await tester.scrollUntilVisible(
      finder,
      700,
      scrollable: find.byType(Scrollable).last,
    );
    await tester.pumpAndSettle();
  }

  group('Week 8 应用内帮助、正式版本与合规披露', () {
    testWidgets('TC-461 设置页升级为无障碍与支持中心', (tester) async {
      await pumpSettings(tester);
      expect(find.text('设置、无障碍与支持'), findsOneWidget);
    });

    testWidgets('TC-462 设置页标明正式发布版', (tester) async {
      await pumpSettings(tester);
      expect(find.text('PRODUCTION RELEASE'), findsOneWidget);
    });

    testWidgets('TC-463 设置页包含版本与开源声明卡片', (tester) async {
      await pumpSettings(tester);
      expect(
        find.byKey(const ValueKey<String>('release-about-card')),
        findsOneWidget,
      );
    });

    testWidgets('TC-464 版本横幅显示正式版本', (tester) async {
      await pumpSettings(tester);
      expect(find.text(ReleaseInfo.version), findsOneWidget);
    });

    testWidgets('TC-465 版本横幅显示正式发布日期', (tester) async {
      await pumpSettings(tester);
      expect(find.textContaining(ReleaseInfo.releaseDate), findsOneWidget);
    });

    testWidgets('TC-466 隐私事实显示仅本地处理', (tester) async {
      await pumpSettings(tester);
      expect(find.text(ReleaseInfo.privacyMode), findsOneWidget);
    });

    testWidgets('TC-467 协议事实显示标准流桥接', (tester) async {
      await pumpSettings(tester);
      expect(find.text(ReleaseInfo.protocol), findsOneWidget);
    });

    testWidgets('TC-468 发布门禁事实显示六百项测试', (tester) async {
      await pumpSettings(tester);
      expect(find.text('600 项自动化测试'), findsOneWidget);
    });

    testWidgets('TC-469 四项能力边界均具有稳定组件键', (tester) async {
      await pumpSettings(tester);
      for (final item in ReleaseInfo.disclosures) {
        expect(
          find.byKey(ValueKey<String>('disclosure-${item.id}')),
          findsOneWidget,
        );
      }
    });

    testWidgets('TC-470 应用内明确不是生成式 AI', (tester) async {
      await pumpSettings(tester);
      expect(find.text('检索系统，不是生成式 AI'), findsOneWidget);
    });

    testWidgets('TC-471 应用内明确 OCR 限制', (tester) async {
      await pumpSettings(tester);
      expect(find.textContaining('OCR 尚未'), findsOneWidget);
    });

    testWidgets('TC-472 应用内明确模型权重不随源码分发', (tester) async {
      await pumpSettings(tester);
      expect(find.text('模型权重不随源码分发'), findsOneWidget);
    });

    testWidgets('TC-473 应用内明确桌面端生产验证范围', (tester) async {
      await pumpSettings(tester);
      expect(find.textContaining('Windows 桌面端'), findsOneWidget);
    });

    testWidgets('TC-474 开源摘要可通过稳定组件键定位', (tester) async {
      await pumpSettings(tester);
      expect(
        find.byKey(const ValueKey<String>('license-boundary-summary')),
        findsOneWidget,
      );
    });

    testWidgets('TC-475 无障碍主张避免错误认证表述', (tester) async {
      await pumpSettings(tester);
      expect(find.text(ReleaseInfo.accessibilityClaim), findsOneWidget);
    });

    testWidgets('TC-476 设置页包含离线快速帮助区域', (tester) async {
      await pumpSettings(tester);
      expect(
        find.byKey(const ValueKey<String>('help-topic-grid')),
        findsOneWidget,
      );
    });

    testWidgets('TC-477 四个帮助主题均具有稳定组件键', (tester) async {
      await pumpSettings(tester);
      for (final topic in ReleaseInfo.helpTopics) {
        expect(
          find.byKey(ValueKey<String>('help-${topic.id}')),
          findsOneWidget,
        );
      }
    });

    testWidgets('TC-478 快速帮助声明无需外部网站', (tester) async {
      await pumpSettings(tester);
      expect(find.textContaining('无需跳转到外部网站'), findsOneWidget);
    });

    testWidgets('TC-479 桌面端帮助主题采用两列信息层级', (tester) async {
      await pumpSettings(tester);
      final first = tester.getTopLeft(
        find.byKey(const ValueKey<String>('help-install')),
      );
      final second = tester.getTopLeft(
        find.byKey(const ValueKey<String>('help-operate')),
      );
      expect(first.dy, second.dy);
      expect(second.dx, greaterThan(first.dx));
    });

    testWidgets('TC-480 帮助卡为读屏器合并标题和文档动作', (tester) async {
      final handle = tester.ensureSemantics();
      await pumpSettings(tester);
      await reveal(tester, find.byKey(const ValueKey<String>('help-install')));
      expect(
        find.bySemanticsLabel(RegExp(r'INSTALLATION\.md')),
        findsOneWidget,
      );
      handle.dispose();
    });
  });
}
