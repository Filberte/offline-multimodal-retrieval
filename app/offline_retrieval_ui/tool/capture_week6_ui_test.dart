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
    final fontLoader = FontLoader('Week6Chinese')
      ..addFont(Future<ByteData>.value(ByteData.sublistView(fontBytes)));
    await fontLoader.load();
  });

  testWidgets('生成 Week 6 多设备界面证据图', (tester) async {
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    tester.view.physicalSize = const Size(1440, 900);
    final desktopLibrary = AppController(LocalDemoRetrievalClient());
    await tester.pumpWidget(
      OfflineRetrievalApp(
        controller: desktopLibrary,
        fontFamily: 'Week6Chinese',
      ),
    );
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('screenshots/01_week6_desktop_library.png'),
    );

    final desktopSearch = AppController(LocalDemoRetrievalClient());
    desktopSearch.setQuery('vector database');
    await desktopSearch.search();
    desktopSearch.selectDestination(1);
    await tester.pumpWidget(
      OfflineRetrievalApp(
        key: const ValueKey('desktop-search'),
        controller: desktopSearch,
        fontFamily: 'Week6Chinese',
      ),
    );
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('screenshots/02_week6_desktop_search.png'),
    );

    desktopSearch.selectDestination(2);
    await desktopSearch.refreshHealth();
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('screenshots/03_week6_desktop_system.png'),
    );

    tester.view.physicalSize = const Size(1024, 768);
    final tabletLibrary = AppController(LocalDemoRetrievalClient());
    await tester.pumpWidget(
      OfflineRetrievalApp(
        key: const ValueKey('tablet-library'),
        controller: tabletLibrary,
        fontFamily: 'Week6Chinese',
      ),
    );
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('screenshots/04_week6_tablet_library.png'),
    );

    tester.view.physicalSize = const Size(390, 844);
    final mobileLibrary = AppController(LocalDemoRetrievalClient());
    await tester.pumpWidget(
      OfflineRetrievalApp(
        key: const ValueKey('mobile-library'),
        controller: mobileLibrary,
        fontFamily: 'Week6Chinese',
      ),
    );
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('screenshots/05_week6_mobile_library.png'),
    );

    final mobileSearch = AppController(LocalDemoRetrievalClient());
    mobileSearch.setQuery('vector database');
    await mobileSearch.search();
    mobileSearch.selectDestination(1);
    await tester.pumpWidget(
      OfflineRetrievalApp(
        key: const ValueKey('mobile-search'),
        controller: mobileSearch,
        fontFamily: 'Week6Chinese',
      ),
    );
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('screenshots/06_week6_mobile_search.png'),
    );
  });
}
