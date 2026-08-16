import 'dart:async';

import 'package:flutter/material.dart';

import 'app.dart';
import 'services/platform_retrieval_client.dart';
import 'state/app_controller.dart';

/// Week 6 完整离线检索应用入口。
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final controller = AppController(createPlatformRetrievalClient());
  runApp(OfflineRetrievalApp(controller: controller));
  unawaited(controller.initialize());
}