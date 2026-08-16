import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/app.dart';
import 'package:offline_retrieval_ui/services/retrieval_client.dart';
import 'package:offline_retrieval_ui/state/app_controller.dart';

/// Generates current Week 8 Flutter widget-render evidence on the Windows host.
/// These images prove the UI state and responsive rendering; they are not a
/// substitute for the separate real-model backend smoke-test evidence.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    final fontBytes = await File(r'C:\Windows\Fonts\msyh.ttc').readAsBytes();
    final loader = FontLoader('Week8Chinese')
      ..addFont(Future<ByteData>.value(ByteData.sublistView(fontBytes)));
    await loader.load();
  });

  testWidgets('generate Week 8 final UI evidence', (tester) async {
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
          fontFamily: 'Week8Chinese',
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
      keyName: 'week8-desktop-library',
      controller: AppController(LocalDemoRetrievalClient()),
      output: '01_week8_desktop_library.png',
    );

    final search = AppController(LocalDemoRetrievalClient());
    search.setQuery('vector database');
    await search.search();
    search.selectDestination(1);
    await render(
      size: const Size(1440, 900),
      keyName: 'week8-desktop-search',
      controller: search,
      output: '02_week8_desktop_search.png',
    );

    search.selectDestination(2);
    await search.refreshHealth();
    await render(
      size: const Size(1440, 900),
      keyName: 'week8-desktop-system',
      controller: search,
      output: '03_week8_desktop_system.png',
    );

    await render(
      size: const Size(390, 844),
      keyName: 'week8-mobile-library',
      controller: AppController(LocalDemoRetrievalClient()),
      output: '04_week8_mobile_library.png',
    );
  });
}
