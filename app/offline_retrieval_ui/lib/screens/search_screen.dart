import 'package:flutter/material.dart';

import '../design_system/app_theme.dart';
import '../design_system/app_icons.dart';
import '../design_system/responsive_layout.dart';
import '../state/app_controller.dart';
import '../widgets/layout_widgets.dart';
import '../widgets/result_card.dart';

/// 语义检索页，支持文件过滤、键盘聚焦和状态播报。
class SearchScreen extends StatefulWidget {
  const SearchScreen({required this.controller, super.key});

  final AppController controller;

  @override
  State<SearchScreen> createState() => SearchScreenState();
}

class SearchScreenState extends State<SearchScreen> {
  late final TextEditingController _textController;
  final FocusNode _queryFocus = FocusNode(debugLabel: 'search-query');

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController(text: widget.controller.query);
  }

  /// 供 Ctrl+K 和全局搜索入口调用。
  void focusQuery() => _queryFocus.requestFocus();

  @override
  void dispose() {
    _textController.dispose();
    _queryFocus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final response = widget.controller.response;
    return FocusTraversalGroup(
      policy: OrderedTraversalPolicy(),
      child: ListView(
        key: const ValueKey<String>('search-screen'),
        padding: ResponsiveLayout.pagePaddingFor(
          MediaQuery.sizeOf(context).width,
        ),
        children: [
          ContentWidth(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const PageHeader(
                  eyebrow: 'HYBRID RETRIEVAL',
                  title: '搜索本地内容',
                  subtitle: '使用语义与关键词混合检索，在本机快速定位文档、图片和相关片段。',
                ),
                const SizedBox(height: AppSpacing.xl),
                SectionCard(
                  title: '查找内容',
                  subtitle: '输入自然语言问题或关键词，按 Ctrl+K 可随时返回搜索框。',
                  child: _SearchControls(
                    controller: widget.controller,
                    textController: _textController,
                    queryFocus: _queryFocus,
                    onClear: () {
                      _textController.clear();
                      widget.controller.setQuery('');
                      focusQuery();
                    },
                  ),
                ),
                const SizedBox(height: AppSpacing.xl),
                if (response == null)
                  const _EmptyState(
                    icon: AppGlyph.search,
                    title: '开始第一次本地检索',
                    message: '输入查询后，系统将显示来源、内容摘要和可解释的匹配分数。',
                    suggestions: [
                      'vector database',
                      'accessibility',
                      'local photo',
                    ],
                  )
                else ...[
                  _ResultsHeader(
                    query: response.query,
                    resultCount: response.hits.length,
                    candidateCount: response.candidateCount,
                    elapsedMs: response.elapsedMs,
                  ),
                  if (response.warnings.isNotEmpty) ...[
                    const SizedBox(height: AppSpacing.s),
                    _WarningPanel(messages: response.warnings),
                  ],
                  const SizedBox(height: AppSpacing.m),
                  if (response.hits.isEmpty)
                    const _EmptyState(
                      icon: AppGlyph.searchEmpty,
                      title: '没有找到匹配内容',
                      message: '尝试缩短查询、清除文件类型筛选或换用更常见的关键词。',
                      suggestions: ['清除筛选', '使用较短关键词', '检查文件是否已索引'],
                    )
                  else
                    for (final hit in response.hits) ResultCard(hit: hit),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SearchControls extends StatelessWidget {
  const _SearchControls({
    required this.controller,
    required this.textController,
    required this.queryFocus,
    required this.onClear,
  });

  final AppController controller;
  final TextEditingController textController;
  final FocusNode queryFocus;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final queryField = TextField(
      key: const ValueKey<String>('search-field'),
      controller: textController,
      focusNode: queryFocus,
      textInputAction: TextInputAction.search,
      decoration: InputDecoration(
        labelText: '搜索查询',
        hintText: '例如：vector database similarity',
        prefixIcon: const AppIcon(AppGlyph.search),
        suffixIcon: Tooltip(
          message: '清除搜索内容',
          child: IconButton(
            key: const ValueKey<String>('clear-search'),
            onPressed: onClear,
            icon: const AppIcon(AppGlyph.close),
          ),
        ),
      ),
      onChanged: controller.setQuery,
      onSubmitted: (_) => controller.search(),
    );
    final searchButton = FilledButton.icon(
      key: const ValueKey<String>('run-search'),
      onPressed: controller.isSearching ? null : controller.search,
      icon: controller.isSearching
          ? const SizedBox.square(
              dimension: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const AppIcon(AppGlyph.search, selected: true),
      label: Text(controller.isSearching ? '正在检索' : '开始检索'),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            if (constraints.maxWidth < AppBreakpoints.stackedSearchControls ||
                ResponsiveLayout.usesLargeText(context)) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  queryField,
                  const SizedBox(height: AppSpacing.s),
                  searchButton,
                ],
              );
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: queryField),
                const SizedBox(width: AppSpacing.s),
                searchButton,
              ],
            );
          },
        ),
        const SizedBox(height: AppSpacing.m),
        LayoutBuilder(
          builder: (context, constraints) {
            final mobile =
                ResponsiveLayout.deviceClassFor(constraints.maxWidth) ==
                AppDeviceClass.mobile;
            if (mobile) {
              final activeFilters =
                  (controller.extension == null ? 0 : 1) +
                  (controller.includeImages ? 1 : 0);
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  OutlinedButton.icon(
                    key: const ValueKey<String>('mobile-filter-button'),
                    onPressed: () => _showMobileFilters(context),
                    icon: const AppIcon(AppGlyph.tune),
                    label: Text('筛选与选项 · $activeFilters'),
                  ),
                  const SizedBox(height: AppSpacing.s),
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: _PrivacyNote(),
                  ),
                ],
              );
            }
            return Wrap(
              spacing: AppSpacing.s,
              runSpacing: AppSpacing.s,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                DropdownMenu<String>(
                  key: const ValueKey<String>('extension-filter'),
                  width: 210,
                  label: const Text('文件类型'),
                  initialSelection: controller.extension ?? 'all',
                  dropdownMenuEntries: _extensionEntries,
                  onSelected: (value) =>
                      controller.setExtension(value == 'all' ? null : value),
                ),
                FilterChip(
                  key: const ValueKey<String>('include-images'),
                  avatar: const AppIcon(AppGlyph.image, size: 18),
                  label: const Text('包含图片结果'),
                  selected: controller.includeImages,
                  onSelected: controller.setIncludeImages,
                ),
                const _PrivacyNote(),
              ],
            );
          },
        ),
      ],
    );
  }

  Future<void> _showMobileFilters(BuildContext context) {
    return showModalBottomSheet<void>(
      context: context,
      useSafeArea: true,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => _MobileFilterSheet(controller: controller),
    );
  }
}

const _extensionEntries = <DropdownMenuEntry<String>>[
  DropdownMenuEntry(value: 'all', label: '全部类型'),
  DropdownMenuEntry(value: 'txt', label: 'TXT'),
  DropdownMenuEntry(value: 'pdf', label: 'PDF'),
  DropdownMenuEntry(value: 'docx', label: 'DOCX'),
  DropdownMenuEntry(value: 'jpg', label: 'JPG'),
  DropdownMenuEntry(value: 'png', label: 'PNG'),
];

class _MobileFilterSheet extends StatefulWidget {
  const _MobileFilterSheet({required this.controller});

  final AppController controller;

  @override
  State<_MobileFilterSheet> createState() => _MobileFilterSheetState();
}

class _MobileFilterSheetState extends State<_MobileFilterSheet> {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        AppSpacing.m,
        0,
        AppSpacing.m,
        MediaQuery.viewInsetsOf(context).bottom + AppSpacing.xl,
      ),
      child: ListView(
        shrinkWrap: true,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '筛选与搜索选项',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              IconButton(
                tooltip: '关闭筛选面板',
                onPressed: () => Navigator.of(context).pop(),
                icon: const AppIcon(AppGlyph.close),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.m),
          LayoutBuilder(
            builder: (context, constraints) {
              return DropdownMenu<String>(
                key: const ValueKey<String>('mobile-extension-filter'),
                width: constraints.maxWidth,
                label: const Text('文件类型'),
                initialSelection: widget.controller.extension ?? 'all',
                dropdownMenuEntries: _extensionEntries,
                onSelected: (value) {
                  widget.controller.setExtension(value == 'all' ? null : value);
                  setState(() {});
                },
              );
            },
          ),
          const SizedBox(height: AppSpacing.m),
          SwitchListTile(
            key: const ValueKey<String>('mobile-include-images'),
            contentPadding: EdgeInsets.zero,
            secondary: const AppIcon(AppGlyph.image),
            title: const Text('包含图片结果'),
            subtitle: const Text('同时返回与查询相关的本地图片。'),
            value: widget.controller.includeImages,
            onChanged: (value) {
              widget.controller.setIncludeImages(value);
              setState(() {});
            },
          ),
          const Divider(height: AppSpacing.xl),
          const _PrivacyNote(),
          const SizedBox(height: AppSpacing.m),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('应用筛选'),
          ),
        ],
      ),
    );
  }
}

class _PrivacyNote extends StatelessWidget {
  const _PrivacyNote();

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '查询仅在本地处理',
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          AppIcon(
            AppGlyph.lock,
            size: 17,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          const SizedBox(width: AppSpacing.xs),
          Text(
            '查询仅在本地处理',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}

class _ResultsHeader extends StatelessWidget {
  const _ResultsHeader({
    required this.query,
    required this.resultCount,
    required this.candidateCount,
    required this.elapsedMs,
  });

  final String query;
  final int resultCount;
  final int candidateCount;
  final double elapsedMs;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      label:
          '搜索完成，共 $resultCount 个结果，候选 $candidateCount 项，耗时 ${elapsedMs.toStringAsFixed(2)} 毫秒',
      child: LayoutBuilder(
        builder: (context, constraints) {
          final title = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '“$query”的搜索结果',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: AppSpacing.xxs),
              Text(
                '找到 $resultCount 项相关内容',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          );
          final metrics = Wrap(
            spacing: AppSpacing.xs,
            runSpacing: AppSpacing.xs,
            children: [
              _ResultMetric(label: '候选', value: '$candidateCount'),
              _ResultMetric(
                label: '耗时',
                value: '${elapsedMs.toStringAsFixed(2)} ms',
              ),
            ],
          );
          if (constraints.maxWidth < AppBreakpoints.stackedSearchControls ||
              ResponsiveLayout.usesLargeText(context)) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                title,
                const SizedBox(height: AppSpacing.s),
                metrics,
              ],
            );
          }
          return Row(
            children: [
              Expanded(child: title),
              metrics,
            ],
          );
        },
      ),
    );
  }
}

class _ResultMetric extends StatelessWidget {
  const _ResultMetric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        '$label $value',
        style: Theme.of(
          context,
        ).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w700),
      ),
    );
  }
}

class _WarningPanel extends StatelessWidget {
  const _WarningPanel({required this.messages});

  final List<String> messages;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Container(
        key: const ValueKey<String>('search-warning'),
        padding: const EdgeInsets.all(AppSpacing.m),
        decoration: BoxDecoration(
          color: Theme.of(context).brightness == Brightness.dark
              ? Theme.of(context).colorScheme.surface
              : const Color(0xFFFFF4E5),
          border: Border.all(color: Theme.of(context).colorScheme.error),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppIcon(AppGlyph.info, color: Theme.of(context).colorScheme.error),
            const SizedBox(width: AppSpacing.s),
            Expanded(child: Text(messages.join('；'))),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.icon,
    required this.title,
    required this.message,
    required this.suggestions,
  });

  final AppGlyph icon;
  final String title;
  final String message;
  final List<String> suggestions;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.xxl),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 620),
            child: Column(
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: Theme.of(context).brightness == Brightness.dark
                        ? Theme.of(context).colorScheme.primary
                        : const Color(0xFFFFE6BF),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: ExcludeSemantics(
                    child: AppIcon(
                      icon,
                      size: 34,
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Theme.of(context).colorScheme.onPrimary
                          : AppColors.textPrimary,
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.m),
                Text(title, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: AppSpacing.xs),
                Text(message, textAlign: TextAlign.center),
                const SizedBox(height: AppSpacing.m),
                Wrap(
                  alignment: WrapAlignment.center,
                  spacing: AppSpacing.xs,
                  runSpacing: AppSpacing.xs,
                  children: [
                    for (final suggestion in suggestions)
                      Chip(label: Text(suggestion)),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
