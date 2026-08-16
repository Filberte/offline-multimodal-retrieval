import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'design_system/app_icons.dart';
import 'design_system/app_theme.dart';
import 'design_system/responsive_layout.dart';
import 'models/release_info.dart';
import 'screens/library_screen.dart';
import 'screens/search_screen.dart';
import 'screens/settings_screen.dart';
import 'state/app_controller.dart';

/// 可在桌面、移动端和 Web 运行的离线检索应用。
class OfflineRetrievalApp extends StatelessWidget {
  const OfflineRetrievalApp({
    required this.controller,
    this.fontFamily = 'OfflineRetrievalCJK',
    super.key,
  });

  final AppController controller;
  final String? fontFamily;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) {
        final settings = controller.accessibility;
        return MaterialApp(
          debugShowCheckedModeBanner: false,
          title: ReleaseInfo.productName,
          theme: AppTheme.light(fontFamily: fontFamily),
          darkTheme: AppTheme.highContrast(fontFamily: fontFamily),
          themeMode: settings.highContrast ? ThemeMode.dark : ThemeMode.light,
          builder: (context, child) {
            final media = MediaQuery.of(context);
            return MediaQuery(
              data: media.copyWith(
                textScaler: TextScaler.linear(settings.fontScale),
                disableAnimations: settings.reduceMotion,
                highContrast: settings.highContrast,
              ),
              child: child!,
            );
          },
          home: RetrievalShell(controller: controller),
        );
      },
    );
  }
}

/// 根据设备形态选择独立的桌面、平板和移动端界面骨架。
class RetrievalShell extends StatefulWidget {
  const RetrievalShell({required this.controller, super.key});

  final AppController controller;

  @override
  State<RetrievalShell> createState() => _RetrievalShellState();
}

class _RetrievalShellState extends State<RetrievalShell> {
  final GlobalKey<SearchScreenState> _searchKey =
      GlobalKey<SearchScreenState>();

  void _select(int index) {
    widget.controller.selectDestination(index);
    if (index == 1) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _searchKey.currentState?.focusQuery();
      });
    }
  }

  Widget _buildPages() {
    return IndexedStack(
      index: widget.controller.selectedIndex,
      children: [
        LibraryScreen(controller: widget.controller),
        SearchScreen(key: _searchKey, controller: widget.controller),
        SettingsScreen(controller: widget.controller),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return CallbackShortcuts(
      bindings: <ShortcutActivator, VoidCallback>{
        const SingleActivator(LogicalKeyboardKey.keyK, control: true): () {
          _select(1);
        },
        const SingleActivator(LogicalKeyboardKey.digit1, alt: true): () {
          _select(0);
        },
        const SingleActivator(LogicalKeyboardKey.digit2, alt: true): () {
          _select(1);
        },
        const SingleActivator(LogicalKeyboardKey.digit3, alt: true): () {
          _select(2);
        },
      },
      child: Focus(
        autofocus: true,
        child: LayoutBuilder(
          builder: (context, constraints) {
            final deviceClass = ResponsiveLayout.deviceClassFor(
              constraints.maxWidth,
            );
            final body = _buildPages();
            return switch (deviceClass) {
              AppDeviceClass.desktop => _DesktopShell(
                controller: widget.controller,
                body: body,
                width: constraints.maxWidth,
                onSelect: _select,
              ),
              AppDeviceClass.tablet => _TabletShell(
                controller: widget.controller,
                body: body,
                onSelect: _select,
              ),
              AppDeviceClass.mobile => _MobileShell(
                controller: widget.controller,
                body: body,
                onSelect: _select,
              ),
            };
          },
        ),
      ),
    );
  }
}

class _DesktopShell extends StatelessWidget {
  const _DesktopShell({
    required this.controller,
    required this.body,
    required this.width,
    required this.onSelect,
  });

  final AppController controller;
  final Widget body;
  final double width;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final largeText = ResponsiveLayout.usesLargeText(context);
    final showGlobalSearch = !largeText || width >= AppBreakpoints.wide;
    final statusBarHeight = ResponsiveLayout.statusBarHeight(context);
    return Scaffold(
      key: const ValueKey<String>('desktop-shell'),
      appBar: AppBar(
        toolbarHeight: ResponsiveLayout.toolbarHeight(context),
        titleSpacing: AppSpacing.m,
        title: _DesktopTopNavigation(
          showGlobalSearch: showGlobalSearch,
          onSearchPressed: () => onSelect(1),
        ),
        actions: showGlobalSearch
            ? const []
            : [
                IconButton(
                  tooltip: '打开搜索（Ctrl+K）',
                  onPressed: () => onSelect(1),
                  icon: const AppIcon(AppGlyph.search),
                ),
                const _CompactPrivacyStatus(),
                const SizedBox(width: AppSpacing.xs),
              ],
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(statusBarHeight),
          child: _SystemStatusBar(
            indexedCount: controller.libraryItems.length,
            height: statusBarHeight,
          ),
        ),
      ),
      body: Row(
        children: [
          _AdaptiveNavigationRail(
            selectedIndex: controller.selectedIndex,
            onSelect: onSelect,
            extended: !largeText,
          ),
          const VerticalDivider(width: 1),
          Expanded(child: body),
        ],
      ),
    );
  }
}

class _TabletShell extends StatelessWidget {
  const _TabletShell({
    required this.controller,
    required this.body,
    required this.onSelect,
  });

  final AppController controller;
  final Widget body;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final statusBarHeight = ResponsiveLayout.statusBarHeight(context);
    return Scaffold(
      key: const ValueKey<String>('tablet-shell'),
      appBar: AppBar(
        toolbarHeight: ResponsiveLayout.toolbarHeight(context),
        titleSpacing: AppSpacing.m,
        title: const _TabletTopNavigation(),
        actions: [
          IconButton(
            key: const ValueKey<String>('tablet-search-entry'),
            tooltip: '打开搜索（Ctrl+K）',
            onPressed: () => onSelect(1),
            icon: const AppIcon(AppGlyph.search),
          ),
          const _CompactPrivacyStatus(),
          const SizedBox(width: AppSpacing.xs),
        ],
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(statusBarHeight),
          child: _SystemStatusBar(
            indexedCount: controller.libraryItems.length,
            height: statusBarHeight,
          ),
        ),
      ),
      body: Row(
        children: [
          _AdaptiveNavigationRail(
            selectedIndex: controller.selectedIndex,
            onSelect: onSelect,
            extended: false,
          ),
          const VerticalDivider(width: 1),
          Expanded(child: body),
        ],
      ),
    );
  }
}

class _MobileShell extends StatelessWidget {
  const _MobileShell({
    required this.controller,
    required this.body,
    required this.onSelect,
  });

  final AppController controller;
  final Widget body;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final selectedIndex = controller.selectedIndex;
    final showSearchEntry = selectedIndex != 1;
    final statusBarHeight = ResponsiveLayout.statusBarHeight(context);
    final mobileSearchHeight = showSearchEntry ? 60.0 : 0.0;
    return Scaffold(
      key: const ValueKey<String>('mobile-shell'),
      appBar: AppBar(
        toolbarHeight: ResponsiveLayout.mobileToolbarHeight(context),
        titleSpacing: AppSpacing.m,
        title: _MobileTopNavigation(label: _destinations[selectedIndex].label),
        actions: const [
          _CompactPrivacyStatus(),
          SizedBox(width: AppSpacing.xs),
        ],
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(mobileSearchHeight + statusBarHeight),
          child: Column(
            children: [
              if (showSearchEntry)
                SizedBox(
                  height: mobileSearchHeight,
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(
                      AppSpacing.s,
                      AppSpacing.xs,
                      AppSpacing.s,
                      AppSpacing.xs,
                    ),
                    child: _MobileSearchEntry(onPressed: () => onSelect(1)),
                  ),
                ),
              _SystemStatusBar(
                indexedCount: controller.libraryItems.length,
                height: statusBarHeight,
              ),
            ],
          ),
        ),
      ),
      body: body,
      bottomNavigationBar: NavigationBar(
        key: const ValueKey<String>('navigation-bar'),
        height: ResponsiveLayout.bottomNavigationHeight(context),
        selectedIndex: selectedIndex,
        onDestinationSelected: onSelect,
        destinations: _destinations
            .map(
              (item) => NavigationDestination(
                icon: AppIcon(item.icon),
                selectedIcon: AppIcon(item.selectedIcon, selected: true),
                label: item.label,
              ),
            )
            .toList(),
      ),
    );
  }
}

class _AdaptiveNavigationRail extends StatelessWidget {
  const _AdaptiveNavigationRail({
    required this.selectedIndex,
    required this.onSelect,
    required this.extended,
  });

  final int selectedIndex;
  final ValueChanged<int> onSelect;
  final bool extended;

  @override
  Widget build(BuildContext context) {
    return NavigationRail(
      key: const ValueKey<String>('navigation-rail'),
      selectedIndex: selectedIndex,
      onDestinationSelected: onSelect,
      extended: extended,
      minExtendedWidth: 216,
      labelType: extended
          ? NavigationRailLabelType.none
          : NavigationRailLabelType.all,
      leading: Padding(
        padding: const EdgeInsets.only(top: AppSpacing.m, bottom: AppSpacing.s),
        child: Tooltip(
          message: '搜索本地内容',
          child: IconButton.filled(
            key: const ValueKey<String>('rail-search-entry'),
            onPressed: () => onSelect(1),
            icon: const AppIcon(AppGlyph.search, selected: true),
          ),
        ),
      ),
      destinations: _destinations
          .map(
            (item) => NavigationRailDestination(
              icon: AppIcon(item.icon),
              selectedIcon: AppIcon(item.selectedIcon, selected: true),
              label: Text(item.label),
            ),
          )
          .toList(),
    );
  }
}

class _DesktopTopNavigation extends StatelessWidget {
  const _DesktopTopNavigation({
    required this.showGlobalSearch,
    required this.onSearchPressed,
  });

  final bool showGlobalSearch;
  final VoidCallback onSearchPressed;

  @override
  Widget build(BuildContext context) {
    if (!showGlobalSearch) {
      return const Row(
        children: [
          AppIcon(AppGlyph.library, size: 26),
          SizedBox(width: AppSpacing.s),
          Expanded(
            child: Text('本地内容检索', maxLines: 1, overflow: TextOverflow.ellipsis),
          ),
        ],
      );
    }
    return Row(
      children: [
        const AppIcon(AppGlyph.library, size: 26),
        const SizedBox(width: AppSpacing.s),
        const Text('离线多模态内容检索'),
        const SizedBox(width: AppSpacing.xxl),
        Expanded(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 680),
            child: _GlobalSearchEntry(onPressed: onSearchPressed),
          ),
        ),
        const SizedBox(width: AppSpacing.l),
        const _DesktopPrivacyStatus(),
      ],
    );
  }
}

class _TabletTopNavigation extends StatelessWidget {
  const _TabletTopNavigation();

  @override
  Widget build(BuildContext context) {
    return const Row(
      children: [
        AppIcon(AppGlyph.library, size: 26),
        SizedBox(width: AppSpacing.s),
        Expanded(
          child: Text('离线内容检索', maxLines: 1, overflow: TextOverflow.ellipsis),
        ),
      ],
    );
  }
}

class _MobileTopNavigation extends StatelessWidget {
  const _MobileTopNavigation({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const AppIcon(AppGlyph.library, size: 24),
        const SizedBox(width: AppSpacing.s),
        Expanded(
          child: Text(
            label,
            key: const ValueKey<String>('mobile-page-title'),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}

class _MobileSearchEntry extends StatelessWidget {
  const _MobileSearchEntry({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final highContrast = Theme.of(context).brightness == Brightness.dark;
    return Semantics(
      button: true,
      label: '打开本地内容搜索',
      child: Material(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(6),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          key: const ValueKey<String>('mobile-search-entry'),
          onTap: onPressed,
          child: Row(
            children: [
              const SizedBox(width: AppSpacing.m),
              AppIcon(
                AppGlyph.search,
                size: 21,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
              const SizedBox(width: AppSpacing.s),
              Expanded(
                child: Text(
                  '搜索文档、图片和音频',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
              Container(
                height: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.m),
                color: highContrast
                    ? Theme.of(context).colorScheme.primary
                    : AppColors.accent,
                alignment: Alignment.center,
                child: AppIcon(
                  AppGlyph.arrowForward,
                  size: 20,
                  color: highContrast
                      ? Theme.of(context).colorScheme.onPrimary
                      : AppColors.textPrimary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _GlobalSearchEntry extends StatelessWidget {
  const _GlobalSearchEntry({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: '打开全局搜索，快捷键 Ctrl+K',
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(6),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          key: const ValueKey<String>('global-search-entry'),
          onTap: onPressed,
          child: SizedBox(
            height: 44,
            child: Row(
              children: [
                const SizedBox(width: AppSpacing.m),
                const AppIcon(
                  AppGlyph.search,
                  color: AppColors.textSecondary,
                  size: 21,
                ),
                const SizedBox(width: AppSpacing.s),
                const Expanded(
                  child: Text(
                    '搜索本地文档、图片和音频',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 14,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ),
                Container(
                  height: 44,
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.m),
                  color: AppColors.accent,
                  alignment: Alignment.center,
                  child: const Row(
                    children: [
                      Text(
                        '查找',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      SizedBox(width: AppSpacing.xs),
                      Text(
                        'Ctrl+K',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _DesktopPrivacyStatus extends StatelessWidget {
  const _DesktopPrivacyStatus();

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '隐私状态：仅本地处理',
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          AppIcon(AppGlyph.lock, size: 18),
          SizedBox(width: AppSpacing.xs),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '仅本地处理',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
              ),
              Text(
                '数据不离开设备',
                style: TextStyle(fontSize: 11, color: Color(0xFFD5D9D9)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _CompactPrivacyStatus extends StatelessWidget {
  const _CompactPrivacyStatus();

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: '仅本地处理',
      child: Semantics(
        label: '隐私状态：仅本地处理',
        child: const Padding(
          padding: EdgeInsets.all(AppSpacing.s),
          child: AppIcon(AppGlyph.lock, size: 20),
        ),
      ),
    );
  }
}

class _SystemStatusBar extends StatelessWidget {
  const _SystemStatusBar({required this.indexedCount, required this.height});

  final int indexedCount;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      width: double.infinity,
      color: AppColors.navSecondary,
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.m),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < AppBreakpoints.compact;
          final largeText = ResponsiveLayout.usesLargeText(context);
          final showCount = !compact && !largeText;
          final showMethod =
              constraints.maxWidth >= AppBreakpoints.medium && !largeText;
          return Row(
            children: [
              const AppIcon(AppGlyph.offline, size: 17, color: Colors.white),
              const SizedBox(width: AppSpacing.xs),
              Text(
                compact ? '离线已就绪' : '离线检索已就绪',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
              if (showCount) ...[
                const SizedBox(width: AppSpacing.m),
                Container(width: 1, height: 16, color: const Color(0xFF697789)),
                const SizedBox(width: AppSpacing.m),
                Text(
                  '$indexedCount 个文件已索引',
                  style: const TextStyle(color: Colors.white, fontSize: 12),
                ),
              ],
              const Spacer(),
              if (showMethod)
                const Text(
                  '语义 + 关键词混合检索',
                  style: TextStyle(fontSize: 12, color: Color(0xFFD5D9D9)),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _Destination {
  const _Destination(this.label, this.icon, this.selectedIcon);

  final String label;
  final AppGlyph icon;
  final AppGlyph selectedIcon;
}

const _destinations = <_Destination>[
  _Destination('资料库', AppGlyph.library, AppGlyph.library),
  _Destination('搜索', AppGlyph.search, AppGlyph.search),
  _Destination('设置', AppGlyph.settings, AppGlyph.settings),
];
