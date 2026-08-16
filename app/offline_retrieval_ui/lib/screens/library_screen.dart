import 'package:flutter/material.dart';

import '../design_system/app_theme.dart';
import '../design_system/app_icons.dart';
import '../design_system/responsive_layout.dart';

import '../state/app_controller.dart';
import '../widgets/layout_widgets.dart';
import '../widgets/result_card.dart';

/// 本地资料库管理页，展示索引概况、内容类型和文件列表。
class LibraryScreen extends StatefulWidget {
  const LibraryScreen({required this.controller, super.key});

  final AppController controller;

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  String? _selectedExtension;

  Future<void> _showIndexDialog(BuildContext context) async {
    final path = await showDialog<String>(
      context: context,
      builder: (context) => const _IndexPathDialog(),
    );
    if (path != null && path.trim().isNotEmpty) {
      await widget.controller.indexPath(path);
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    final items = controller.libraryItems;
    final extensions = items.map((item) => item.extension).toSet().toList()
      ..sort();
    final visible = _selectedExtension == null
        ? items
        : items.where((item) => item.extension == _selectedExtension).toList();
    final imageCount = items.where((item) => item.isImage).length;

    return FocusTraversalGroup(
      policy: OrderedTraversalPolicy(),
      child: ListView(
        key: const ValueKey<String>('library-screen'),
        padding: ResponsiveLayout.pagePaddingFor(
          MediaQuery.sizeOf(context).width,
        ),
        children: [
          ContentWidth(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                PageHeader(
                  eyebrow: 'LOCAL LIBRARY',
                  title: '本地资料库',
                  subtitle: '集中查看已索引内容、文件类型和本地存储位置。',
                  actions: [
                    _StatusBadge(
                      icon: controller.healthStatus?.ready == true
                          ? AppGlyph.verified
                          : AppGlyph.info,
                      label: controller.healthStatus?.ready == true
                          ? '本地后端已就绪'
                          : controller.backendModeLabel,
                    ),
                    FilledButton.icon(
                      key: const ValueKey<String>('index-local-path'),
                      onPressed: controller.isIndexing
                          ? null
                          : () => _showIndexDialog(context),
                      icon: controller.isIndexing
                          ? const SizedBox.square(
                              dimension: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const AppIcon(AppGlyph.addFolder),
                      label: Text(controller.isIndexing ? '正在索引' : '添加本地路径'),
                    ),
                  ],
                ),
                if (controller.isIndexing) ...[
                  const SizedBox(height: AppSpacing.m),
                  const LinearProgressIndicator(
                    key: ValueKey<String>('index-progress'),
                  ),
                ],
                if (controller.lastIndexingResult != null ||
                    controller.backendError != null) ...[
                  const SizedBox(height: AppSpacing.m),
                  _IndexOutcome(controller: controller),
                ],
                const SizedBox(height: AppSpacing.xl),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final deviceClass = ResponsiveLayout.deviceClassFor(
                      constraints.maxWidth,
                    );
                    final largeText = ResponsiveLayout.usesLargeText(context);
                    final cards = [
                      MetricCard(
                        icon: AppGlyph.inventory,
                        value: '${items.length}',
                        label: '个文件',
                        supportingText: '已完成本地索引',
                      ),
                      MetricCard(
                        icon: AppGlyph.category,
                        value: '${extensions.length}',
                        label: '种类型',
                        supportingText: '文本、文档与图片',
                      ),
                      MetricCard(
                        icon: AppGlyph.image,
                        value: '$imageCount',
                        label: '个图片',
                        supportingText: '可参与跨模态检索',
                      ),
                    ];
                    if (deviceClass == AppDeviceClass.mobile && !largeText) {
                      final cardWidth =
                          (constraints.maxWidth - AppSpacing.s) / 2;
                      return Wrap(
                        key: const ValueKey<String>('mobile-metric-grid'),
                        spacing: AppSpacing.s,
                        runSpacing: AppSpacing.s,
                        children: [
                          for (final card in cards)
                            SizedBox(width: cardWidth, child: card),
                        ],
                      );
                    }
                    if (deviceClass == AppDeviceClass.tablet && !largeText) {
                      if (constraints.maxWidth >=
                          AppBreakpoints.threeColumnMetrics) {
                        return Row(
                          children: [
                            for (
                              var index = 0;
                              index < cards.length;
                              index++
                            ) ...[
                              Expanded(child: cards[index]),
                              if (index < cards.length - 1)
                                const SizedBox(width: AppSpacing.s),
                            ],
                          ],
                        );
                      }
                      final cardWidth =
                          (constraints.maxWidth - AppSpacing.s) / 2;
                      return Wrap(
                        key: const ValueKey<String>('tablet-metric-grid'),
                        spacing: AppSpacing.s,
                        runSpacing: AppSpacing.s,
                        children: [
                          for (final card in cards)
                            SizedBox(width: cardWidth, child: card),
                        ],
                      );
                    }
                    if (deviceClass != AppDeviceClass.desktop || largeText) {
                      return Column(
                        children: [
                          for (
                            var index = 0;
                            index < cards.length;
                            index++
                          ) ...[
                            cards[index],
                            if (index < cards.length - 1)
                              const SizedBox(height: AppSpacing.s),
                          ],
                        ],
                      );
                    }
                    return Row(
                      children: [
                        for (var index = 0; index < cards.length; index++) ...[
                          Expanded(child: cards[index]),
                          if (index < cards.length - 1)
                            const SizedBox(width: AppSpacing.m),
                        ],
                      ],
                    );
                  },
                ),
                const SizedBox(height: AppSpacing.xl),
                SectionCard(
                  title: '筛选资料',
                  subtitle: '按文件类型缩小范围，当前显示 ${visible.length} 项。',
                  child: Wrap(
                    spacing: AppSpacing.xs,
                    runSpacing: AppSpacing.xs,
                    children: [
                      FilterChip(
                        key: const ValueKey<String>('filter-all'),
                        label: const Text('全部'),
                        selected: _selectedExtension == null,
                        onSelected: (_) =>
                            setState(() => _selectedExtension = null),
                      ),
                      for (final extension in extensions)
                        FilterChip(
                          key: ValueKey<String>('filter-$extension'),
                          label: Text(extension.toUpperCase()),
                          selected: _selectedExtension == extension,
                          onSelected: (_) =>
                              setState(() => _selectedExtension = extension),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.xl),
                Row(
                  children: [
                    Text(
                      '已索引内容',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const Spacer(),
                    Text(
                      '${visible.length} 项',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.s),
                if (visible.isEmpty)
                  const SectionCard(child: _LibraryEmptyState())
                else
                  for (final item in visible) ResultCard(hit: item),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.icon, required this.label});

  final AppGlyph icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final highContrast = Theme.of(context).brightness == Brightness.dark;
    return Semantics(
      label: label,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.s,
          vertical: AppSpacing.xs,
        ),
        decoration: BoxDecoration(
          color: highContrast
              ? Theme.of(context).colorScheme.surface
              : const Color(0xFFE7F4F0),
          border: Border.all(
            color: highContrast
                ? Theme.of(context).colorScheme.outline
                : AppColors.success,
          ),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            AppIcon(
              icon,
              size: 18,
              color: highContrast
                  ? Theme.of(context).colorScheme.onSurface
                  : AppColors.success,
            ),
            const SizedBox(width: AppSpacing.xs),
            Text(
              label,
              style: TextStyle(
                color: highContrast
                    ? Theme.of(context).colorScheme.onSurface
                    : AppColors.success,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LibraryEmptyState extends StatelessWidget {
  const _LibraryEmptyState();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.xxl),
      child: Column(
        children: [
          const AppIcon(AppGlyph.filterOff, size: 42),
          const SizedBox(height: AppSpacing.s),
          Text('当前筛选条件下没有文件', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: AppSpacing.xs),
          Text(
            '请选择其他文件类型或返回“全部”。',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}

class _IndexOutcome extends StatelessWidget {
  const _IndexOutcome({required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final result = controller.lastIndexingResult;
    final success = result?.success == true;
    final message = success
        ? '索引完成：解析 ${result!.parsedFiles} 个文件，写入 '
              '${result.persistedVectors} 个向量。'
        : controller.backendError ?? result?.message ?? '索引未完成，请检查本地路径。';
    return Semantics(
      liveRegion: true,
      child: Container(
        key: const ValueKey<String>('index-outcome'),
        padding: const EdgeInsets.all(AppSpacing.m),
        decoration: BoxDecoration(
          color: success ? const Color(0xFFE7F4F0) : const Color(0xFFFFF4E5),
          border: Border.all(
            color: success
                ? AppColors.success
                : Theme.of(context).colorScheme.error,
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppIcon(success ? AppGlyph.success : AppGlyph.info),
            const SizedBox(width: AppSpacing.s),
            Expanded(child: Text(message)),
          ],
        ),
      ),
    );
  }
}

class _IndexPathDialog extends StatefulWidget {
  const _IndexPathDialog();

  @override
  State<_IndexPathDialog> createState() => _IndexPathDialogState();
}

class _IndexPathDialogState extends State<_IndexPathDialog> {
  final TextEditingController _controller = TextEditingController();
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      key: const ValueKey<String>('index-path-dialog'),
      title: const Text('添加本地文件或目录'),
      content: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 560),
        child: Form(
          key: _formKey,
          child: TextFormField(
            key: const ValueKey<String>('index-path-field'),
            controller: _controller,
            autofocus: true,
            decoration: const InputDecoration(
              labelText: '本地路径',
              hintText: r'C:\Users\YourName\Documents',
              prefixIcon: AppIcon(AppGlyph.folder),
              helperText: '文件内容仅在本机解析、嵌入和存储。',
            ),
            validator: (value) =>
                value == null || value.trim().isEmpty ? '请输入本地路径' : null,
            onFieldSubmitted: (_) => _submit(),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('取消'),
        ),
        FilledButton(
          key: const ValueKey<String>('confirm-index-path'),
          onPressed: _submit,
          child: const Text('开始索引'),
        ),
      ],
    );
  }

  void _submit() {
    if (_formKey.currentState?.validate() != true) {
      return;
    }
    Navigator.of(context).pop(_controller.text.trim());
  }
}
