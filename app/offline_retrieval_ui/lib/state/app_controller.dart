import 'dart:async';

import 'package:flutter/foundation.dart';

import '../models/retrieval_models.dart';
import '../services/retrieval_client.dart';

/// 管理导航、检索、索引、后端健康和无障碍设置。
class AppController extends ChangeNotifier {
  AppController(this.client)
    : _libraryItems = List<RetrievalHit>.of(client.libraryItems);

  final RetrievalClient client;

  int _selectedIndex = 0;
  bool _isSearching = false;
  bool _isIndexing = false;
  bool _isLoadingHealth = false;
  bool _initialized = false;
  String _query = '';
  String? _extension;
  bool _includeImages = true;
  SearchResponse? _response;
  BackendHealth? _health;
  IndexingResult? _lastIndexingResult;
  String? _backendError;
  List<RetrievalHit> _libraryItems;
  AccessibilitySettings _accessibility = const AccessibilitySettings();

  int get selectedIndex => _selectedIndex;
  bool get isSearching => _isSearching;
  bool get isIndexing => _isIndexing;
  bool get isLoadingHealth => _isLoadingHealth;
  String get query => _query;
  String? get extension => _extension;
  bool get includeImages => _includeImages;
  SearchResponse? get response => _response;
  BackendHealth? get healthStatus => _health;
  IndexingResult? get lastIndexingResult => _lastIndexingResult;
  String? get backendError => _backendError;
  String get backendModeLabel => client.modeLabel;
  AccessibilitySettings get accessibility => _accessibility;
  List<RetrievalHit> get libraryItems =>
      List<RetrievalHit>.unmodifiable(_libraryItems);

  /// 异步加载后端健康状态和持久化资料库。
  Future<void> initialize() async {
    if (_initialized) {
      return;
    }
    _initialized = true;
    _isLoadingHealth = true;
    notifyListeners();
    try {
      _health = await client.health();
      _libraryItems = await client.loadLibrary();
      _backendError = null;
    } catch (error) {
      _backendError = error.toString();
    } finally {
      _isLoadingHealth = false;
      notifyListeners();
    }
  }

  /// 重新读取本地后端状态。
  Future<void> refreshHealth() async {
    if (_isLoadingHealth) {
      return;
    }
    _isLoadingHealth = true;
    notifyListeners();
    try {
      _health = await client.health();
      _backendError = null;
    } catch (error) {
      _backendError = error.toString();
    } finally {
      _isLoadingHealth = false;
      notifyListeners();
    }
  }

  /// 对文件或目录执行完整索引，并刷新资料库。
  Future<void> indexPath(String path, {bool recursive = true}) async {
    if (_isIndexing || path.trim().isEmpty) {
      return;
    }
    _isIndexing = true;
    _lastIndexingResult = null;
    _backendError = null;
    notifyListeners();
    try {
      _lastIndexingResult = await client.indexPath(
        path.trim(),
        recursive: recursive,
      );
      _libraryItems = await client.loadLibrary();
      _health = await client.health();
      if (_lastIndexingResult?.success != true) {
        _backendError =
            _lastIndexingResult?.message ?? '索引未完成，请检查路径和失败明细。';
      }
    } catch (error) {
      _backendError = error.toString();
    } finally {
      _isIndexing = false;
      notifyListeners();
    }
  }

  /// 切换主界面导航页。
  void selectDestination(int index) {
    if (index == _selectedIndex) {
      return;
    }
    _selectedIndex = index.clamp(0, 2);
    notifyListeners();
  }

  /// 更新当前查询文本。
  void setQuery(String value) {
    if (value == _query) {
      return;
    }
    _query = value;
    notifyListeners();
  }

  /// 设置文件扩展名过滤条件。
  void setExtension(String? value) {
    final normalized = value == null || value.isEmpty ? null : value;
    if (normalized == _extension) {
      return;
    }
    _extension = normalized;
    notifyListeners();
  }

  /// 控制是否在结果中包含图片。
  void setIncludeImages(bool value) {
    if (value == _includeImages) {
      return;
    }
    _includeImages = value;
    notifyListeners();
  }

  /// 调用稳定检索接口并刷新界面结果。
  Future<void> search() async {
    if (_isSearching) {
      return;
    }
    _isSearching = true;
    _backendError = null;
    notifyListeners();
    try {
      _response = await client.search(
        SearchQuery(
          query: _query,
          extension: _extension,
          includeImages: _includeImages,
        ),
      );
    } catch (error) {
      _backendError = error.toString();
      _response = SearchResponse(
        query: _query.trim(),
        hits: const <RetrievalHit>[],
        elapsedMs: 0,
        candidateCount: 0,
        warnings: <String>['检索失败：$error'],
      );
    } finally {
      _isSearching = false;
      notifyListeners();
    }
  }

  /// 开启或关闭高对比度主题。
  void setHighContrast(bool value) {
    _accessibility = _accessibility.copyWith(highContrast: value);
    notifyListeners();
  }

  /// 调整界面字体缩放比例。
  void setFontScale(double value) {
    _accessibility = _accessibility.copyWith(fontScale: value.clamp(0.9, 2.0));
    notifyListeners();
  }

  /// 控制是否减少非必要动画。
  void setReduceMotion(bool value) {
    _accessibility = _accessibility.copyWith(reduceMotion: value);
    notifyListeners();
  }

  /// 恢复默认无障碍显示设置。
  void resetAccessibility() {
    _accessibility = const AccessibilitySettings();
    notifyListeners();
  }

  @override
  void dispose() {
    unawaited(client.close());
    super.dispose();
  }
}