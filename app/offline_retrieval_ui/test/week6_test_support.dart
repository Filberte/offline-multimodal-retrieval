import 'package:offline_retrieval_ui/models/retrieval_models.dart';
import 'package:offline_retrieval_ui/services/retrieval_client.dart';

class FakeWeek6RetrievalClient implements RetrievalClient {
  FakeWeek6RetrievalClient({
    List<RetrievalHit>? items,
    BackendHealth? healthResponse,
    IndexingResult? indexResponse,
    SearchResponse? searchResponse,
  }) : _items = List<RetrievalHit>.of(items ?? demoItems),
       healthResponse =
           healthResponse ??
           const BackendHealth(
             status: 'ready',
             mode: 'integrated-local',
             offlineOnly: true,
             backendName: 'test-backend',
             vectorStore: 'memory',
             indexedRecords: 5,
             uptimeSeconds: 1,
           ),
       indexResponse =
           indexResponse ??
           const IndexingResult(
             discoveredFiles: 1,
             parsedFiles: 1,
             persistedVectors: 1,
             success: true,
           ),
       searchResponse =
           searchResponse ??
           SearchResponse(
             query: 'vector',
             hits: <RetrievalHit>[demoItems.first],
             elapsedMs: 1,
             candidateCount: 1,
           );

  final List<RetrievalHit> _items;
  BackendHealth healthResponse;
  IndexingResult indexResponse;
  SearchResponse searchResponse;
  bool throwOnSearch = false;
  int healthCalls = 0;
  int libraryCalls = 0;
  int indexCalls = 0;
  int searchCalls = 0;
  int closeCalls = 0;
  String? indexedPath;

  @override
  List<RetrievalHit> get libraryItems =>
      List<RetrievalHit>.unmodifiable(_items);

  @override
  String get modeLabel => '本地集成';

  @override
  Future<BackendHealth> health() async {
    healthCalls += 1;
    return healthResponse;
  }

  @override
  Future<List<RetrievalHit>> loadLibrary() async {
    libraryCalls += 1;
    return libraryItems;
  }

  @override
  Future<IndexingResult> indexPath(
    String path, {
    bool recursive = true,
  }) async {
    indexCalls += 1;
    indexedPath = path;
    return indexResponse;
  }

  @override
  Future<SearchResponse> search(SearchQuery request) async {
    searchCalls += 1;
    if (throwOnSearch) {
      throw StateError('planned search failure');
    }
    return SearchResponse(
      query: request.query.trim(),
      hits: searchResponse.hits,
      elapsedMs: searchResponse.elapsedMs,
      candidateCount: searchResponse.candidateCount,
      warnings: searchResponse.warnings,
    );
  }

  @override
  Future<void> close() async {
    closeCalls += 1;
  }
}
