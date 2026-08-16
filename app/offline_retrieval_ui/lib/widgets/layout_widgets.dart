import 'package:flutter/material.dart';

import '../design_system/app_theme.dart';
import '../design_system/app_icons.dart';
import '../design_system/responsive_layout.dart';

/// 将页面内容限制在适合桌面阅读的宽度内。
class ContentWidth extends StatelessWidget {
  const ContentWidth({required this.child, this.maxWidth = 1180, super.key});

  final Widget child;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: child,
      ),
    );
  }
}

/// 页面统一标题区，负责标题层级、说明文字和可选操作。
class PageHeader extends StatelessWidget {
  const PageHeader({
    required this.title,
    required this.subtitle,
    this.eyebrow,
    this.actions = const <Widget>[],
    super.key,
  });

  final String title;
  final String subtitle;
  final String? eyebrow;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final mobile =
            ResponsiveLayout.deviceClassFor(constraints.maxWidth) ==
            AppDeviceClass.mobile;
        final titleBlock = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (eyebrow != null) ...[
              Text(
                eyebrow!,
                style:
                    (mobile
                            ? Theme.of(context).textTheme.labelMedium
                            : Theme.of(context).textTheme.labelLarge)
                        ?.copyWith(
                          color: Theme.of(context).colorScheme.secondary,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.6,
                        ),
              ),
              SizedBox(height: mobile ? AppSpacing.xxs : AppSpacing.xs),
            ],
            Semantics(
              header: true,
              child: Text(
                title,
                style: mobile
                    ? Theme.of(context).textTheme.titleLarge
                    : Theme.of(context).textTheme.headlineMedium,
              ),
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              subtitle,
              style:
                  (mobile
                          ? Theme.of(context).textTheme.bodyMedium
                          : Theme.of(context).textTheme.bodyLarge)
                      ?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
            ),
          ],
        );

        if (actions.isEmpty) {
          return titleBlock;
        }
        if (constraints.maxWidth < AppBreakpoints.stackedHeader ||
            ResponsiveLayout.usesLargeText(context)) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              titleBlock,
              const SizedBox(height: AppSpacing.m),
              Wrap(
                spacing: AppSpacing.s,
                runSpacing: AppSpacing.s,
                children: actions,
              ),
            ],
          );
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: titleBlock),
            const SizedBox(width: AppSpacing.xl),
            Wrap(
              spacing: AppSpacing.s,
              runSpacing: AppSpacing.s,
              children: actions,
            ),
          ],
        );
      },
    );
  }
}

/// 用于表单、筛选器和说明区的统一白色内容面板。
class SectionCard extends StatelessWidget {
  const SectionCard({
    required this.child,
    this.title,
    this.subtitle,
    this.trailing,
    this.padding,
    super.key,
  });

  final String? title;
  final String? subtitle;
  final Widget? trailing;
  final EdgeInsetsGeometry? padding;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final resolvedPadding =
            padding ?? ResponsiveLayout.sectionPaddingFor(constraints.maxWidth);
        return Card(
          child: Padding(
            padding: resolvedPadding,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (title != null || trailing != null) ...[
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (title != null)
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                title!,
                                style: Theme.of(context).textTheme.titleMedium,
                              ),
                              if (subtitle != null) ...[
                                const SizedBox(height: AppSpacing.xxs),
                                Text(
                                  subtitle!,
                                  style: Theme.of(context).textTheme.bodySmall
                                      ?.copyWith(
                                        color: Theme.of(
                                          context,
                                        ).colorScheme.onSurfaceVariant,
                                      ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ?trailing,
                    ],
                  ),
                  const SizedBox(height: AppSpacing.m),
                ],
                child,
              ],
            ),
          ),
        );
      },
    );
  }
}

/// 用于状态和指标摘要的紧凑信息卡。
class MetricCard extends StatelessWidget {
  const MetricCard({
    required this.icon,
    required this.value,
    required this.label,
    required this.supportingText,
    super.key,
  });

  final AppGlyph icon;
  final String value;
  final String label;
  final String supportingText;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.m),
        child: Row(
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
              child: AppIcon(
                icon,
                color: Theme.of(context).brightness == Brightness.dark
                    ? Theme.of(context).colorScheme.onPrimary
                    : AppColors.textPrimary,
              ),
            ),
            const SizedBox(width: AppSpacing.s),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        value,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(width: AppSpacing.xs),
                      Expanded(
                        child: Text(
                          label,
                          style: Theme.of(context).textTheme.labelLarge,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xxs),
                  Text(
                    supportingText,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
