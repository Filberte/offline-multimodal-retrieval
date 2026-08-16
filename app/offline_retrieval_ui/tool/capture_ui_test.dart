import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/app.dart';
import 'package:offline_retrieval_ui/services/retrieval_client.dart';
import 'package:offline_retrieval_ui/state/app_controller.dart';

/// 生成报告使用的真实 Flutter 界面快照，不计入 TC-001 至 TC-150。
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    final fontBytes = await File(r'C:\Windows\Fonts\simhei.ttf').readAsBytes();
    final fontLoader = FontLoader('Week5Chinese')
      ..addFont(Future<ByteData>.value(ByteData.sublistView(fontBytes)));
    await fontLoader.load();
  });

  testWidgets('生成 Week 5 界面证据图', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = AppController(LocalDemoRetrievalClient());
    await tester.pumpWidget(
      OfflineRetrievalApp(controller: controller, fontFamily: 'Week5Chinese'),
    );
    await tester.pumpAndSettle();

    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('screenshots/01_library.png'),
    );

    final searchController = AppController(LocalDemoRetrievalClient());
    searchController.setQuery('vector database');
    await searchController.search();
    searchController.selectDestination(1);
    await tester.pumpWidget(
      OfflineRetrievalApp(
        key: const ValueKey('search-capture'),
        controller: searchController,
        fontFamily: 'Week5Chinese',
      ),
    );
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('screenshots/02_search_results.png'),
    );

    searchController.selectDestination(2);
    searchController.setHighContrast(true);
    searchController.setFontScale(1.2);
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('screenshots/03_accessibility_settings.png'),
    );
  });
}
