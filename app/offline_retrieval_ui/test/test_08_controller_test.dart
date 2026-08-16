import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/services/retrieval_client.dart';
import 'package:offline_retrieval_ui/state/app_controller.dart';

void main() {
  group('Week 5 界面状态控制器', () {
    test('TC-121 控制器默认打开资料库页', () {
      final controller = AppController(LocalDemoRetrievalClient());
      expect(controller.selectedIndex, 0);
    });

    test('TC-122 导航索引上界限制为设置页', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.selectDestination(99);
      expect(controller.selectedIndex, 2);
    });

    test('TC-123 导航索引下界限制为资料库页', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.selectDestination(-5);
      expect(controller.selectedIndex, 0);
    });

    test('TC-124 选择当前导航页不会重复通知', () {
      final controller = AppController(LocalDemoRetrievalClient());
      var notifications = 0;
      controller.addListener(() => notifications++);
      controller.selectDestination(0);
      expect(notifications, 0);
    });

    test('TC-125 控制器可以更新查询文本', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setQuery('semantic search');
      expect(controller.query, 'semantic search');
    });

    test('TC-126 相同查询文本不会重复通知', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setQuery('vector');
      var notifications = 0;
      controller.addListener(() => notifications++);
      controller.setQuery('vector');
      expect(notifications, 0);
    });

    test('TC-127 空扩展名会标准化为空过滤条件', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setExtension('');
      expect(controller.extension, isNull);
    });

    test('TC-128 控制器可以关闭图片结果', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setIncludeImages(false);
      expect(controller.includeImages, isFalse);
    });

    test('TC-129 控制器搜索后保存响应', () async {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setQuery('vector');
      await controller.search();
      expect(controller.response?.hits, isNotEmpty);
    });

    test('TC-130 控制器搜索结束后恢复空闲状态', () async {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setQuery('vector');
      await controller.search();
      expect(controller.isSearching, isFalse);
    });

    test('TC-131 控制器保留空查询警告', () async {
      final controller = AppController(LocalDemoRetrievalClient());
      await controller.search();
      expect(controller.response?.warnings, isNotEmpty);
    });

    test('TC-132 控制器可以开启高对比度', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setHighContrast(true);
      expect(controller.accessibility.highContrast, isTrue);
    });

    test('TC-133 字体缩放上限固定为 200%', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setFontScale(3);
      expect(controller.accessibility.fontScale, 2.0);
    });

    test('TC-134 字体缩放下限固定为 90%', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setFontScale(0.1);
      expect(controller.accessibility.fontScale, 0.9);
    });

    test('TC-135 控制器可以恢复默认无障碍设置', () {
      final controller = AppController(LocalDemoRetrievalClient());
      controller.setHighContrast(true);
      controller.setFontScale(2.0);
      controller.setReduceMotion(true);
      controller.resetAccessibility();
      expect(controller.accessibility.highContrast, isFalse);
      expect(controller.accessibility.fontScale, 1);
      expect(controller.accessibility.reduceMotion, isFalse);
    });
  });
}
