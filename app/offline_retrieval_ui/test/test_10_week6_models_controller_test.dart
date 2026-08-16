import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/models/retrieval_models.dart';
import 'package:offline_retrieval_ui/services/retrieval_client.dart';
import 'package:offline_retrieval_ui/state/app_controller.dart';

import 'week6_test_support.dart';

void main() {
  group('Week 6 Flutter 数据契约与集成状态', () {
    test('TC-271 RetrievalHit 可以解析 Python JSON 字段', () {
      final hit = RetrievalHit.fromJson(<String, Object?>{
        'item_id': 'a',
        'document_id': 'doc-a',
        'text': 'alpha',
        'score': 0.8,
        'semantic_score': 0.9,
        'keyword_score': 0.6,
        'space': 'text',
        'modality': 'text',
        'source_path': r'C:\library\a.txt',
        'file_name': 'a.txt',
        'content_type': 'text/plain',
        'chunk_index': 2,
      });
      expect((hit.itemId, hit.chunkIndex, hit.score), ('a', 2, 0.8));
    });

    test('TC-272 RetrievalHit 缺失数值字段使用安全默认值', () {
      final hit = RetrievalHit.fromJson(<String, Object?>{});
      expect((hit.score, hit.chunkIndex, hit.modality), (0, 0, 'text'));
    });

    test('TC-273 SearchResponse 可以解析结果列表', () {
      final response = SearchResponse.fromJson(<String, Object?>{
        'query': 'alpha',
        'hits': <Object?>[
          <String, Object?>{'item_id': 'a', 'file_name': 'a.txt'},
        ],
        'elapsed_ms': 1.5,
        'candidate_count': 3,
      });
      expect((response.hits.length, response.candidateCount), (1, 3));
    });

    test('TC-274 BackendHealth 可以解析缓存命中率', () {
      final health = BackendHealth.fromJson(<String, Object?>{
        'status': 'ready',
        'mode': 'integrated-local',
        'offline_only': true,
        'backend_name': 'bert',
        'vector_store': 'chroma',
        'indexed_records': 20,
        'uptime_seconds': 4,
        'embedding_cache': <String, Object?>{'hit_rate': 0.75},
        'query_cache': <String, Object?>{'hit_rate': 0.5},
      });
      expect(
        (health.embeddingCacheHitRate, health.queryCacheHitRate),
        (0.75, 0.5),
      );
    });

    test('TC-275 BackendHealth ready 仅对应就绪状态', () {
      final ready = BackendHealth.fromJson(<String, Object?>{
        'status': 'ready',
      });
      expect(ready.ready, isTrue);
    });

    test('TC-276 IndexingResult 可以解析写入统计', () {
      final result = IndexingResult.fromJson(<String, Object?>{
        'discovered_files': 3,
        'parsed_files': 2,
        'persisted_vectors': 8,
        'success': true,
      });
      expect(
        (result.discoveredFiles, result.parsedFiles, result.persistedVectors),
        (3, 2, 8),
      );
    });

    test('TC-277 IndexingResult 汇总解析与嵌入失败', () {
      final result = IndexingResult.fromJson(<String, Object?>{
        'parse_failures': <Object?>[
          <String, Object?>{'error': 'parse'},
        ],
        'embedding_failures': <Object?>[
          <String, Object?>{'error': 'embed'},
        ],
      });
      expect(result.failureCount, 2);
    });

    test('TC-278 演示客户端明确返回降级健康状态', () async {
      final health = await LocalDemoRetrievalClient().health();
      expect((health.status, health.offlineOnly), ('degraded', true));
    });

    test('TC-279 演示客户端可以加载只读资料库', () async {
      final client = LocalDemoRetrievalClient();
      expect(await client.loadLibrary(), hasLength(5));
    });

    test('TC-280 演示客户端拒绝执行真实索引', () async {
      final result = await LocalDemoRetrievalClient().indexPath('C:/data');
      expect(result.success, isFalse);
      expect(result.message, contains('只读'));
    });

    test('TC-281 控制器从客户端建立初始资料列表', () {
      final controller = AppController(FakeWeek6RetrievalClient());
      expect(controller.libraryItems, hasLength(5));
    });

    test('TC-282 控制器初始化后保存健康状态', () async {
      final controller = AppController(FakeWeek6RetrievalClient());
      await controller.initialize();
      expect(controller.healthStatus?.ready, isTrue);
    });

    test('TC-283 控制器初始化会刷新持久化资料库', () async {
      final client = FakeWeek6RetrievalClient();
      final controller = AppController(client);
      await controller.initialize();
      expect(client.libraryCalls, 1);
    });

    test('TC-284 控制器可以主动刷新后端健康状态', () async {
      final client = FakeWeek6RetrievalClient();
      final controller = AppController(client);
      await controller.refreshHealth();
      expect(client.healthCalls, 1);
    });

    test('TC-285 索引完成后保存结果并刷新状态', () async {
      final client = FakeWeek6RetrievalClient();
      final controller = AppController(client);
      await controller.indexPath(r'C:\library');
      expect(controller.lastIndexingResult?.success, isTrue);
      expect((client.indexCalls, client.libraryCalls, client.healthCalls), (1, 1, 1));
    });
  });
}
