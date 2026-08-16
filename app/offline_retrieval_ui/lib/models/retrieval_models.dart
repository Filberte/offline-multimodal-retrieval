/// Week 4 核心检索接口在 Flutter 端的查询映射。
class SearchQuery {
  const SearchQuery({
    required this.query,
    this.topK = 10,
    this.extension,
    this.sourcePath,
    this.includeImages = true,
  });

  final String query;
  final int topK;
  final String? extension;
  final String? sourcePath;
  final bool includeImages;

  /// 将查询转换为本地接口可直接传输的字段。
  Map<String, Object?> toJson() => <String, Object?>{
    'query': query,
    'top_k': topK,
    'extension': extension,
    'source_path': sourcePath,
    'include_images': includeImages,
  };
}

/// 与 Week 4 RetrievalHit 字段保持一致的界面结果模型。
class RetrievalHit {
  const RetrievalHit({
    required this.itemId,
    required this.documentId,
    required this.text,
    required this.score,
    required this.semanticScore,
    required this.keywordScore,
    required this.space,
    required this.modality,
    required this.sourcePath,
    required this.fileName,
    required this.contentType,
    required this.chunkIndex,
    this.metadata = const <String, Object?>{},
  });

  factory RetrievalHit.fromJson(Map<String, Object?> json) {
    return RetrievalHit(
      itemId: json['item_id']?.toString() ?? '',
      documentId: json['document_id']?.toString() ?? '',
      text: json['text']?.toString() ?? '',
      score: _asDouble(json['score']),
      semanticScore: _asDouble(json['semantic_score']),
      keywordScore: _asDouble(json['keyword_score']),
      space: json['space']?.toString() ?? '',
      modality: json['modality']?.toString() ?? 'text',
      sourcePath: json['source_path']?.toString() ?? '',
      fileName: json['file_name']?.toString() ?? '',
      contentType: json['content_type']?.toString() ?? '',
      chunkIndex: _asInt(json['chunk_index']) ?? 0,
      metadata: _asObjectMap(json['metadata']),
    );
  }

  final String itemId;
  final String documentId;
  final String text;
  final double score;
  final double semanticScore;
  final double keywordScore;
  final String space;
  final String modality;
  final String sourcePath;
  final String fileName;
  final String contentType;
  final int chunkIndex;
  final Map<String, Object?> metadata;

  /// 根据文件类型返回界面图标。
  String get extension {
    final index = fileName.lastIndexOf('.');
    return index < 0 ? '' : fileName.substring(index + 1).toLowerCase();
  }

  bool get isImage => modality == 'image';
}

/// 与 Week 4 SearchResponse 字段保持一致的界面响应模型。
class SearchResponse {
  const SearchResponse({
    required this.query,
    required this.hits,
    required this.elapsedMs,
    required this.candidateCount,
    this.warnings = const <String>[],
  });

  factory SearchResponse.fromJson(Map<String, Object?> json) {
    final rawHits = json['hits'];
    final hits = rawHits is List
        ? rawHits
              .whereType<Map>()
              .map(
                (item) => RetrievalHit.fromJson(
                  item.map((key, value) => MapEntry(key.toString(), value)),
                ),
              )
              .toList(growable: false)
        : <RetrievalHit>[];
    return SearchResponse(
      query: json['query']?.toString() ?? '',
      hits: hits,
      elapsedMs: _asDouble(json['elapsed_ms']),
      candidateCount: _asInt(json['candidate_count']) ?? 0,
      warnings: _asStringList(json['warnings']),
    );
  }

  final String query;
  final List<RetrievalHit> hits;
  final double elapsedMs;
  final int candidateCount;
  final List<String> warnings;
}

/// 本地后端可用性、缓存和隐私边界。
class BackendHealth {
  const BackendHealth({
    required this.status,
    required this.mode,
    required this.offlineOnly,
    required this.backendName,
    required this.vectorStore,
    required this.indexedRecords,
    required this.uptimeSeconds,
    this.embeddingCacheHitRate = 0,
    this.queryCacheHitRate = 0,
    this.issues = const <String>[],
  });

  factory BackendHealth.fromJson(Map<String, Object?> json) {
    final embeddingCache = _asObjectMap(json['embedding_cache']);
    final queryCache = _asObjectMap(json['query_cache']);
    return BackendHealth(
      status: json['status']?.toString() ?? 'degraded',
      mode: json['mode']?.toString() ?? 'unknown',
      offlineOnly: json['offline_only'] == true,
      backendName: json['backend_name']?.toString() ?? 'unknown',
      vectorStore: json['vector_store']?.toString() ?? 'unknown',
      indexedRecords: _asInt(json['indexed_records']) ?? 0,
      uptimeSeconds: _asDouble(json['uptime_seconds']),
      embeddingCacheHitRate: _asDouble(embeddingCache['hit_rate']),
      queryCacheHitRate: _asDouble(queryCache['hit_rate']),
      issues: _asStringList(json['issues']),
    );
  }

  final String status;
  final String mode;
  final bool offlineOnly;
  final String backendName;
  final String vectorStore;
  final int indexedRecords;
  final double uptimeSeconds;
  final double embeddingCacheHitRate;
  final double queryCacheHitRate;
  final List<String> issues;

  bool get ready => status == 'ready';
}

/// 单次文件或目录索引操作的可观察结果。
class IndexingResult {
  const IndexingResult({
    required this.discoveredFiles,
    required this.parsedFiles,
    required this.persistedVectors,
    required this.success,
    this.parseFailures = const <String>[],
    this.embeddingFailures = const <String>[],
    this.message,
  });

  factory IndexingResult.fromJson(Map<String, Object?> json) {
    return IndexingResult(
      discoveredFiles: _asInt(json['discovered_files']) ?? 0,
      parsedFiles: _asInt(json['parsed_files']) ?? 0,
      persistedVectors: _asInt(json['persisted_vectors']) ?? 0,
      success: json['success'] == true,
      parseFailures: _failureMessages(json['parse_failures']),
      embeddingFailures: _failureMessages(json['embedding_failures']),
    );
  }

  final int discoveredFiles;
  final int parsedFiles;
  final int persistedVectors;
  final bool success;
  final List<String> parseFailures;
  final List<String> embeddingFailures;
  final String? message;

  int get failureCount => parseFailures.length + embeddingFailures.length;
}

/// 用户可以调整的无障碍显示参数。
class AccessibilitySettings {
  const AccessibilitySettings({
    this.highContrast = false,
    this.fontScale = 1.0,
    this.reduceMotion = false,
  });

  final bool highContrast;
  final double fontScale;
  final bool reduceMotion;

  AccessibilitySettings copyWith({
    bool? highContrast,
    double? fontScale,
    bool? reduceMotion,
  }) {
    return AccessibilitySettings(
      highContrast: highContrast ?? this.highContrast,
      fontScale: fontScale ?? this.fontScale,
      reduceMotion: reduceMotion ?? this.reduceMotion,
    );
  }
}

double _asDouble(Object? value) => value is num
    ? value.toDouble()
    : double.tryParse(value?.toString() ?? '') ?? 0;

int? _asInt(Object? value) =>
    value is int ? value : int.tryParse(value?.toString() ?? '');

Map<String, Object?> _asObjectMap(Object? value) {
  if (value is! Map) {
    return <String, Object?>{};
  }
  return value.map((key, item) => MapEntry(key.toString(), item));
}

List<String> _asStringList(Object? value) =>
    value is List ? value.map((item) => item.toString()).toList() : <String>[];

List<String> _failureMessages(Object? value) {
  if (value is! List) {
    return <String>[];
  }
  return value.map((item) {
    if (item is Map) {
      return item['error']?.toString() ?? item.toString();
    }
    return item.toString();
  }).toList(growable: false);
}