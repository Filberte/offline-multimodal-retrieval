import 'dart:async';
import 'dart:convert';
import 'dart:io';

import '../models/retrieval_models.dart';
import 'retrieval_client.dart';

RetrievalClient createPlatformRetrievalClient() =>
    LocalProcessRetrievalClient();

/// 通过标准输入输出与本地 Python 核心通信，不开放网络端口。
class LocalProcessRetrievalClient implements RetrievalClient {
  LocalProcessRetrievalClient({
    LocalDemoRetrievalClient? fallback,
    this.requestTimeout = const Duration(seconds: 90),
  }) : _fallback = fallback ?? LocalDemoRetrievalClient(),
       _items = List<RetrievalHit>.of(
         (fallback ?? LocalDemoRetrievalClient()).libraryItems,
       );

  final LocalDemoRetrievalClient _fallback;
  final Duration requestTimeout;
  final Map<String, Completer<Map<String, Object?>>> _pending =
      <String, Completer<Map<String, Object?>>>{};
  List<RetrievalHit> _items;
  Process? _process;
  StreamSubscription<String>? _stdoutSubscription;
  StreamSubscription<String>? _stderrSubscription;
  int _requestSequence = 0;
  bool _disabled = false;
  String? _lastError;

  @override
  List<RetrievalHit> get libraryItems => List<RetrievalHit>.unmodifiable(_items);

  @override
  String get modeLabel => _disabled ? '只读演示' : '本地集成';

  @override
  Future<BackendHealth> health() async {
    if (_disabled) {
      return _degradedHealth();
    }
    try {
      return BackendHealth.fromJson(await _request('health'));
    } catch (error) {
      _disable(error);
      return _degradedHealth();
    }
  }

  @override
  Future<List<RetrievalHit>> loadLibrary() async {
    if (_disabled) {
      return libraryItems;
    }
    try {
      final response = await _request('library');
      final rawItems = response['items'];
      if (rawItems is List) {
        final loaded = rawItems
            .whereType<Map>()
            .map(
              (item) => RetrievalHit.fromJson(
                item.map((key, value) => MapEntry(key.toString(), value)),
              ),
            )
            .toList(growable: false);
        if (loaded.isNotEmpty) {
          _items = loaded;
        }
      }
    } catch (error) {
      _disable(error);
    }
    return libraryItems;
  }

  @override
  Future<IndexingResult> indexPath(
    String path, {
    bool recursive = true,
  }) async {
    if (_disabled) {
      return _fallback.indexPath(path, recursive: recursive);
    }
    try {
      final isDirectory = await Directory(path).exists();
      final response = isDirectory
          ? await _request(
              'index_directory',
              <String, Object?>{'path': path, 'recursive': recursive},
            )
          : await _request(
              'index_paths',
              <String, Object?>{
                'paths': <String>[path],
                'continue_on_error': true,
              },
            );
      final result = IndexingResult.fromJson(response);
      await loadLibrary();
      return result;
    } catch (error) {
      return IndexingResult(
        discoveredFiles: 0,
        parsedFiles: 0,
        persistedVectors: 0,
        success: false,
        message: error.toString(),
      );
    }
  }

  @override
  Future<SearchResponse> search(SearchQuery request) async {
    if (_disabled) {
      return _fallbackSearch(request);
    }
    try {
      return SearchResponse.fromJson(
        await _request('search', request.toJson()),
      );
    } catch (error) {
      _disable(error);
      return _fallbackSearch(request);
    }
  }

  Future<Map<String, Object?>> _request(
    String command, [
    Map<String, Object?> data = const <String, Object?>{},
  ]) async {
    final process = await _ensureProcess();
    final requestId = '${++_requestSequence}';
    final completer = Completer<Map<String, Object?>>();
    _pending[requestId] = completer;
    process.stdin.writeln(
      jsonEncode(<String, Object?>{
        'request_id': requestId,
        'command': command,
        'data': data,
      }),
    );
    await process.stdin.flush();
    return completer.future.timeout(
      requestTimeout,
      onTimeout: () {
        _pending.remove(requestId);
        throw TimeoutException('本地检索后端响应超时。', requestTimeout);
      },
    );
  }

  Future<Process> _ensureProcess() async {
    if (_disabled) {
      throw StateError(_lastError ?? '本地检索后端不可用。');
    }
    final existing = _process;
    if (existing != null) {
      return existing;
    }
    final root = _locateProductRoot();
    if (root == null) {
      throw StateError('未找到正式版本地检索后端。');
    }
    final script = File(_join(root.path, 'run_backend.py'));
    final forcePython =
        Platform.environment['OFFLINE_RETRIEVAL_FORCE_PYTHON'] == '1';
    final packagedBackend = forcePython ? null : _locatePackagedBackend(root);
    final configuredPython = Platform.environment['OFFLINE_RETRIEVAL_PYTHON'];
    final workspacePython = File(
      _join(root.parent.path, '.venv_week3', 'Scripts', 'python.exe'),
    );
    final python = configuredPython?.trim().isNotEmpty == true
        ? configuredPython!
        : workspacePython.existsSync()
        ? workspacePython.path
        : 'python';

    final environment = Map<String, String>.of(Platform.environment);
    environment['PYTHONIOENCODING'] = 'utf-8';
    final executable = packagedBackend?.path ?? python;
    final arguments = packagedBackend == null ? <String>[script.path] : <String>[];
    final process = await Process.start(
      executable,
      arguments,
      workingDirectory: root.path,
      environment: environment,
      runInShell: packagedBackend == null && python == 'python',
    );
    _process = process;
    _stdoutSubscription = process.stdout
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen(_handleLine, onError: _handleProcessError);
    _stderrSubscription = process.stderr
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen((line) {
          if (line.trim().isNotEmpty) {
            _lastError = line.trim();
          }
        });
    unawaited(
      process.exitCode.then((code) {
        if (_process == process) {
          _process = null;
          if (code != 0) {
            _failPending(StateError('本地检索后端异常退出，代码 $code。'));
          }
        }
      }),
    );
    return process;
  }

  void _handleLine(String line) {
    try {
      final decoded = jsonDecode(line);
      if (decoded is! Map) {
        throw const FormatException('后端响应不是 JSON 对象。');
      }
      final response = decoded.map(
        (key, value) => MapEntry(key.toString(), value),
      );
      final requestId = response['request_id']?.toString() ?? '';
      final completer = _pending.remove(requestId);
      if (completer == null) {
        return;
      }
      if (response['ok'] != true) {
        final error = response['error'];
        final details = error is Map
            ? error['message']?.toString()
            : error?.toString();
        completer.completeError(StateError(details ?? '本地后端请求失败。'));
        return;
      }
      completer.complete(_objectMap(response['data']));
    } catch (error) {
      _handleProcessError(error);
    }
  }

  void _handleProcessError(Object error) {
    _lastError = error.toString();
    _failPending(error);
  }

  void _failPending(Object error) {
    for (final completer in _pending.values) {
      if (!completer.isCompleted) {
        completer.completeError(error);
      }
    }
    _pending.clear();
  }

  void _disable(Object error) {
    _lastError = error.toString();
    _disabled = true;
  }

  Future<SearchResponse> _fallbackSearch(SearchQuery request) async {
    final response = await _fallback.search(request);
    return SearchResponse(
      query: response.query,
      hits: response.hits,
      elapsedMs: response.elapsedMs,
      candidateCount: response.candidateCount,
      warnings: <String>[
        ...response.warnings,
        '本地集成后端暂不可用，已切换只读演示模式。',
      ],
    );
  }

  BackendHealth _degradedHealth() {
    return BackendHealth(
      status: 'degraded',
      mode: 'demo-fallback',
      offlineOnly: true,
      backendName: 'deterministic-demo',
      vectorStore: 'memory',
      indexedRecords: _items.length,
      uptimeSeconds: 0,
      issues: <String>[
        _lastError ?? '本地集成后端不可用，已切换只读演示模式。',
      ],
    );
  }

  Directory? _locateProductRoot() {
    final configured =
        Platform.environment['OFFLINE_RETRIEVAL_ROOT']?.trim();
    if (configured != null && configured.isNotEmpty) {
      final directory = Directory(configured);
      if (File(_join(directory.path, 'run_backend.py')).existsSync()) {
        return directory;
      }
    }
    for (final start in <Directory>[
      Directory.current,
      File(Platform.resolvedExecutable).parent,
    ]) {
      var current = start.absolute;
      for (var depth = 0; depth < 10; depth++) {
        if (File(_join(current.path, 'run_backend.py')).existsSync()) {
          return current;
        }
        final child = Directory(_join(current.path, 'Week8_Deliverables'));
        if (File(_join(child.path, 'run_backend.py')).existsSync()) {
          return child;
        }
        if (current.parent.path == current.path) {
          break;
        }
        current = current.parent;
      }
    }
    return null;
  }

  File? _locatePackagedBackend(Directory root) {
    final executableName = Platform.isWindows
        ? 'offline_retrieval_backend.exe'
        : 'offline_retrieval_backend';
    final candidates = <File>[
      File(_join(root.path, 'backend', executableName)),
      File(_join(root.path, executableName)),
      File(
        _join(
          File(Platform.resolvedExecutable).parent.path,
          'backend',
          executableName,
        ),
      ),
    ];
    for (final candidate in candidates) {
      if (candidate.existsSync()) {
        return candidate;
      }
    }
    return null;
  }

  @override
  Future<void> close() async {
    final process = _process;
    if (process == null) {
      return;
    }
    try {
      await _request('shutdown').timeout(const Duration(seconds: 2));
    } catch (_) {
      process.kill();
    }
    await _stdoutSubscription?.cancel();
    await _stderrSubscription?.cancel();
    _process = null;
  }
}

Map<String, Object?> _objectMap(Object? value) {
  if (value is! Map) {
    return <String, Object?>{};
  }
  return value.map((key, item) => MapEntry(key.toString(), item));
}

String _join(String first, [String? second, String? third, String? fourth]) {
  final values = <String>[
    first,
    ?second,
    ?third,
    ?fourth,
  ];
  return values.join(Platform.pathSeparator);
}
