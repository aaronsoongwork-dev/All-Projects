import 'package:flutter/material.dart';
import 'package:jadi_fit_app/themes/theme_selector.dart';
import 'package:provider/provider.dart';

class ThemeSettingsPage extends StatelessWidget {
  const ThemeSettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.isDarkMode;

    return Scaffold(
      backgroundColor: theme.surface,
      appBar: AppBar(
        backgroundColor: theme.surface,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: theme.inversePrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Theme',
          style: TextStyle(
            color: theme.inversePrimary,
            fontWeight: FontWeight.w800,
            fontFamily: 'Helvetica',
            fontSize: 18,
          ),
        ),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 40),
        children: [
          Text(
            'Choose your preferred appearance',
            style: TextStyle(fontSize: 13, color: theme.onSurface),
          ),
          const SizedBox(height: 24),

          // ── Theme options ───────────────────────────
          _themeOption(
            context: context,
            icon: Icons.light_mode,
            title: 'Light',
            subtitle: 'Clean & bright appearance',
            selected: !isDark,
            theme: theme,
            onTap: () {
              if (isDark) themeProvider.toggleTheme();
            },
          ),
          const SizedBox(height: 10),
          _themeOption(
            context: context,
            icon: Icons.dark_mode,
            title: 'Dark',
            subtitle: 'Easy on the eyes',
            selected: isDark,
            theme: theme,
            onTap: () {
              if (!isDark) themeProvider.toggleTheme();
            },
          ),

          const SizedBox(height: 32),

          // ── Preview card ────────────────────────────
          Text(
            'Preview',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: theme.onSurface,
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: theme.tertiary,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: theme.outline.withOpacity(0.2)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [theme.primary, theme.secondary],
                        ),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Icon(Icons.fitness_center,
                          size: 22, color: theme.onPrimary),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Sample Workout',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                              color: theme.inversePrimary,
                            ),
                          ),
                          Text(
                            '3 exercises • 1/3 done',
                            style: TextStyle(
                              fontSize: 12,
                              color: theme.onSurface,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: 0.33,
                    minHeight: 6,
                    backgroundColor: theme.outline.withOpacity(0.3),
                    valueColor: AlwaysStoppedAnimation(theme.primary),
                  ),
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    _previewTag('Primary', theme.primary, theme.onPrimary),
                    const SizedBox(width: 8),
                    _previewTag(
                        'Surface', theme.tertiary, theme.inversePrimary,
                        border: theme.outline.withOpacity(0.3)),
                    const SizedBox(width: 8),
                    _previewTag('Text', theme.surface, theme.inversePrimary,
                        border: theme.outline.withOpacity(0.3)),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _themeOption({
    required BuildContext context,
    required IconData icon,
    required String title,
    required String subtitle,
    required bool selected,
    required ColorScheme theme,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        decoration: BoxDecoration(
          color: theme.tertiary,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: selected ? theme.primary : theme.outline.withOpacity(0.2),
            width: selected ? 1.5 : 1,
          ),
          boxShadow: selected
              ? [
                  BoxShadow(
                    color: theme.primary.withOpacity(0.08),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ]
              : null,
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: selected
                    ? theme.primary.withOpacity(0.1)
                    : theme.outline.withOpacity(0.15),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(
                icon,
                size: 22,
                color: selected ? theme.primary : theme.onSurface,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: theme.inversePrimary,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(fontSize: 12, color: theme.onSurface),
                  ),
                ],
              ),
            ),
            if (selected)
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: theme.primary,
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.check, size: 14, color: theme.onPrimary),
              )
            else
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: theme.outline.withOpacity(0.4),
                    width: 1.5,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _previewTag(String label, Color bg, Color fg, {Color? border}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
        border: border != null ? Border.all(color: border) : null,
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w500,
          color: fg,
        ),
      ),
    );
  }
}
