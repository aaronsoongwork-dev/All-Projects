import 'package:flutter/material.dart';

class BottomNavBar extends StatelessWidget {
  final int selectedIndex;
  final Function(int) onItemTapped;

  const BottomNavBar({
    super.key,
    required this.selectedIndex,
    required this.onItemTapped,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;

    return Container(
      decoration: BoxDecoration(
        color: theme.tertiary,
        border: Border(
          top: BorderSide(
            color: theme.outline.withOpacity(0.15),
            width: 1,
          ),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 24,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 65, // FIXED: Reduced from 72 to prevent overflow
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem(
                Icons.home_rounded,
                Icons.home_outlined,
                'Home',
                0,
                theme,
              ),
              _buildNavItem(
                Icons.restaurant_rounded,
                Icons.restaurant_outlined,
                'Food',
                1,
                theme,
              ),
              _buildNavItem(
                Icons.calendar_today_rounded,
                Icons.calendar_today_outlined,
                'Planner',
                2,
                theme,
              ),
              _buildNavItem(
                Icons.settings_rounded,
                Icons.settings_outlined,
                'Settings',
                3,
                theme,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(
      IconData activeIcon,
      IconData inactiveIcon,
      String label,
      int index,
      ColorScheme theme,
      ) {
    final isActive = selectedIndex == index;

    return Expanded(
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => onItemTapped(index),
          splashColor: theme.primary.withOpacity(0.1),
          highlightColor: theme.primary.withOpacity(0.05),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 6), // FIXED: Reduced padding
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                // Icon with animated container
                AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14, // FIXED: Reduced from 16
                    vertical: 4,    // FIXED: Reduced from 6
                  ),
                  decoration: BoxDecoration(
                    gradient: isActive
                        ? LinearGradient(
                      colors: [
                        theme.primary.withOpacity(0.15),
                        theme.secondary.withOpacity(0.15),
                      ],
                    )
                        : null,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    isActive ? activeIcon : inactiveIcon,
                    color: isActive
                        ? theme.primary
                        : theme.onSurface.withOpacity(0.5),
                    size: 24, // FIXED: Reduced from 26
                  ),
                ),
                const SizedBox(height: 2), // FIXED: Reduced from 4
                // Label
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 11, // FIXED: Reduced from 12
                    fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                    color: isActive
                        ? theme.primary
                        : theme.onSurface.withOpacity(0.6),
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