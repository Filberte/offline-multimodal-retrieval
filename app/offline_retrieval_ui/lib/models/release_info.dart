/// Week 8 正式版的单一事实来源，供 UI、测试和文档校验使用。
class ReleaseDisclosure {
  const ReleaseDisclosure({
    required this.id,
    required this.title,
    required this.summary,
  });

  final String id;
  final String title;
  final String summary;
}

class HelpTopic {
  const HelpTopic({
    required this.id,
    required this.title,
    required this.detail,
    required this.action,
  });

  final String id;
  final String title;
  final String detail;
  final String action;
}

class LicenseSummary {
  const LicenseSummary({
    required this.component,
    required this.license,
    required this.distribution,
  });

  final String component;
  final String license;
  final String distribution;
}

abstract final class ReleaseInfo {
  // 产品与平台名称延续 Week 5/6；Week 8 将发布治理升级为正式交付。
  static const productName = '离线多模态检索';
  static const platformDisplayName = 'offline_retrieval_ui';
  static const version = '1.0.0';
  static const releaseDate = '2026-08-08';
  static const protocol = '本地 JSON Lines / stdin-stdout';
  static const privacyMode = '仅本地处理，不开放网络端口';
  static const automatedTestTarget = 600;
  static const projectLicense = 'Apache-2.0';
  static const accessibilityClaim = 'WCAG 2.1 AA 对齐设计（非独立认证）';

  static const disclosures = <ReleaseDisclosure>[
    ReleaseDisclosure(
      id: 'retrieval-only',
      title: '检索系统，不是生成式 AI',
      summary: '返回本地文件的排序结果，不生成答案，也不运行 RAG 或自主代理。',
    ),
    ReleaseDisclosure(
      id: 'ocr-limited',
      title: 'OCR 尚未形成生产能力',
      summary: '图片可使用视觉嵌入检索，但图片中文字的完整 OCR 不在本次发布范围。',
    ),
    ReleaseDisclosure(
      id: 'models-excluded',
      title: '模型权重不随源码分发',
      summary: 'BERT 与 MobileCLIP 等可选模型须由用户按各自条款在本地配置。',
    ),
    ReleaseDisclosure(
      id: 'desktop-primary',
      title: 'Windows 桌面端是实机生产验证基线',
      summary: 'macOS 与 Linux 由跨平台 CI 构建；本地报告中的模拟结果不等同实机执行。',
    ),
  ];

  static const helpTopics = <HelpTopic>[
    HelpTopic(
      id: 'install',
      title: '安装与首次验证',
      detail: '先运行发布预检，再确认后端状态、数据目录和本地模型路径。',
      action: '查看 docs/INSTALLATION.md',
    ),
    HelpTopic(
      id: 'operate',
      title: '索引与搜索',
      detail: '从资料库添加本地路径，完成索引后使用 Ctrl+K 进入搜索。',
      action: '查看 docs/USER_GUIDE.md',
    ),
    HelpTopic(
      id: 'accessibility',
      title: '无障碍使用',
      detail: '支持键盘导航、高对比度、减少动画及 90%–200% 字体缩放。',
      action: '查看 docs/ACCESSIBILITY_GUIDE.md',
    ),
    HelpTopic(
      id: 'diagnostics',
      title: '故障诊断',
      detail: '从系统状态读取降级原因，并使用不含私人内容的合成样例复现。',
      action: '查看 docs/TROUBLESHOOTING.md',
    ),
  ];

  static const licenses = <LicenseSummary>[
    LicenseSummary(
      component: '项目源码',
      license: 'Apache-2.0',
      distribution: '随源码提供 LICENSE 与 NOTICE',
    ),
    LicenseSummary(
      component: 'MobileCLIP 权重',
      license: 'Apple ML Research Terms',
      distribution: '不打包，由用户自行取得',
    ),
    LicenseSummary(
      component: '验证数据集',
      license: '来源特定条款',
      distribution: '不打包，仅提交聚合指标',
    ),
  ];

  static ReleaseDisclosure? disclosureById(String id) {
    for (final item in disclosures) {
      if (item.id == id) return item;
    }
    return null;
  }

  static HelpTopic? helpTopicById(String id) {
    for (final item in helpTopics) {
      if (item.id == id) return item;
    }
    return null;
  }
}
