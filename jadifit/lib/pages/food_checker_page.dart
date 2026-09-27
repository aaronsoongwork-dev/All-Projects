import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:jadi_fit_app/models/food_entry.dart';
import 'package:jadi_fit_app/pages/food_result_page.dart';
import 'package:jadi_fit_app/services.auth/ai_food_service.dart';

/// Food capture / checker screen – with TFLite + Gemini AI analysis
class FoodCheckerPage extends StatefulWidget {
  const FoodCheckerPage({super.key});

  @override
  State<FoodCheckerPage> createState() => _FoodCheckerPageState();
}

class _FoodCheckerPageState extends State<FoodCheckerPage> {
  final _nameController = TextEditingController();
  final _weightController = TextEditingController();
  final _originController = TextEditingController();
  bool _isOrganic = false;
  bool _saveToLibrary = true; // Default to true
  File? _imageFile;
  bool _isAnalyzing = false;

  final _picker = ImagePicker();
  final _aiFoodService = AIFoodService();

  @override
  void initState() {
    super.initState();
    _initializeService();
  }

  Future<void> _initializeService() async {
    try {
      await _aiFoodService.initialize();
      print('✅ Hybrid food service ready');
    } catch (e) {
      print('❌ Failed to initialize service: $e');
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _weightController.dispose();
    _originController.dispose();
    _aiFoodService.dispose();
    super.dispose();
  }

  Future<void> _takePhoto() async {
    final picked = await _picker.pickImage(
      source: ImageSource.camera,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 85,
    );
    if (picked != null) {
      setState(() => _imageFile = File(picked.path));
    }
  }

  Future<void> _uploadPhoto() async {
    final picked = await _picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 85,
    );
    if (picked != null) {
      setState(() => _imageFile = File(picked.path));
    }
  }

  void _analyzeFood() async {
    if (_imageFile == null) {
      _showError('Please take or upload a photo first');
      return;
    }

    setState(() => _isAnalyzing = true);

    try {
      // 🤖 Hybrid AI Analysis: TFLite detection → Gemini nutrition
      final result = await _aiFoodService.analyzeFoodImage(_imageFile!.path);

      if (!mounted) return;

      setState(() => _isAnalyzing = false);

      // Navigate to result page with AI data
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => FoodResultPage(
            name: result.name,
            weightGrams: result.weightGrams,
            origin: result.origin,
            isOrganic: result.isOrganic,
            saveToLibrary: _saveToLibrary,
            nutrition: result.nutrition,
            imagePath: _imageFile!.path,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _isAnalyzing = false);
      _showError('Analysis failed: ${e.toString()}');
    }
  }

  void _manualAnalyze() {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      _showError('Please enter a food name');
      return;
    }

    final weight = int.tryParse(_weightController.text.trim()) ?? 100;

    // Simulated nutrition analysis based on weight
    final caloriesPer100g = _estimateCaloriesPer100g(name);
    final proteinPer100g = _estimateProteinPer100g(name);
    final carbsPer100g = _estimateCarbsPer100g(name);
    final fatsPer100g = _estimateFatsPer100g(name);

    final scale = weight / 100.0;

    final nutrition = NutritionInfo(
      calories: (caloriesPer100g * scale).round(),
      protein: (proteinPer100g * scale).round(),
      carbs: (carbsPer100g * scale).round(),
      fats: (fatsPer100g * scale).round(),
    );

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => FoodResultPage(
          name: name,
          weightGrams: weight,
          origin: _originController.text.trim(),
          isOrganic: _isOrganic,
          saveToLibrary: _saveToLibrary,
          nutrition: nutrition,
          imagePath: _imageFile?.path,
        ),
      ),
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Theme.of(context).colorScheme.error,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  // Simple heuristic calorie estimators (fallback)
  int _estimateCaloriesPer100g(String name) {
    final lower = name.toLowerCase();
    if (lower.contains('chicken') || lower.contains('fish')) return 165;
    if (lower.contains('rice')) return 130;
    if (lower.contains('salad')) return 30;
    if (lower.contains('pasta')) return 160;
    if (lower.contains('bread')) return 265;
    if (lower.contains('pizza')) return 266;
    if (lower.contains('burger')) return 295;
    if (lower.contains('egg')) return 155;
    return 100;
  }

  int _estimateProteinPer100g(String name) {
    final lower = name.toLowerCase();
    if (lower.contains('chicken')) return 31;
    if (lower.contains('fish')) return 20;
    if (lower.contains('egg')) return 13;
    if (lower.contains('beef') || lower.contains('steak')) return 26;
    if (lower.contains('tofu')) return 8;
    return 5;
  }

  int _estimateCarbsPer100g(String name) {
    final lower = name.toLowerCase();
    if (lower.contains('rice')) return 28;
    if (lower.contains('pasta')) return 31;
    if (lower.contains('bread')) return 49;
    if (lower.contains('potato')) return 17;
    if (lower.contains('banana')) return 23;
    if (lower.contains('pizza')) return 33;
    if (lower.contains('burger')) return 28;
    return 15;
  }

  int _estimateFatsPer100g(String name) {
    final lower = name.toLowerCase();
    if (lower.contains('salmon')) return 13;
    if (lower.contains('avocado')) return 15;
    if (lower.contains('cheese')) return 33;
    if (lower.contains('nuts')) return 50;
    if (lower.contains('butter')) return 81;
    if (lower.contains('pizza')) return 10;
    if (lower.contains('burger')) return 14;
    if (lower.contains('egg')) return 11;
    return 5;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Camera Area ──
          Container(
            padding: const EdgeInsets.all(24),
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
              children: [
                // Image preview area
                Container(
                  height: 220,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: theme.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: theme.outline.withOpacity(0.3)),
                  ),
                  child: _imageFile != null
                      ? ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.file(
                      _imageFile!,
                      fit: BoxFit.cover,
                      width: double.infinity,
                    ),
                  )
                      : Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.camera_alt_outlined,
                        size: 56,
                        color: theme.onSurface.withOpacity(0.3),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Place food in frame',
                        style: TextStyle(
                          color: theme.onSurface.withOpacity(0.5),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Camera & upload buttons
                Row(
                  children: [
                    Expanded(
                      child: _GradientButton(
                        onTap: _takePhoto,
                        icon: Icons.camera_alt,
                        label: 'Take Photo',
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _OutlinedButton(
                        onTap: _uploadPhoto,
                        icon: Icons.upload_rounded,
                        label: 'Upload',
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // ── Save to Library Toggle (Prominent) ──
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.primaryContainer.withOpacity(0.3),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: theme.primary.withOpacity(0.2),
              ),
            ),
            child: _ToggleRow(
              label: '💾 Save to Food Library',
              value: _saveToLibrary,
              onChanged: (v) => setState(() => _saveToLibrary = v),
            ),
          ),

          const SizedBox(height: 16),

          // ── AI Analyze Button (Primary) ──
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton(
              onPressed: _isAnalyzing ? null : _analyzeFood,
              style: ElevatedButton.styleFrom(
                backgroundColor: theme.primary,
                foregroundColor: theme.onPrimary,
                disabledBackgroundColor: theme.primary.withOpacity(0.6),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                elevation: 2,
              ),
              child: _isAnalyzing
                  ? Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'Analyzing with AI...',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: theme.onPrimary.withOpacity(0.9),
                    ),
                  ),
                ],
              )
                  : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.auto_awesome, size: 20),
                  const SizedBox(width: 8),
                  const Text(
                    'Analyze with AI',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // ── OR Divider ──
          Row(
            children: [
              Expanded(child: Divider(color: theme.outline.withOpacity(0.3))),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Text(
                  'OR ENTER MANUALLY',
                  style: TextStyle(
                    fontSize: 12,
                    color: theme.onSurface.withOpacity(0.6),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Expanded(child: Divider(color: theme.outline.withOpacity(0.3))),
            ],
          ),

          const SizedBox(height: 20),

          // ── Food Information (Manual Entry) ──
          Container(
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
                Text(
                  'Food Information',
                  style: GoogleFonts.plusJakartaSans(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: theme.inversePrimary,
                  ),
                ),
                const SizedBox(height: 16),

                _InputField(
                  label: 'Food Name',
                  hint: 'e.g., Grilled Chicken',
                  controller: _nameController,
                ),
                const SizedBox(height: 14),

                _InputField(
                  label: 'Weight (g)',
                  hint: '150',
                  controller: _weightController,
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 14),

                _InputField(
                  label: 'Origin',
                  hint: 'e.g., Local farm',
                  controller: _originController,
                ),
                const SizedBox(height: 14),

                // Organic toggle
                _ToggleRow(
                  label: 'Organic',
                  value: _isOrganic,
                  onChanged: (v) => setState(() => _isOrganic = v),
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // ── Manual Analyze Button (Secondary) ──
          SizedBox(
            width: double.infinity,
            height: 48,
            child: OutlinedButton(
              onPressed: _manualAnalyze,
              style: OutlinedButton.styleFrom(
                foregroundColor: theme.primary,
                side: BorderSide(color: theme.primary),
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              child: const Text(
                'Analyze Manually',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Helper Widgets ──

class _GradientButton extends StatelessWidget {
  final VoidCallback onTap;
  final IconData icon;
  final String label;

  const _GradientButton({
    required this.onTap,
    required this.icon,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Ink(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [theme.primary, theme.secondary],
            ),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 18, color: theme.onPrimary),
                const SizedBox(width: 8),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: theme.onPrimary,
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

class _OutlinedButton extends StatelessWidget {
  final VoidCallback onTap;
  final IconData icon;
  final String label;

  const _OutlinedButton({
    required this.onTap,
    required this.icon,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, size: 18),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: theme.inversePrimary,
        side: BorderSide(color: theme.outline.withOpacity(0.5)),
        padding: const EdgeInsets.symmetric(vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
      ),
    );
  }
}

class _InputField extends StatelessWidget {
  final String label;
  final String hint;
  final TextEditingController controller;
  final TextInputType keyboardType;

  const _InputField({
    required this.label,
    required this.hint,
    required this.controller,
    this.keyboardType = TextInputType.text,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: theme.inversePrimary.withOpacity(0.8),
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          style: TextStyle(
            color: theme.inversePrimary,
            fontSize: 14,
          ),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(
              color: theme.onSurface.withOpacity(0.4),
              fontSize: 14,
            ),
            filled: true,
            fillColor: theme.surface,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: theme.outline),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: theme.outline.withOpacity(0.3)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: theme.primary, width: 2),
            ),
          ),
        ),
      ],
    );
  }
}

class _ToggleRow extends StatelessWidget {
  final String label;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _ToggleRow({
    required this.label,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    return GestureDetector(
      onTap: () => onChanged(!value),
      child: Container(
        color: Colors.transparent,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: theme.inversePrimary,
              ),
            ),
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 48,
              height: 26,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(13),
                gradient: value
                    ? LinearGradient(
                  colors: [theme.primary, theme.secondary],
                )
                    : null,
                color: value ? null : theme.outline,
              ),
              child: AnimatedAlign(
                duration: const Duration(milliseconds: 200),
                alignment: value ? Alignment.centerRight : Alignment.centerLeft,
                child: Container(
                  margin: const EdgeInsets.all(3),
                  width: 20,
                  height: 20,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 4,
                        offset: const Offset(0, 1),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}