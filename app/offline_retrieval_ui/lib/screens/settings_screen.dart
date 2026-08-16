import 'package:flutter/material.dart';

import '../design_system/app_theme.dart';
import '../design_system/app_icons.dart';
import '../design_system/responsive_layout.dart';
import '../models/release_info.dart';
import '../state/app_controller.dart';
import '../widgets/layout_widgets.dart';

/// 设置与支持页，集中控制无障碍偏好并公开版本、隐私和能力边界。
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({required this.controller, super.key});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final settings = controller.accessibility;
    return ListView(
      key: const ValueKey<String>('settings-screen'),
      padding: ResponsiveLayout.pagePaddingFor(
        MediaQuery.sizeOf(context).width,
      ),
      children: [
        ContentWidth(
          maxWidth: 1040,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              PageHeader(
                eyebrow: 'PRODUCTION RELEASE',
                title: '设置、无障碍与支持',
                subtitle: '调整阅读体验，并核对版本、隐私边界、已知限制和帮助入口。',
                actions: [
                  OutlinedButton.icon(
                    key: const ValueKey<String>('reset-accessibility'),
                    onPressed: controller.resetAccessibility,
                    icon: const AppIcon(AppGlyph.restart),
                    label: const Text('恢复默认设置'),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),
              _SystemStatusCard(controller: controller),
              const SizedBox(height: AppSpacing.xl),
              SectionCard(
                title: '无障碍设置',
                subtitle: '根据视力、阅读习惯和系统偏好调整界面。',
                child: Column(
                  children: [
                    _SettingSwitch(
                      key: const ValueKey<String>('high-contrast-toggle'),
                      icon: AppGlyph.contrast,
                      title: '高对比度模式',
                      subtitle: '使用黑色背景、白色文字和黄色焦点，增强关键控件辨识度。',
                      value: settings.highContrast,
                      onChanged: controller.setHighContrast,
                    ),
                    const Divider(),
                    _SettingSwitch(
                      key: const ValueKey<String>('reduce-motion-toggle'),
                      icon: AppGlyph.reduceMotion,
                      title: '减少动画',
                      subtitle: '关闭非必要的页面过渡和装饰性动效。',
                      value: settings.reduceMotion,
                      onChanged: controller.setReduceMotion,
                    ),
                    const Divider(),
                    _FontScaleSetting(
                      value: settings.fontScale,
                      onChanged: controller.setFontScale,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.xl),
              SectionCard(
                title: '键盘快捷键',
                subtitle: '无需鼠标即可完成导航、搜索和控件操作。',
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final columns =
                        constraints.maxWidth >=
                                AppBreakpoints.twoColumnSettings &&
                            !ResponsiveLayout.usesLargeText(context)
                        ? 2
                        : 1;
                    final width = columns == 2
                        ? (constraints.maxWidth - AppSpacing.m) / 2
                        : constraints.maxWidth;
                    return Wrap(
                      spacing: AppSpacing.m,
                      runSpacing: AppSpacing.s,
                      children: [
                        for (final shortcut in _shortcuts)
                          SizedBox(
                            width: width,
                            child: _ShortcutRow(
                              keys: shortcut.keys,
                              action: shortcut.action,
                            ),
                          ),
                      ],
                    );
                  },
                ),
              ),
              const SizedBox(height: AppSpacing.xl),
              const _AccessibilitySummary(),
              const SizedBox(height: AppSpacing.xl),
              const _ReleaseAboutCard(),
              const SizedBox(height: AppSpacing.xl),
              const _HelpTopicGrid(),
            ],
          ),
        ),
      ],
    );
  }
}

class _SystemStatusCard extends StatelessWidget {
  const _SystemStatusCard({required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final health = controller.healthStatus;
    final ready = health?.ready == true;
    final issueText =
        controller.backendError ??
        (health?.issues.isNotEmpty == true ? health!.issues.join('；') : null);
    final metrics = <Widget>[
      _StatusMetric(
        label: '后端状态',
        value: controller.isLoadingHealth
            ? '正在检查'
            : ready
            ? '已就绪'
            : '已降级',
      ),
      _StatusMetric(label: '运行模式', value: controller.backendModeLabel),
      _StatusMetric(label: '嵌入模型', value: health?.backendName ?? '等待后端响应'),
      _StatusMetric(label: '向量存储', value: health?.vectorStore ?? '等待后端响应'),
      _StatusMetric(
        label: '已索引向量',
        value: (health?.indexedRecords ?? 0).toString(),
      ),
      _StatusMetric(
        label: '数据边界',
        value: health?.offlineOnly == false ? '需要检查' : '仅本地',
      ),
    ];
    return SectionCard(
      title: '系统与本地隐私状态',
      subtitle: '桌面端通过本地进程桥接核心检索服务，不开放网络端口。',
      trailing: IconButton(
        key: const ValueKey<String>('refresh-backend-health'),
        tooltip: '刷新后端状态',
        onPressed: controller.isLoadingHealth ? null : controller.refreshHealth,
        icon: controller.isLoadingHealth
            ? const SizedBox.square(
                dimension: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const AppIcon(AppGlyph.refresh),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          LayoutBuilder(
            builder: (context, constraints) {
              final columns =
                  constraints.maxWidth >= AppBreakpoints.twoColumnSettings &&
                      !ResponsiveLayout.usesLargeText(context)
                  ? 3
                  : constraints.maxWidth >= 480
                  ? 2
                  : 1;
              final width =
                  (constraints.maxWidth - AppSpacing.s * (columns - 1)) /
                  columns;
              return Wrap(
                spacing: AppSpacing.s,
                runSpacing: AppSpacing.s,
                children: [
                  for (final metric in metrics)
                    SizedBox(width: width, child: metric),
                ],
              );
            },
          ),
          if (issueText != null) ...[
            const SizedBox(height: AppSpacing.m),
            Semantics(
              liveRegion: true,
              child: Container(
                key: const ValueKey<String>('backend-health-issue'),
                width: double.infinity,
                padding: const EdgeInsets.all(AppSpacing.s),
                decoration: BoxDecoration(
                  color: Theme.of(context).brightness == Brightness.dark
                      ? Theme.of(context).colorScheme.surface
                      : const Color(0xFFFFF4E5),
                  border: Border.all(
                    color: Theme.of(context).colorScheme.error,
                  ),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(issueText),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _StatusMetric extends StatelessWidget {
  const _StatusMetric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 76),
      padding: const EdgeInsets.all(AppSpacing.s),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLowest,
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: AppSpacing.xxs),
          Text(
            value,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.titleSmall,
          ),
        ],
      ),
    );
  }
}

class _SettingSwitch extends StatelessWidget {
  const _SettingSwitch({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
    super.key,
  });

  final AppGlyph icon;
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final copy = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: AppSpacing.xxs),
        Text(subtitle),
      ],
    );
    return LayoutBuilder(
      builder: (context, constraints) {
        final stacked =
            constraints.maxWidth < 360 ||
            (ResponsiveLayout.usesLargeText(context) &&
                constraints.maxWidth < AppBreakpoints.stackedSearchControls);
        if (stacked) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: AppSpacing.s),
            child: Column(
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _SettingIcon(icon: icon),
                    const SizedBox(width: AppSpacing.s),
                    Expanded(child: copy),
                  ],
                ),
                const SizedBox(height: AppSpacing.xs),
                Align(
                  alignment: Alignment.centerRight,
                  child: Semantics(
                    label: '$title，${value ? '已开启' : '已关闭'}',
                    child: Switch(value: value, onChanged: onChanged),
                  ),
                ),
              ],
            ),
          );
        }
        return SwitchListTile(
          contentPadding: EdgeInsets.zero,
          secondary: _SettingIcon(icon: icon),
          title: Text(title, style: Theme.of(context).textTheme.titleMedium),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: AppSpacing.xxs),
            child: Text(subtitle),
          ),
          value: value,
          onChanged: onChanged,
        );
      },
    );
  }
}

class _FontScaleSetting extends StatelessWidget {
  const _FontScaleSetting({required this.value, required this.onChanged});

  final double value;
  final ValueChanged<double> onChanged;

  @override
  Widget build(BuildContext context) {
    final percent = (value * 100).round();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.s),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SettingIcon(icon: AppGlyph.fontSize),
          const SizedBox(width: AppSpacing.s),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  alignment: WrapAlignment.spaceBetween,
                  runSpacing: AppSpacing.xs,
                  spacing: AppSpacing.s,
                  children: [
                    Text(
                      '界面字体缩放',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    _ScaleBadge(percent: percent),
                  ],
                ),
                const SizedBox(height: AppSpacing.xxs),
                Text(
                  '可在 90% 至 200% 范围内调整，核心内容会随字号自动重排。',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: AppSpacing.xs),
                Semantics(
                  label: '当前字体缩放 $percent%',
                  child: Slider(
                    key: const ValueKey<String>('font-scale-slider'),
                    min: 0.9,
                    max: 2.0,
                    divisions: 11,
                    label: '$percent%',
                    value: value,
                    onChanged: onChanged,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingIcon extends StatelessWidget {
  const _SettingIcon({required this.icon});

  final AppGlyph icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 42,
      height: 42,
      decoration: BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark
            ? Theme.of(context).colorScheme.primary
            : const Color(0xFFFFE6BF),
        borderRadius: BorderRadius.circular(6),
      ),
      child: AppIcon(
        icon,
        color: Theme.of(context).brightness == Brightness.dark
            ? Theme.of(context).colorScheme.onPrimary
            : AppColors.textPrimary,
      ),
    );
  }
}

class _ScaleBadge extends StatelessWidget {
  const _ScaleBadge({required this.percent});

  final int percent;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s,
        vertical: AppSpacing.xxs,
      ),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainer,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        '$percent%',
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
    );
  }
}

class _ShortcutRow extends StatelessWidget {
  const _ShortcutRow({required this.keys, required this.action});

  final String keys;
  final String action;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.s),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLowest,
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(6),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final keyLabel = Container(
            constraints: const BoxConstraints(minWidth: 92),
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.xs,
              vertical: AppSpacing.xxs,
            ),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHigh,
              border: Border.all(color: Theme.of(context).colorScheme.outline),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              keys,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                fontFamily: 'Cascadia Mono',
                fontSize: 12,
              ),
            ),
          );
          if (constraints.maxWidth < 420) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                keyLabel,
                const SizedBox(height: AppSpacing.xs),
                Text(action),
              ],
            );
          }
          return Row(
            children: [
              keyLabel,
              const SizedBox(width: AppSpacing.s),
              Expanded(child: Text(action)),
            ],
          );
        },
      ),
    );
  }
}

class _AccessibilitySummary extends StatelessWidget {
  const _AccessibilitySummary();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.m),
      decoration: BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark
            ? Theme.of(context).colorScheme.surface
            : const Color(0xFFE7F4F5),
        border: Border.all(color: Theme.of(context).colorScheme.secondary),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppIcon(
            AppGlyph.accessibility,
            color: Theme.of(context).colorScheme.secondary,
          ),
          const SizedBox(width: AppSpacing.s),
          const Expanded(child: Text('界面支持键盘导航、可见焦点、语义标签、高对比度、动态字体和减少动画。')),
        ],
      ),
    );
  }
}

class _ReleaseAboutCard extends StatelessWidget {
  const _ReleaseAboutCard();

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      key: const ValueKey<String>('release-about-card'),
      title: '版本、隐私与开源声明',
      subtitle: '正式版将产品能力、证据口径与分发边界直接呈现在应用内。',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            key: const ValueKey<String>('release-version-banner'),
            width: double.infinity,
            padding: const EdgeInsets.all(AppSpacing.m),
            decoration: BoxDecoration(
              color: Theme.of(context).brightness == Brightness.dark
                  ? Theme.of(context).colorScheme.surface
                  : const Color(0xFFFFF4E5),
              border: Border.all(color: Theme.of(context).colorScheme.primary),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Wrap(
              crossAxisAlignment: WrapCrossAlignment.center,
              spacing: AppSpacing.s,
              runSpacing: AppSpacing.xs,
              children: [
                const AppIcon(AppGlyph.verified, semanticLabel: '正式发布版'),
                Text(
                  ReleaseInfo.productName,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                _ReleaseBadge(label: ReleaseInfo.version),
                _ReleaseBadge(label: '发布日期 ${ReleaseInfo.releaseDate}'),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.m),
          LayoutBuilder(
            builder: (context, constraints) {
              final columns = constraints.maxWidth >= 720 ? 3 : 1;
              final width = columns == 3
                  ? (constraints.maxWidth - AppSpacing.s * 2) / 3
                  : constraints.maxWidth;
              return Wrap(
                spacing: AppSpacing.s,
                runSpacing: AppSpacing.s,
                children: [
                  SizedBox(
                    width: width,
                    child: const _ReleaseFact(
                      icon: AppGlyph.lock,
                      label: '隐私模式',
                      value: ReleaseInfo.privacyMode,
                    ),
                  ),
                  SizedBox(
                    width: width,
                    child: const _ReleaseFact(
                      icon: AppGlyph.offline,
                      label: '进程协议',
                      value: ReleaseInfo.protocol,
                    ),
                  ),
                  SizedBox(
                    width: width,
                    child: const _ReleaseFact(
                      icon: AppGlyph.success,
                      label: '发布测试目标',
                      value: '${ReleaseInfo.automatedTestTarget} 项自动化测试',
                    ),
                  ),
                ],
              );
            },
          ),
          const SizedBox(height: AppSpacing.l),
          Text('能力边界', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: AppSpacing.s),
          for (final disclosure in ReleaseInfo.disclosures)
            _DisclosureRow(disclosure: disclosure),
          const Divider(height: AppSpacing.xl),
          Text('开源与模型许可', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: AppSpacing.xs),
          const Text(
            '项目源码采用 Apache-2.0。第三方依赖保留各自许可；MobileCLIP 等模型权重和验证数据不进入源码包。完整清单见 THIRD_PARTY_NOTICES.md 与 MODEL_AND_DATA_LICENSES.md。',
            key: ValueKey<String>('license-boundary-summary'),
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            ReleaseInfo.accessibilityClaim,
            key: const ValueKey<String>('accessibility-claim'),
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}

class _ReleaseBadge extends StatelessWidget {
  const _ReleaseBadge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s,
        vertical: AppSpacing.xxs,
      ),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(label, style: Theme.of(context).textTheme.labelMedium),
    );
  }
}

class _ReleaseFact extends StatelessWidget {
  const _ReleaseFact({
    required this.icon,
    required this.label,
    required this.value,
  });

  final AppGlyph icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 96),
      padding: const EdgeInsets.all(AppSpacing.s),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLowest,
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppIcon(icon, size: 20),
          const SizedBox(width: AppSpacing.s),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: Theme.of(context).textTheme.labelMedium),
                const SizedBox(height: AppSpacing.xxs),
                Text(value),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DisclosureRow extends StatelessWidget {
  const _DisclosureRow({required this.disclosure});

  final ReleaseDisclosure disclosure;

  @override
  Widget build(BuildContext context) {
    return Padding(
      key: ValueKey<String>('disclosure-${disclosure.id}'),
      padding: const EdgeInsets.only(bottom: AppSpacing.s),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const AppIcon(AppGlyph.info, size: 19),
          const SizedBox(width: AppSpacing.s),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  disclosure.title,
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: AppSpacing.xxs),
                Text(disclosure.summary),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _HelpTopicGrid extends StatelessWidget {
  const _HelpTopicGrid();

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      key: const ValueKey<String>('help-topic-grid'),
      title: '快速帮助',
      subtitle: '文档随源码离线提供，无需跳转到外部网站。',
      child: LayoutBuilder(
        builder: (context, constraints) {
          final useTwoColumns =
              constraints.maxWidth >= 680 &&
              !ResponsiveLayout.usesLargeText(context);
          final width = useTwoColumns
              ? (constraints.maxWidth - AppSpacing.m) / 2
              : constraints.maxWidth;
          return Wrap(
            spacing: AppSpacing.m,
            runSpacing: AppSpacing.m,
            children: [
              for (final topic in ReleaseInfo.helpTopics)
                SizedBox(
                  width: width,
                  child: _HelpTopicCard(topic: topic),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _HelpTopicCard extends StatelessWidget {
  const _HelpTopicCard({required this.topic});

  final HelpTopic topic;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      label: '${topic.title}；${topic.action}',
      child: Container(
        key: ValueKey<String>('help-${topic.id}'),
        constraints: const BoxConstraints(minHeight: 132),
        padding: const EdgeInsets.all(AppSpacing.m),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerLowest,
          border: Border.all(
            color: Theme.of(context).colorScheme.outlineVariant,
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const AppIcon(AppGlyph.document, size: 20),
                const SizedBox(width: AppSpacing.xs),
                Expanded(
                  child: Text(
                    topic.title,
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(topic.detail),
            const SizedBox(height: AppSpacing.xs),
            Text(
              topic.action,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: Theme.of(context).colorScheme.secondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Shortcut {
  const _Shortcut(this.keys, this.action);

  final String keys;
  final String action;
}

const _shortcuts = <_Shortcut>[
  _Shortcut('Ctrl + K', '聚焦搜索框'),
  _Shortcut('Alt + 1', '打开资料库'),
  _Shortcut('Alt + 2', '打开搜索'),
  _Shortcut('Alt + 3', '打开无障碍设置'),
  _Shortcut('Tab / Shift + Tab', '前后移动焦点'),
  _Shortcut('Enter / Space', '激活当前控件'),
];
