import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/app.dart';
import 'package:offline_retrieval_ui/services/retrieval_client.dart';
import 'package:offline_retrieval_ui/state/app_controller.dart';

/// 生成报告使用的真实 Flutter 多设备界面快照，不计入 TC-001 至 TC-300。
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    final fontBytes = await File(r'C:\Windows\Fonts\simhei.ttf').readAsBytes();
    final loader = FontLoader('Week6Chinese')
      ..addFont(Future<ByteData>.value(ByteData.sublistView(fontBytes)));
    await loader.load();
  });

  testWidgets('生成 Week 6 多设备界面证据图', (tester) async {
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    Future<void> render({
      required Size size,
      required String keyName,
      required AppController controller,
      required String output,
    }) async {
      tester.view.physicalSize = size;
      await tester.pumpWidget(
        OfflineRetrievalApp(
          key: ValueKey(keyName),
          controller: controller,
          fontFamily: 'Week6Chinese',
        ),
      );
      await tester.pump(const Duration(milliseconds: 250));
      await expectLater(
        find.byType(Scaffold),
        matchesGoldenFile('screenshots/$output'),
      );
    }

    await render(
      size: const Size(1440, 900),
      keyName: 'desktop-library',
      controller: AppController(LocalDemoRetrievalClient()),
      output: '01_week6_desktop_library.png',
    );

    final desktopSearch = AppController(LocalDemoRetrievalClient());
    desktopSearch.setQuery('vector database');
    await desktopSearch.search();
    desktopSearch.selectDestination(1);
    await render(
      size: const Size(1440, 900),
      keyName: 'desktop-search',
      controller: desktopSearch,
      output: '02_week6_desktop_search.png',
    );

    desktopSearch.selectDestination(2);
    await desktopSearch.refreshHealth();
    await render(
      size: const Size(1440, 900),
      keyName: 'desktop-system',
      controller: desktopSearch,
      output: '03_week6_desktop_system.png',
    );

    await render(
      size: const Size(1024, 768),
      keyName: 'tablet-library',
      controller: AppController(LocalDemoRetrievalClient()),
      output: '04_week6_tablet_library.png',
    );

    await render(
      size: const Size(390, 844),
      keyName: 'mobile-library',
      controller: AppController(LocalDemoRetrievalClient()),
      output: '05_week6_mobile_library.png',
    );

    final mobileSearch = AppController(LocalDemoRetrievalClient());
    mobileSearch.setQuery('vector database');
    await mobileSearch.search();
    mobileSearch.selectDestination(1);
    await render(
      size: const Size(390, 844),
      keyName: 'mobile-search',
      controller: mobileSearch,
      output: '06_week6_mobile_search.png',
    );
  });
}
