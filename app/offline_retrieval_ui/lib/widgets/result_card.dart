import 'package:flutter/material.dart';

import '../design_system/app_theme.dart';
import '../design_system/app_icons.dart';
import '../design_system/responsive_layout.dart';
import '../models/retrieval_models.dart';

/// 展示文件来源、摘要、匹配解释和详情入口的检索结果卡片。
class ResultCard extends StatelessWidget {
  const ResultCard({required this.hit, super.key});

  final RetrievalHit hit;

  AppGlyph get _icon {
    return switch (hit.extension) {
      'pdf' => AppGlyph.pdf,
      'docx' => AppGlyph.document,
      'jpg' || 'jpeg' || 'png' => AppGlyph.image,
      _ => AppGlyph.text,
    };
  }

  String get _relevanceLabel {
    if (hit.score >= 0.85) {
      return '高度相关';
    }
    if (hit.score >= 0.6) {
      return '相关';
    }
    return '可能相关';
  }

  @override
  Widget build(BuildContext context) {
    final percent = (hit.score * 100).round();
    return Semantics(
      container: true,
      explicitChildNodes: true,
      label: '${hit.fileName}，$_relevanceLabel，综合相关性 $percent%',
      child: Card(
        key: ValueKey<String>('result-${hit.itemId}'),
        margin: const EdgeInsets.only(bottom: AppSpacing.s),
        child: InkWell(
          onTap: () => _showDetails(context),
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.m),
            child: LayoutBuilder(
              builder: (context, constraints) {
                final mobile =
                    ResponsiveLayout.deviceClassFor(constraints.maxWidth) ==
                    AppDeviceClass.mobile;
                final compact =
                    constraints.maxWidth < AppBreakpoints.stackedResultCard ||
                    ResponsiveLayout.usesLargeText(context);
                if (compact) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _FileHeading(
                        icon: _icon,
                        fileName: hit.fileName,
                        extension: hit.extension,
                      ),
                      const SizedBox(height: AppSpacing.s),
                      _ResultContent(hit: hit),
                      const SizedBox(height: AppSpacing.m),
                      if (mobile) ...[
                        Align(
                          alignment: Alignment.centerLeft,
                          child: _RelevanceBadge(
                            percent: percent,
                            label: _relevanceLabel,
                          ),
                        ),
                        const SizedBox(height: AppSpacing.s),
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: () => _showDetails(context),
                            icon: const AppIcon(AppGlyph.external, size: 18),
                            label: const Text('查看详情'),
                          ),
                        ),
                      ] else
                        Wrap(
                          alignment: WrapAlignment.spaceBetween,
                          runSpacing: AppSpacing.xs,
                          spacing: AppSpacing.m,
                          children: [
                            _RelevanceBadge(
                              percent: percent,
                              label: _relevanceLabel,
                            ),
                            TextButton.icon(
                              onPressed: () => _showDetails(context),
                              icon: const AppIcon(AppGlyph.external, size: 18),
                              label: const Text('查看详情'),
                            ),
                          ],
                        ),
                    ],
                  );
                }
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 220,
                      child: _FileHeading(
                        icon: _icon,
                        fileName: hit.fileName,
                        extension: hit.extension,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.l),
                    Expanded(child: _ResultContent(hit: hit)),
                    const SizedBox(width: AppSpacing.l),
                    SizedBox(
                      width: 124,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          _RelevanceBadge(
                            percent: percent,
                            label: _relevanceLabel,
                          ),
                          const SizedBox(height: AppSpacing.s),
                          TextButton.icon(
                            onPressed: () => _showDetails(context),
                            icon: const AppIcon(AppGlyph.external, size: 18),
                            label: const Text('查看详情'),
                          ),
                        ],
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _showDetails(BuildContext context) {
    final percent = (hit.score * 100).round();
    return showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: Row(
            children: [
              AppIcon(_icon),
              const SizedBox(width: AppSpacing.s),
              Expanded(child: Text(hit.fileName)),
            ],
          ),
          content: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 620),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: AppSpacing.xs,
                    runSpacing: AppSpacing.xs,
                    children: [
                      Chip(label: Text(hit.extension.toUpperCase())),
                      Chip(label: Text(hit.modality)),
                      Chip(label: Text('综合相关性 $percent%')),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.m),
                  Text('内容摘要', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: AppSpacing.xs),
                  SelectableText(hit.text),
                  const SizedBox(height: AppSpacing.l),
                  Text('匹配解释', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: AppSpacing.xs),
                  _ScoreRow(label: '语义相关性', value: hit.semanticScore),
                  const SizedBox(height: AppSpacing.xs),
                  _ScoreRow(label: '关键词相关性', value: hit.keywordScore),
                  const SizedBox(height: AppSpacing.l),
                  Text('本地来源', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: AppSpacing.xs),
                  SelectableText(
                    hit.sourcePath,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      fontFamily: 'Cascadia Mono',
                    ),
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('关闭'),
            ),
          ],
        );
      },
    );
  }
}

class _FileHeading extends StatelessWidget {
  const _FileHeading({
    required this.icon,
    required this.fileName,
    required this.extension,
  });

  final AppGlyph icon;
  final String fileName;
  final String extension;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: Theme.of(context).brightness == Brightness.dark
                ? Theme.of(context).colorScheme.primary
                : const Color(0xFFFFE6BF),
            borderRadius: BorderRadius.circular(6),
          ),
          child: ExcludeSemantics(
            child: AppIcon(
              icon,
              color: Theme.of(context).brightness == Brightness.dark
                  ? Theme.of(context).colorScheme.onPrimary
                  : AppColors.textPrimary,
            ),
          ),
        ),
        const SizedBox(width: AppSpacing.s),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                fileName,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: AppSpacing.xxs),
              Text(
                extension.isEmpty ? '未知类型' : extension.toUpperCase(),
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ResultContent extends StatelessWidget {
  const _ResultContent({required this.hit});

  final RetrievalHit hit;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          hit.text,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: AppSpacing.s),
        Wrap(
          spacing: AppSpacing.m,
          runSpacing: AppSpacing.xs,
          children: [
            _ScoreLabel(label: '语义', value: hit.semanticScore),
            _ScoreLabel(label: '关键词', value: hit.keywordScore),
            _MetadataLabel(
              icon: hit.isImage ? AppGlyph.image : AppGlyph.article,
              text: hit.isImage ? '图片模态' : '文本模态',
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.s),
        Row(
          children: [
            AppIcon(
              AppGlyph.folder,
              size: 16,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(width: AppSpacing.xs),
            Expanded(
              child: Text(
                hit.sourcePath,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _RelevanceBadge extends StatelessWidget {
  const _RelevanceBadge({required this.percent, required this.label});

  final int percent;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '$label，综合相关性 $percent%',
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.s,
          vertical: AppSpacing.xs,
        ),
        decoration: BoxDecoration(
          color: Theme.of(context).brightness == Brightness.dark
              ? Theme.of(context).colorScheme.surface
              : const Color(0xFFE7F4F5),
          border: Border.all(color: Theme.of(context).colorScheme.secondary),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Column(
          children: [
            Text(
              '$percent%',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            Text(label, style: Theme.of(context).textTheme.labelSmall),
          ],
        ),
      ),
    );
  }
}

class _ScoreLabel extends StatelessWidget {
  const _ScoreLabel({required this.label, required this.value});

  final String label;
  final double value;

  @override
  Widget build(BuildContext context) {
    return Text(
      '$label ${(value * 100).round()}%',
      style: Theme.of(
        context,
      ).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600),
    );
  }
}

class _MetadataLabel extends StatelessWidget {
  const _MetadataLabel({required this.icon, required this.text});

  final AppGlyph icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        AppIcon(icon, size: 16),
        const SizedBox(width: AppSpacing.xxs),
        Text(
          text,
          style: Theme.of(
            context,
          ).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600),
        ),
      ],
    );
  }
}

class _ScoreRow extends StatelessWidget {
  const _ScoreRow({required this.label, required this.value});

  final String label;
  final double value;

  @override
  Widget build(BuildContext context) {
    final percent = (value * 100).round();
    return Row(
      children: [
        SizedBox(width: 96, child: Text(label)),
        Expanded(
          child: LinearProgressIndicator(
            value: value.clamp(0, 1),
            minHeight: 8,
            borderRadius: BorderRadius.circular(4),
          ),
        ),
        const SizedBox(width: AppSpacing.s),
        SizedBox(
          width: 42,
          child: Text(
            '$percent%',
            textAlign: TextAlign.end,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
        ),
      ],
    );
  }
}
