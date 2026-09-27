import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:jadi_fit_app/models/food_entry.dart';
import 'package:jadi_fit_app/services.auth/food_service.dart';
import 'package:jadi_fit_app/pages/food_result_page.dart';

/// Displays a list of previously tracked food entries grouped by date.
class FoodHistoryPage extends StatefulWidget {
  const FoodHistoryPage({super.key});

  @override
  State<FoodHistoryPage> createState() => _FoodHistoryPageState();
}

class _FoodHistoryPageState extends State<FoodHistoryPage> {
  String _activeFilter = 'all'; // 'all', 'today', 'saved'

  List<FoodEntry> _filteredEntries(FoodProvider provider) {
    switch (_activeFilter) {
      case 'today':
        return provider.todayEntries;
      case 'saved':
        return provider.savedEntries;
      default:
        return provider.entries;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;

    return Consumer<FoodProvider>(
      builder: (context, provider, _) {
        final entries = _filteredEntries(provider);
        final grouped = <String, List<FoodEntry>>{};
        for (final entry in entries) {
          grouped.putIfAbsent(entry.formattedDate, () => []).add(entry);
        }

        return SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Filter chips ──
              Row(
                children: [
                  _FilterChip(
                    label: 'All',
                    isActive: _activeFilter == 'all',
                    onTap: () => setState(() => _activeFilter = 'all'),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Today',
                    isActive: _activeFilter == 'today',
                    onTap: () => setState(() => _activeFilter = 'today'),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Saved',
                    isActive: _activeFilter == 'saved',
                    onTap: () => setState(() => _activeFilter = 'saved'),
                  ),
                ],
              ),

              const SizedBox(height: 20),

              // ── Summary card ──
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      theme.primary.withOpacity(0.08),
                      theme.secondary.withOpacity(0.04),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: theme.primary.withOpacity(0.15),
                  ),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Today\'s Intake',
                            style: GoogleFonts.plusJakartaSans(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: theme.inversePrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${provider.todayEntries.length} items logged',
                            style: TextStyle(
                              fontSize: 13,
                              color: theme.onSurface,
                            ),
                          ),
                          const SizedBox(height: 12),
                          ShaderMask(
                            shaderCallback: (bounds) => LinearGradient(
                              colors: [theme.primary, theme.secondary],
                            ).createShader(bounds),
                            child: Text(
                              '${provider.todayCalories} kcal',
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Text('🍽️', style: TextStyle(fontSize: 40)),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // ── Entry list ──
              if (entries.isEmpty)
                _EmptyState(filter: _activeFilter)
              else
                ...grouped.entries.map((group) => _DateGroup(
                  dateLabel: group.key,
                  entries: group.value,
                )),
            ],
          ),
        );
      },
    );
  }
}

// ════════════════════════════════════════════════════════════
//  Widgets
// ════════════════════════════════════════════════════════════

class _FilterChip extends StatelessWidget {
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          gradient: isActive
              ? LinearGradient(colors: [theme.primary, theme.secondary])
              : null,
          color: isActive ? null : theme.tertiary,
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: isActive ? theme.onPrimary : theme.onSurface,
          ),
        ),
      ),
    );
  }
}

class _DateGroup extends StatelessWidget {
  final String dateLabel;
  final List<FoodEntry> entries;

  const _DateGroup({required this.dateLabel, required this.entries});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    final totalCal = entries.fold(0, (sum, e) => sum + e.nutrition.calories);

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Date header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                dateLabel,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: theme.inversePrimary,
                ),
              ),
              Text(
                '$totalCal kcal',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: theme.onSurface,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Entry cards
          ...entries.map((entry) => _FoodEntryCard(entry: entry)),
        ],
      ),
    );
  }
}

class _FoodEntryCard extends StatelessWidget {
  final FoodEntry entry;

  const _FoodEntryCard({required this.entry});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Dismissible(
        key: Key(entry.id),
        direction: DismissDirection.endToStart,
        background: Container(
          alignment: Alignment.centerRight,
          padding: const EdgeInsets.only(right: 20),
          decoration: BoxDecoration(
            color: Colors.red.withOpacity(0.1),
            borderRadius: BorderRadius.circular(16),
          ),
          child: const Icon(Icons.delete_outline, color: Colors.red),
        ),
        onDismissed: (_) {
          context.read<FoodProvider>().removeEntry(entry.id);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('${entry.name} removed'),
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          );
        },
        child: InkWell(
          // ✅ Navigate to FoodResultPage on tap
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => FoodResultPage(
                  name: entry.name,
                  weightGrams: entry.weightGrams,
                  origin: entry.origin,
                  isOrganic: entry.isOrganic,
                  saveToLibrary: entry.savedToLibrary,
                  nutrition: entry.nutrition,
                  imagePath: entry.imagePath,
                ),
              ),
            );
          },
          borderRadius: BorderRadius.circular(16),
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: theme.tertiary,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              children: [
                // Emoji avatar
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: theme.primary.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Center(
                    child: Text(entry.emoji, style: const TextStyle(fontSize: 22)),
                  ),
                ),
                const SizedBox(width: 12),

                // Name, weight, time
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              entry.name,
                              style: GoogleFonts.plusJakartaSans(
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                                color: theme.inversePrimary,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          if (entry.savedToLibrary)
                            Padding(
                              padding: const EdgeInsets.only(left: 4),
                              child: Icon(
                                Icons.bookmark,
                                size: 14,
                                color: theme.primary,
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 3),
                      Text(
                        '${entry.weightGrams}g • ${entry.formattedTime}',
                        style: TextStyle(
                          fontSize: 12,
                          color: theme.onSurface,
                        ),
                      ),
                    ],
                  ),
                ),

                // Macros summary
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    ShaderMask(
                      shaderCallback: (bounds) => LinearGradient(
                        colors: [theme.primary, theme.secondary],
                      ).createShader(bounds),
                      child: Text(
                        '${entry.nutrition.calories}',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    Text(
                      'kcal',
                      style: TextStyle(
                        fontSize: 11,
                        color: theme.onSurface,
                      ),
                    ),
                  ],
                ),

                const SizedBox(width: 4),
                Icon(
                  Icons.chevron_right,
                  size: 20,
                  color: theme.onSurface.withOpacity(0.4),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final String filter;

  const _EmptyState({required this.filter});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    String message;
    switch (filter) {
      case 'today':
        message = 'No food logged today.\nUse the checker to add your first meal!';
        break;
      case 'saved':
        message = 'No saved foods yet.\nSave items from the food checker.';
        break;
      default:
        message = 'No food entries yet.\nStart tracking your meals!';
    }

    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 60),
        child: Column(
          children: [
            Icon(
              Icons.restaurant_outlined,
              size: 48,
              color: theme.onSurface.withOpacity(0.25),
            ),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                color: theme.onSurface,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}