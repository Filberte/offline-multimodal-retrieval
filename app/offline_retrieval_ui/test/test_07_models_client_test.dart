import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/models/retrieval_models.dart';
import 'package:offline_retrieval_ui/services/retrieval_client.dart';

void main() {
  group('Week 5 数据模型与本地适配层', () {
    test('TC-101 SearchQuery 序列化保留查询文本', () {
      const query = SearchQuery(query: 'vector database');
      expect(query.toJson()['query'], 'vector database');
    });

    test('TC-102 SearchQuery 默认返回十项结果', () {
      const query = SearchQuery(query: 'vector');
      expect(query.topK, 10);
    });

    test('TC-103 SearchQuery 序列化扩展名过滤条件', () {
      const query = SearchQuery(query: 'guide', extension: 'pdf');
      expect(query.toJson()['extension'], 'pdf');
    });

    test('TC-104 RetrievalHit 正确解析文件扩展名', () {
      expect(demoItems.first.extension, 'txt');
    });

    test('TC-105 RetrievalHit 对无扩展名文件返回空值', () {
      final item = _copyHit(demoItems.first, fileName: 'README');
      expect(item.extension, isEmpty);
    });

    test('TC-106 RetrievalHit 可以识别图片模态', () {
      expect(demoItems.where((item) => item.isImage), hasLength(2));
    });

    test('TC-107 SearchResponse 默认没有警告', () {
      const response = SearchResponse(
        query: 'test',
        hits: <RetrievalHit>[],
        elapsedMs: 1,
        candidateCount: 0,
      );
      expect(response.warnings, isEmpty);
    });

    test('TC-108 AccessibilitySettings 默认符合标准显示', () {
      const settings = AccessibilitySettings();
      expect(settings.highContrast, isFalse);
      expect(settings.fontScale, 1);
      expect(settings.reduceMotion, isFalse);
    });

    test('TC-109 AccessibilitySettings 可更新高对比度', () {
      const settings = AccessibilitySettings();
      expect(settings.copyWith(highContrast: true).highContrast, isTrue);
    });

    test('TC-110 AccessibilitySettings 可更新字体缩放', () {
      const settings = AccessibilitySettings();
      expect(settings.copyWith(fontScale: 1.4).fontScale, 1.4);
    });

    test('TC-111 AccessibilitySettings 可更新减少动画', () {
      const settings = AccessibilitySettings();
      expect(settings.copyWith(reduceMotion: true).reduceMotion, isTrue);
    });

    test('TC-112 本地演示资料库包含五种样例记录', () {
      final client = LocalDemoRetrievalClient();
      expect(client.libraryItems, hasLength(5));
    });

    test('TC-113 本地检索返回向量数据库结果', () async {
      final client = LocalDemoRetrievalClient();
      final response = await client.search(
        const SearchQuery(query: 'vector database'),
      );
      expect(response.hits.first.fileName, 'vector_database.txt');
    });

    test('TC-114 本地检索不区分英文大小写', () async {
      final client = LocalDemoRetrievalClient();
      final response = await client.search(const SearchQuery(query: 'VECTOR'));
      expect(response.hits, isNotEmpty);
    });

    test('TC-115 本地检索支持 PDF 扩展名过滤', () async {
      final client = LocalDemoRetrievalClient();
      final response = await client.search(
        const SearchQuery(query: 'ranking', extension: 'pdf'),
      );
      expect(response.hits, hasLength(1));
      expect(response.hits.single.extension, 'pdf');
    });

    test('TC-116 本地检索可以排除图片结果', () async {
      final client = LocalDemoRetrievalClient();
      final response = await client.search(
        const SearchQuery(query: 'photo', includeImages: false),
      );
      expect(response.hits.where((item) => item.isImage), isEmpty);
    });

    test('TC-117 本地检索可以返回跨模态图片', () async {
      final client = LocalDemoRetrievalClient();
      final response = await client.search(
        const SearchQuery(query: 'photo', includeImages: true),
      );
      expect(response.hits.where((item) => item.isImage), isNotEmpty);
    });

    test('TC-118 本地检索遵守 topK 上限', () async {
      final client = LocalDemoRetrievalClient();
      final response = await client.search(
        const SearchQuery(query: 'local', topK: 1),
      );
      expect(response.hits.length, lessThanOrEqualTo(1));
    });

    test('TC-119 空查询返回可读警告', () async {
      final client = LocalDemoRetrievalClient();
      final response = await client.search(const SearchQuery(query: '  '));
      expect(response.warnings.single, contains('请输入'));
    });

    test('TC-120 无匹配查询返回空结果', () async {
      final client = LocalDemoRetrievalClient();
      final response = await client.search(
        const SearchQuery(query: 'nonexistent-token'),
      );
      expect(response.hits, isEmpty);
    });
  });
}

RetrievalHit _copyHit(RetrievalHit source, {required String fileName}) {
  return RetrievalHit(
    itemId: source.itemId,
    documentId: source.documentId,
    text: source.text,
    score: source.score,
    semanticScore: source.semanticScore,
    keywordScore: source.keywordScore,
    space: source.space,
    modality: source.modality,
    sourcePath: source.sourcePath,
    fileName: fileName,
    contentType: source.contentType,
    chunkIndex: source.chunkIndex,
  );
}
