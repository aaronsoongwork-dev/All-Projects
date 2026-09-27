import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:jadi_fit_app/pages/food_checker_page.dart';
import 'package:jadi_fit_app/pages/food_history_page.dart';

/// Container page for the Food tab – switches between Checker and History.
class FoodPage extends StatefulWidget {
  const FoodPage({super.key});

  @override
  State<FoodPage> createState() => _FoodPageState();
}

class _FoodPageState extends State<FoodPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;

    return SafeArea(
      child: Column(
        children: [
          // ── Header ──
          Container(
            color: theme.surface, // ✅ CHANGED: Use surface color instead of tertiary
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 16), // ✅ FIXED: Consistent padding
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Food',
                  style: GoogleFonts.plusJakartaSans(
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                    color: theme.inversePrimary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Track & analyze your meals',
                  style: TextStyle(
                    fontSize: 13,
                    color: theme.onSurface,
                  ),
                ),
                const SizedBox(height: 16),

                // ── Segmented tab bar ──
                Container(
                  height: 44, // ✅ INCREASED slightly for better touch target
                  decoration: BoxDecoration(
                    color: theme.tertiary, // ✅ Background for tabs
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.all(4), // ✅ Inner padding
                  child: Row(
                    children: [
                      _TabSegment(
                        label: 'Checker',
                        icon: Icons.camera_alt_outlined,
                        isActive: _tabController.index == 0,
                        onTap: () => _tabController.animateTo(0),
                      ),
                      _TabSegment(
                        label: 'History',
                        icon: Icons.history,
                        isActive: _tabController.index == 1,
                        onTap: () => _tabController.animateTo(1),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // ── Tab content ──
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: const [
                FoodCheckerPage(),
                FoodHistoryPage(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TabSegment extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool isActive;
  final VoidCallback onTap;

  const _TabSegment({
    required this.label,
    required this.icon,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;

    return Expanded(
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(10),
          splashColor: Colors.transparent, // ✅ REMOVED splash
          highlightColor: Colors.transparent, // ✅ REMOVED highlight
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(10),
              gradient: isActive
                  ? LinearGradient(colors: [theme.primary, theme.secondary])
                  : null,
            ),
            child: Center( // ✅ CENTERED content properly
              child: Row(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    icon,
                    size: 18,
                    color: isActive
                        ? theme.onPrimary
                        : theme.onSurface.withOpacity(0.6),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    label,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: isActive ? FontWeight.w600 : FontWeight.w500,
                      color: isActive
                          ? theme.onPrimary
                          : theme.onSurface.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}