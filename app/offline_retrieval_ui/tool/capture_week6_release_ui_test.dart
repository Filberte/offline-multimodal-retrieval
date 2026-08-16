import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'capture_week6_final_ui_test.dart' as final_capture;

/// 为最终截图补充中文常规与粗体字形，再复用完整多设备渲染流程。
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    final regular = await File(r'C:\Windows\Fonts\msyh.ttc').readAsBytes();
    final bold = await File(r'C:\Windows\Fonts\msyhbd.ttc').readAsBytes();
    final loader = FontLoader('Week6Chinese')
      ..addFont(Future<ByteData>.value(ByteData.sublistView(regular)))
      ..addFont(Future<ByteData>.value(ByteData.sublistView(bold)));
    await loader.load();
  });
  final_capture.main();
}
