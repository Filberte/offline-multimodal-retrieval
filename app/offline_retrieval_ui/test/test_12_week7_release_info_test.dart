import 'package:flutter_test/flutter_test.dart';
import 'package:offline_retrieval_ui/models/release_info.dart';

void main() {
  group('Week 8 正式发布信息单一事实来源', () {
    test('TC-441 产品名称延续 Week6 界面命名', () {
      expect(ReleaseInfo.productName, '离线多模态检索');
    });

    test('TC-442 平台显示名延续 Week6 工程命名', () {
      expect(ReleaseInfo.platformDisplayName, 'offline_retrieval_ui');
    });

    test('TC-443 正式发布版本为一点零', () {
      expect(ReleaseInfo.version, '1.0.0');
    });

    test('TC-444 发布日期对应 Week8 收尾日', () {
      expect(ReleaseInfo.releaseDate, '2026-08-08');
    });

    test('TC-445 自动化测试目标为六百项', () {
      expect(ReleaseInfo.automatedTestTarget, 600);
    });

    test('TC-446 项目许可证为 Apache 二点零', () {
      expect(ReleaseInfo.projectLicense, 'Apache-2.0');
    });

    test('TC-447 隐私模式声明不开放网络端口', () {
      expect(ReleaseInfo.privacyMode, contains('不开放网络端口'));
    });

    test('TC-448 进程协议明确使用本地标准流', () {
      expect(ReleaseInfo.protocol, contains('stdin-stdout'));
    });

    test('TC-449 无障碍主张明确不是独立认证', () {
      expect(ReleaseInfo.accessibilityClaim, contains('非独立认证'));
    });

    test('TC-450 发布版定义四项能力边界', () {
      expect(ReleaseInfo.disclosures, hasLength(4));
    });

    test('TC-451 能力边界编号唯一', () {
      final ids = ReleaseInfo.disclosures.map((item) => item.id).toSet();
      expect(ids, hasLength(ReleaseInfo.disclosures.length));
    });

    test('TC-452 检索能力边界排除生成式回答', () {
      final item = ReleaseInfo.disclosureById('retrieval-only');
      expect(item?.summary, contains('不生成答案'));
    });

    test('TC-453 OCR 能力边界明确未完成', () {
      final item = ReleaseInfo.disclosureById('ocr-limited');
      expect(item?.title, contains('尚未'));
    });

    test('TC-454 模型能力边界明确不随源码分发', () {
      final item = ReleaseInfo.disclosureById('models-excluded');
      expect(item?.summary, contains('用户'));
    });

    test('TC-455 未知能力边界编号返回空', () {
      expect(ReleaseInfo.disclosureById('unknown'), isNull);
    });

    test('TC-456 发布版提供四个离线帮助主题', () {
      expect(ReleaseInfo.helpTopics, hasLength(4));
    });

    test('TC-457 安装帮助指向随包文档', () {
      expect(
        ReleaseInfo.helpTopicById('install')?.action,
        endsWith('INSTALLATION.md'),
      );
    });

    test('TC-458 未知帮助主题编号返回空', () {
      expect(ReleaseInfo.helpTopicById('unknown'), isNull);
    });

    test('TC-459 许可摘要覆盖源码模型和数据', () {
      final components = ReleaseInfo.licenses
          .map((item) => item.component)
          .join('|');
      expect(
        components,
        allOf(contains('项目源码'), contains('权重'), contains('数据集')),
      );
    });

    test('TC-460 模型权重许可摘要明确不打包', () {
      final model = ReleaseInfo.licenses.firstWhere(
        (item) => item.component.contains('MobileCLIP'),
      );
      expect(model.distribution, contains('不打包'));
    });
  });
}
