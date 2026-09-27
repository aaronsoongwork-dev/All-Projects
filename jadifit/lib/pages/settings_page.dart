import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:jadi_fit_app/pages/edit_profile_page.dart';
import 'package:jadi_fit_app/pages/theme_settings_page.dart';
import 'package:jadi_fit_app/services.auth/auth_service.dart';
import 'package:jadi_fit_app/services.auth/user_provider.dart';
import 'package:jadi_fit_app/pages/welcome_screen.dart';
import 'package:provider/provider.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    final AuthService authService = AuthService();

    return Consumer<UserProvider>(
      builder: (context, userProvider, child) {
        if (userProvider.isLoading) {
          return const Center(child: CircularProgressIndicator());
        }

        return Scaffold(
          backgroundColor: theme.surface,
          body: SafeArea(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 40),
              children: [
                // ── Header ────────────────────────────────────
                Text(
                  'Settings',
                  style: GoogleFonts.plusJakartaSans(
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                    color: theme.inversePrimary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Manage your account and preferences',
                  style: TextStyle(fontSize: 13, color: theme.onSurface),
                ),

                const SizedBox(height: 24),

                // ── Profile card ─────────────────────────────��
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: theme.tertiary,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: theme.outline.withOpacity(0.2),
                    ),
                  ),
                  child: Row(
                    children: [
                      // Avatar
                      Container(
                        width: 64,
                        height: 64,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [theme.primary, theme.secondary],
                          ),
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Text(
                            userProvider.displayName.isNotEmpty
                                ? userProvider.displayName[0].toUpperCase()
                                : 'U',
                            style: TextStyle(
                              color: theme.onPrimary,
                              fontSize: 28,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),

                      // Name & Email
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              userProvider.displayName,
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: theme.inversePrimary,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              userProvider.email,
                              style: TextStyle(
                                fontSize: 13,
                                color: theme.onSurface,
                              ),
                            ),
                          ],
                        ),
                      ),

                      // Edit Button
                      GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const EditProfilePage(isFirstTime: false), // ← Add this parameter
                            ),
                          );
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 14,
                            vertical: 7,
                          ),
                          decoration: BoxDecoration(
                            color: theme.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            'Edit',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: theme.primary,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 35),

                _settingsTile(
                  icon: Icons.palette_outlined,
                  title: 'Themes',
                  subtitle: 'Customize appearance',
                  theme: theme,
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const ThemeSettingsPage()),
                  ),
                ),
                _settingsTile(
                  icon: Icons.notifications_none_rounded,
                  title: 'Notifications',
                  subtitle: 'Manage alerts',
                  theme: theme,
                  onTap: () {},
                ),
                _settingsTile(
                  icon: Icons.help_outline_rounded,
                  title: 'Support',
                  subtitle: 'Get help',
                  theme: theme,
                  onTap: () {},
                ),
                _settingsTile(
                  icon: Icons.info_outline_rounded,
                  title: 'About JadiFit',
                  subtitle: 'Version 1.0.0',
                  theme: theme,
                  onTap: () {},
                ),

                const SizedBox(height: 35),

                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () async {
                      // SIMPLE ALERTDIALOG - NO GLASS EFFECT
                      final confirm = await showDialog<bool>(
                        context: context,
                        builder: (context) => AlertDialog(
                          backgroundColor: theme.surface,
                          title: Text(
                            'Sign Out',
                            style: TextStyle(color: theme.inversePrimary),
                          ),
                          content: Text(
                            'Are you sure you want to sign out?',
                            style: TextStyle(color: theme.onSurface),
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(context, false),
                              child: const Text('Cancel'),
                            ),
                            TextButton(
                              onPressed: () => Navigator.pop(context, true),
                              child: const Text(
                                'Sign Out',
                                style: TextStyle(color: Colors.red),
                              ),
                            ),
                          ],
                        ),
                      );

                      if (confirm == true && context.mounted) {
                        await authService.signOut();
                        context.read<UserProvider>().clearData();
                        Navigator.of(context).pushAndRemoveUntil(
                          MaterialPageRoute(builder: (context) => const WelcomeScreen()),
                              (route) => false,
                        );
                      }
                    },
                    icon: const Icon(Icons.logout, size: 18, color: Colors.red),
                    label: const Text(
                      'Sign Out',
                      style: TextStyle(color: Colors.red),
                    ),
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(color: Colors.red.withOpacity(0.3)),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ── helpers ──────────────────────────────────────────────

  Widget _sectionTitle(String text, ColorScheme theme) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: theme.onSurface,
        letterSpacing: 0.5,
      ),
    );
  }

  Widget _settingsTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required ColorScheme theme,
    required VoidCallback onTap,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: theme.tertiary,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: theme.primary.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(icon, size: 20, color: theme.primary),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                          color: theme.inversePrimary,
                        ),
                      ),
                      Text(
                        subtitle,
                        style: TextStyle(
                          fontSize: 12,
                          color: theme.onSurface,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(
                  Icons.chevron_right,
                  size: 20,
                  color: theme.onSurface.withOpacity(0.5),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}