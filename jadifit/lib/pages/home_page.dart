import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:jadi_fit_app/components/circular_progress_widget.dart';
import 'package:jadi_fit_app/components/stat_card.dart';
import 'package:jadi_fit_app/components/bottom_nav_bar.dart';
import 'package:jadi_fit_app/pages/food_page.dart';
import 'package:jadi_fit_app/pages/planner_page.dart';
import 'package:jadi_fit_app/pages/settings_page.dart';
import 'package:jadi_fit_app/services.auth/user_provider.dart';
import 'package:provider/provider.dart';

import 'edit_profile_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedIndex = 0;

  void _onNavItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: Column(
        children: [
          Expanded(
            child: IndexedStack(
              index: _selectedIndex,
              children: [
                // 0 – Home
                _buildHomePage(),
                // 1 – Food
                const FoodPage(),
                // 2 – Planner
                const PlannerPage(),
                // 3 – Settings
                const SettingsPage(),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: BottomNavBar(
        selectedIndex: _selectedIndex,
        onItemTapped: _onNavItemTapped,
      ),
    );
  }

  Widget _buildHomePage() {
    final theme = Theme.of(context).colorScheme;

    return Consumer<UserProvider>(
      builder: (context, userProvider, child) {
        if (userProvider.isLoading) {
          return const Center(child: CircularProgressIndicator());
        }

        // If profile not complete, show prompt
        if (!userProvider.isProfileComplete) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.person_outline,
                    size: 80,
                    color: theme.primary.withOpacity(0.5),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Complete Your Profile',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: theme.inversePrimary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Add your personal info to see your fitness stats and track progress.',
                    style: TextStyle(
                      fontSize: 16,
                      color: theme.onSurface,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 32),
                  ElevatedButton.icon(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const EditProfilePage(isFirstTime: true),
                        ),
                      );
                    },
                    icon: const Icon(Icons.edit),
                    label: const Text('Complete Profile'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: theme.primary,
                      foregroundColor: theme.onPrimary,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 32,
                        vertical: 16,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        return SafeArea(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Header ────────────────────────────────────
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Hello, ${userProvider.firstName}!',
                            style: GoogleFonts.plusJakartaSans(
                              fontSize: 26,
                              fontWeight: FontWeight.bold,
                              color: theme.inversePrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Ready to crush your goals?',
                            style: TextStyle(
                              fontSize: 14,
                              color: theme.onSurface,
                            ),
                          ),
                        ],
                      ),
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [theme.primary, theme.secondary],
                          ),
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Text(
                            userProvider.firstName.isNotEmpty
                                ? userProvider.firstName[0].toUpperCase()
                                : 'U',
                            style: TextStyle(
                              color: theme.onPrimary,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 32),

                  // ── Your Stats ────────────────────────────────
                  Text(
                    'Your Stats',
                    style: GoogleFonts.plusJakartaSans(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: theme.inversePrimary,
                    ),
                  ),
                  const SizedBox(height: 16),

                  Row(
                    children: [
                      Expanded(
                        child: StatCard(
                          icon: Icons.monitor_weight_outlined,
                          label: 'Weight',
                          value: '${userProvider.weight.toStringAsFixed(1)} kg',
                          progress: userProvider.weightProgress,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _buildBMICard(context, userProvider),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  Row(
                    children: [
                      Expanded(
                        child: StatCard(
                          icon: Icons.local_fire_department_outlined,
                          label: 'Burned Today',
                          value: '${userProvider.currentDailyCaloriesBurned} kcal',
                          progress: userProvider.calorieBurnProgress,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: StatCard(
                          icon: Icons.fitness_center_outlined,
                          label: 'Workouts',
                          value: userProvider.weeklyWorkoutGoal > 0
                              ? '${userProvider.currentWeeklyWorkouts}/${userProvider.weeklyWorkoutGoal}'
                              : '${userProvider.currentWeeklyWorkouts}',
                          progress: userProvider.workoutProgress,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 32),

                  // ── Quick Actions ─────────────────────────────
                  Text(
                    'Quick Actions',
                    style: GoogleFonts.plusJakartaSans(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: theme.inversePrimary,
                    ),
                  ),
                  const SizedBox(height: 16),

                  Row(
                    children: [
                      Expanded(
                        child: _buildQuickActionCard(
                          context,
                          icon: Icons.restaurant,
                          label: 'Log Food',
                          onTap: () => setState(() => _selectedIndex = 1),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _buildQuickActionCard(
                          context,
                          icon: Icons.calendar_today,
                          label: 'Plan Workout',
                          onTap: () => setState(() => _selectedIndex = 2),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildBMICard(BuildContext context, UserProvider userProvider) {
    final theme = Theme.of(context).colorScheme;
    final bmi = userProvider.bmi;

    // Determine BMI category and color
    Color bmiColor;
    String bmiCategory;
    double bmiProgress;

    if (bmi < 18.5) {
      bmiColor = Colors.blue;
      bmiCategory = 'Underweight';
      bmiProgress = (bmi / 18.5).clamp(0.0, 1.0);
    } else if (bmi < 25) {
      bmiColor = Colors.green;
      bmiCategory = 'Normal';
      bmiProgress = ((bmi - 18.5) / (25 - 18.5)).clamp(0.0, 1.0);
    } else if (bmi < 30) {
      bmiColor = Colors.orange;
      bmiCategory = 'Overweight';
      bmiProgress = ((bmi - 25) / (30 - 25)).clamp(0.0, 1.0);
    } else {
      bmiColor = Colors.red;
      bmiCategory = 'Obese';
      bmiProgress = 1.0;
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.tertiary,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon with gradient
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [bmiColor, bmiColor.withOpacity(0.7)],
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              Icons.analytics_outlined,
              color: Colors.white,
              size: 22,
            ),
          ),
          const SizedBox(height: 12),

          // BMI Value
          ShaderMask(
            shaderCallback: (bounds) => LinearGradient(
              colors: [bmiColor, bmiColor.withOpacity(0.8)],
            ).createShader(bounds),
            child: Text(
              bmi.toStringAsFixed(1),
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(height: 4),

          // Label
          Text(
            'BMI • $bmiCategory',
            style: TextStyle(
              fontSize: 13,
              color: theme.onSurface,
              fontWeight: FontWeight.w500,
            ),
          ),

          const SizedBox(height: 12),

          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: bmiProgress,
              backgroundColor: theme.outline.withOpacity(0.2),
              valueColor: AlwaysStoppedAnimation<Color>(bmiColor),
              minHeight: 6,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionCard(
      BuildContext context, {
        required IconData icon,
        required String label,
        required VoidCallback onTap,
      }) {
    final theme = Theme.of(context).colorScheme;

    return Material(
      color: theme.tertiary,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [theme.primary, theme.secondary],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: theme.onPrimary, size: 24),
              ),
              const SizedBox(height: 12),
              Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: theme.inversePrimary,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}