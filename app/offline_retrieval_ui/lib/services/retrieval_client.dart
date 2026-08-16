import '../models/retrieval_models.dart';

/// Flutter UI 与本地检索核心之间的稳定适配接口。
abstract interface class RetrievalClient {
  List<RetrievalHit> get libraryItems;

  String get modeLabel;

  Future<BackendHealth> health();

  Future<List<RetrievalHit>> loadLibrary();

  Future<IndexingResult> indexPath(String path, {bool recursive = true});

  Future<SearchResponse> search(SearchQuery request);

  Future<void> close();
}

/// 不支持本地子进程的平台使用的只读演示实现。
class LocalDemoRetrievalClient implements RetrievalClient {
  LocalDemoRetrievalClient({List<RetrievalHit>? items})
    : _items = List<RetrievalHit>.unmodifiable(items ?? demoItems);

  final List<RetrievalHit> _items;

  @override
  List<RetrievalHit> get libraryItems => _items;

  @override
  String get modeLabel => '只读演示';

  @override
  Future<BackendHealth> health() async {
    return const BackendHealth(
      status: 'degraded',
      mode: 'demo',
      offlineOnly: true,
      backendName: 'deterministic-demo',
      vectorStore: 'memory',
      indexedRecords: 5,
      uptimeSeconds: 0,
      issues: <String>['当前平台不支持本地 Python 子进程，已进入只读演示模式。'],
    );
  }

  @override
  Future<List<RetrievalHit>> loadLibrary() async => _items;

  @override
  Future<IndexingResult> indexPath(String path, {bool recursive = true}) async {
    return const IndexingResult(
      discoveredFiles: 0,
      parsedFiles: 0,
      persistedVectors: 0,
      success: false,
      message: '只读演示模式不执行文件索引。',
    );
  }

  @override
  Future<SearchResponse> search(SearchQuery request) async {
    final stopwatch = Stopwatch()..start();
    final normalizedQuery = request.query.trim().toLowerCase();
    if (normalizedQuery.isEmpty) {
      return const SearchResponse(
        query: '',
        hits: <RetrievalHit>[],
        elapsedMs: 0,
        candidateCount: 0,
        warnings: <String>['请输入检索内容。'],
      );
    }

    final queryTerms = _tokenize(normalizedQuery);
    final candidates = _items.where((item) {
      if (!request.includeImages && item.isImage) {
        return false;
      }
      if (request.extension != null &&
          request.extension!.isNotEmpty &&
          item.extension != request.extension!.toLowerCase()) {
        return false;
      }
      if (request.sourcePath != null &&
          request.sourcePath!.isNotEmpty &&
          !item.sourcePath.toLowerCase().contains(
            request.sourcePath!.toLowerCase(),
          )) {
        return false;
      }
      return true;
    }).toList();

    final ranked =
        candidates
            .map((item) => _rescore(item, queryTerms))
            .where((item) => item.score > 0)
            .toList()
          ..sort((left, right) => right.score.compareTo(left.score));
    stopwatch.stop();

    return SearchResponse(
      query: request.query.trim(),
      hits: ranked.take(request.topK).toList(growable: false),
      elapsedMs: stopwatch.elapsedMicroseconds / 1000,
      candidateCount: candidates.length,
    );
  }

  /// 使用可复现的本地词项匹配模拟降级结果。
  RetrievalHit _rescore(RetrievalHit item, Set<String> queryTerms) {
    final searchable = '${item.fileName} ${item.text} ${item.modality}'
        .toLowerCase();
    final matched = queryTerms.where(searchable.contains).length;
    final keyword = queryTerms.isEmpty ? 0.0 : matched / queryTerms.length;
    final semantic = keyword == 0 && _relatedMeaning(searchable, queryTerms)
        ? 0.55
        : keyword;
    final score = (semantic * 0.7) + (keyword * 0.3);
    return RetrievalHit(
      itemId: item.itemId,
      documentId: item.documentId,
      text: item.text,
      score: score.clamp(0, 1),
      semanticScore: semantic.clamp(0, 1),
      keywordScore: keyword.clamp(0, 1),
      space: item.space,
      modality: item.modality,
      sourcePath: item.sourcePath,
      fileName: item.fileName,
      contentType: item.contentType,
      chunkIndex: item.chunkIndex,
      metadata: item.metadata,
    );
  }

  bool _relatedMeaning(String searchable, Set<String> terms) {
    const groups = <Set<String>>[
      <String>{'photo', 'image', 'picture', '图片', '照片'},
      <String>{'vector', 'embedding', 'semantic', '向量', '语义'},
      <String>{'accessibility', 'screen', 'reader', '无障碍', '读屏'},
    ];
    return groups.any(
      (group) =>
          group.any(terms.contains) &&
          group.any((term) => searchable.contains(term)),
    );
  }

  Set<String> _tokenize(String value) => value
      .split(RegExp(r'[\s,.;:!?，。；：！？/\\_-]+'))
      .where((term) => term.isNotEmpty)
      .toSet();

  @override
  Future<void> close() async {}
}

/// 与前五周样例语义一致的离线演示资料。
const demoItems = <RetrievalHit>[
  RetrievalHit(
    itemId: 'doc-vector:chunk:0',
    documentId: 'doc-vector',
    text:
        'A local vector database stores embeddings and returns nearest '
        'neighbors for semantic search.',
    score: 1,
    semanticScore: 1,
    keywordScore: 1,
    space: 'bert-base-mean-pool-v1',
    modality: 'text',
    sourcePath: r'C:\LocalLibrary\documents\vector_database.txt',
    fileName: 'vector_database.txt',
    contentType: 'text/plain',
    chunkIndex: 0,
  ),
  RetrievalHit(
    itemId: 'doc-ranking:chunk:0',
    documentId: 'doc-ranking',
    text: 'Hybrid ranking combines keyword matching and embedding similarity.',
    score: 0.88,
    semanticScore: 0.9,
    keywordScore: 0.82,
    space: 'bert-base-mean-pool-v1',
    modality: 'text',
    sourcePath: r'C:\LocalLibrary\documents\hybrid_ranking.pdf',
    fileName: 'hybrid_ranking.pdf',
    contentType: 'application/pdf',
    chunkIndex: 0,
  ),
  RetrievalHit(
    itemId: 'doc-accessibility:chunk:0',
    documentId: 'doc-accessibility',
    text:
        'Keyboard navigation, screen reader labels and high contrast '
        'support improve accessible search workflows.',
    score: 0.84,
    semanticScore: 0.86,
    keywordScore: 0.8,
    space: 'bert-base-mean-pool-v1',
    modality: 'text',
    sourcePath: r'C:\LocalLibrary\documents\accessibility_guide.docx',
    fileName: 'accessibility_guide.docx',
    contentType:
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    chunkIndex: 0,
  ),
  RetrievalHit(
    itemId: 'image-forest',
    documentId: 'image-forest',
    text: 'Forest trail reference photograph with trees and a walking path.',
    score: 0.76,
    semanticScore: 0.8,
    keywordScore: 0.67,
    space: 'mobileclip-s1-shared-v1',
    modality: 'image',
    sourcePath: r'C:\LocalLibrary\images\forest_trail.jpg',
    fileName: 'forest_trail.jpg',
    contentType: 'image/jpeg',
    chunkIndex: 0,
  ),
  RetrievalHit(
    itemId: 'image-city',
    documentId: 'image-city',
    text: 'Night city skyline photo used for cross-modal retrieval testing.',
    score: 0.72,
    semanticScore: 0.75,
    keywordScore: 0.65,
    space: 'mobileclip-s1-shared-v1',
    modality: 'image',
    sourcePath: r'C:\LocalLibrary\images\city_night.png',
    fileName: 'city_night.png',
    contentType: 'image/png',
    chunkIndex: 0,
  ),
];