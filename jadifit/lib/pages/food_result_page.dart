import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:jadi_fit_app/models/food_entry.dart';
import 'package:jadi_fit_app/services.auth/food_service.dart';
import 'package:jadi_fit_app/services.auth/image_storage_service.dart';

/// Shows the nutrition analysis result for a food item.
class FoodResultPage extends StatefulWidget {
  final String name;
  final int weightGrams;
  final String origin;
  final bool isOrganic;
  final bool saveToLibrary;
  final NutritionInfo nutrition;
  final String? imagePath;

  const FoodResultPage({
    super.key,
    required this.name,
    required this.weightGrams,
    this.origin = '',
    this.isOrganic = false,
    this.saveToLibrary = false,
    required this.nutrition,
    this.imagePath,
  });

  @override
  State<FoodResultPage> createState() => _FoodResultPageState();
}

class _FoodResultPageState extends State<FoodResultPage> {
  final _picker = ImagePicker();
  String? _currentImagePath;

  @override
  void initState() {
    super.initState();
    _currentImagePath = widget.imagePath;
  }

  String get _emoji {
    final lower = widget.name.toLowerCase();
    if (lower.contains('chicken')) return '🍗';
    if (lower.contains('rice')) return '🍚';
    if (lower.contains('salad')) return '🥗';
    if (lower.contains('egg')) return '🥚';
    if (lower.contains('fish') || lower.contains('salmon')) return '🐟';
    if (lower.contains('steak') || lower.contains('beef')) return '🥩';
    if (lower.contains('pasta') || lower.contains('noodle')) return '🍝';
    if (lower.contains('bread') || lower.contains('toast')) return '🍞';
    if (lower.contains('banana')) return '🍌';
    if (lower.contains('apple')) return '🍎';
    if (lower.contains('pizza')) return '🍕';
    if (lower.contains('burger')) return '🍔';
    return '🍽️';
  }

  Future<void> _takePhoto() async {
    final picked = await _picker.pickImage(source: ImageSource.camera);
    if (picked != null) {
      setState(() => _currentImagePath = picked.path);
    }
  }

  Future<void> _uploadPhoto() async {
    final picked = await _picker.pickImage(source: ImageSource.gallery);
    if (picked != null) {
      setState(() => _currentImagePath = picked.path);
    }
  }

  void _addToLog(BuildContext context) async {
    final provider = context.read<FoodProvider>();

    // ✅ Save image permanently if exists
    String? permanentImagePath;
    if (_currentImagePath != null) {
      try {
        permanentImagePath = await ImageStorageService.saveImagePermanently(_currentImagePath!);
      } catch (e) {
        print('⚠️ Failed to save image permanently: $e');
        permanentImagePath = _currentImagePath;
      }
    }

    provider.addEntry(
      name: widget.name,
      weightGrams: widget.weightGrams,
      origin: widget.origin,
      isOrganic: widget.isOrganic,
      nutrition: widget.nutrition,
      imagePath: permanentImagePath,
      saveToLibrary: widget.saveToLibrary,
    );

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Added to your food log'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );

    Navigator.pop(context);
  }

  void _saveToLib(BuildContext context) async {
    final provider = context.read<FoodProvider>();

    // ✅ Save image permanently if exists
    String? permanentImagePath;
    if (_currentImagePath != null) {
      try {
        permanentImagePath = await ImageStorageService.saveImagePermanently(_currentImagePath!);
      } catch (e) {
        print('⚠️ Failed to save image permanently: $e');
        permanentImagePath = _currentImagePath;
      }
    }

    provider.addEntry(
      name: widget.name,
      weightGrams: widget.weightGrams,
      origin: widget.origin,
      isOrganic: widget.isOrganic,
      nutrition: widget.nutrition,
      imagePath: permanentImagePath,
      saveToLibrary: true,
    );

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Saved to your library'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: theme.surface,
      body: SafeArea(
        child: Column(
          children: [
            // ── Header ──
            Container(
              color: theme.tertiary,
              padding: const EdgeInsets.fromLTRB(8, 12, 20, 16),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: Icon(Icons.arrow_back, color: theme.inversePrimary),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    'Food Analysis',
                    style: GoogleFonts.plusJakartaSans(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: theme.inversePrimary,
                    ),
                  ),
                ],
              ),
            ),

            // ── Content ──
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
                child: Column(
                  children: [
                    // Food image/illustration card
                    Container(
                      width: double.infinity,
                      height: 220,
                      decoration: BoxDecoration(
                        color: theme.tertiary,
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.05),
                            blurRadius: 10,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: _currentImagePath != null
                          ? Stack(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(20),
                            child: Image.file(
                              File(_currentImagePath!),
                              width: double.infinity,
                              height: double.infinity,
                              fit: BoxFit.cover,
                            ),
                          ),
                          // Camera buttons overlay
                          Positioned(
                            bottom: 12,
                            right: 12,
                            child: Row(
                              children: [
                                _SmallIconButton(
                                  icon: Icons.camera_alt,
                                  onTap: _takePhoto,
                                ),
                                const SizedBox(width: 8),
                                _SmallIconButton(
                                  icon: Icons.upload_rounded,
                                  onTap: _uploadPhoto,
                                ),
                              ],
                            ),
                          ),
                        ],
                      )
                          : Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            _emoji,
                            style: const TextStyle(fontSize: 72),
                          ),
                          const SizedBox(height: 16),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              _ActionButton(
                                icon: Icons.camera_alt,
                                label: 'Photo',
                                onTap: _takePhoto,
                              ),
                              const SizedBox(width: 12),
                              _ActionButton(
                                icon: Icons.upload_rounded,
                                label: 'Upload',
                                onTap: _uploadPhoto,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Nutrition summary card
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: theme.tertiary,
                        borderRadius: BorderRadius.circular(20),
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
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(
                                child: Text(
                                  widget.name,
                                  style: GoogleFonts.plusJakartaSans(
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                    color: theme.inversePrimary,
                                  ),
                                ),
                              ),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  ShaderMask(
                                    shaderCallback: (bounds) => LinearGradient(
                                      colors: [theme.primary, theme.secondary],
                                    ).createShader(bounds),
                                    child: Text(
                                      '${widget.nutrition.calories}',
                                      style: const TextStyle(
                                        fontSize: 28,
                                        fontWeight: FontWeight.bold,
                                        color: Colors.white,
                                      ),
                                    ),
                                  ),
                                  Text(
                                    'kcal',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: theme.onSurface,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),

                          const SizedBox(height: 8),
                          Text(
                            '${widget.weightGrams}g',
                            style: TextStyle(
                              fontSize: 14,
                              color: theme.onSurface,
                            ),
                          ),

                          const SizedBox(height: 16),

                          Row(
                            children: [
                              _MacroItem(
                                label: 'Protein',
                                value: '${widget.nutrition.protein}g',
                                theme: theme,
                              ),
                              _MacroItem(
                                label: 'Carbs',
                                value: '${widget.nutrition.carbs}g',
                                theme: theme,
                              ),
                              _MacroItem(
                                label: 'Fats',
                                value: '${widget.nutrition.fats}g',
                                theme: theme,
                                showBorder: false,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: _buildGradientButton(
                        context,
                        icon: Icons.add,
                        label: 'Add to Log',
                        onTap: () => _addToLog(context),
                      ),
                    ),

                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(
                          child: SizedBox(
                            height: 48,
                            child: _buildOutlinedButton(
                              context,
                              icon: Icons.edit_outlined,
                              label: 'Edit',
                              onTap: () => Navigator.pop(context),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: SizedBox(
                            height: 48,
                            child: _buildOutlinedButton(
                              context,
                              icon: Icons.bookmark_add_outlined,
                              label: 'Save',
                              onTap: () => _saveToLib(context),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGradientButton(
      BuildContext context, {
        required IconData icon,
        required String label,
        required VoidCallback onTap,
      }) {
    final theme = Theme.of(context).colorScheme;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(colors: [theme.primary, theme.secondary]),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: theme.onPrimary, size: 20),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  color: theme.onPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOutlinedButton(
      BuildContext context, {
        required IconData icon,
        required String label,
        required VoidCallback onTap,
      }) {
    final theme = Theme.of(context).colorScheme;
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, size: 18),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: theme.inversePrimary,
        side: BorderSide(color: theme.outline.withOpacity(0.3)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }
}

class _MacroItem extends StatelessWidget {
  final String label;
  final String value;
  final ColorScheme theme;
  final bool showBorder;

  const _MacroItem({
    required this.label,
    required this.value,
    required this.theme,
    this.showBorder = true,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          border: showBorder
              ? Border(right: BorderSide(color: theme.outline.withOpacity(0.2)))
              : null,
        ),
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: theme.inversePrimary,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: theme.onSurface.withOpacity(0.7),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SmallIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _SmallIconButton({
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    return Material(
      color: theme.surface.withOpacity(0.9),
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.all(10),
          child: Icon(icon, size: 20, color: theme.inversePrimary),
        ),
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    return Material(
      color: theme.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 18, color: theme.primary),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: theme.inversePrimary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}