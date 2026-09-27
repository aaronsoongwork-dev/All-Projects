import 'package:flutter/material.dart';
import 'dart:math' as math;

class CircularProgressWidget extends StatelessWidget {
  final int currentCalories;
  final int targetCalories;

  const CircularProgressWidget({
    super.key,
    required this.currentCalories,
    required this.targetCalories,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).colorScheme;
    final progress = targetCalories > 0
        ? (currentCalories / targetCalories).clamp(0.0, 1.0)
        : 0.0;

    return Container(
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
          // Circular Progress Ring
          SizedBox(
            width: 180,
            height: 180,
            child: Stack(
              children: [
                // Background circle
                Center(
                  child: Container(
                    width: 180,
                    height: 180,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: theme.surface,
                    ),
                  ),
                ),

                // Progress ring
                Center(
                  child: SizedBox(
                    width: 180,
                    height: 180,
                    child: CustomPaint(
                      painter: _CircularProgressPainter(
                        progress: progress,
                        primaryColor: theme.primary,
                        secondaryColor: theme.secondary,
                        backgroundColor: theme.outline.withOpacity(0.2),
                      ),
                    ),
                  ),
                ),

                // Center content
                Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      ShaderMask(
                        shaderCallback: (bounds) => LinearGradient(
                          colors: [theme.primary, theme.secondary],
                        ).createShader(bounds),
                        child: Text(
                          currentCalories.toString(),
                          style: const TextStyle(
                            fontSize: 48,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                      Text(
                        'of $targetCalories kcal',
                        style: TextStyle(
                          fontSize: 14,
                          color: theme.onSurface,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              theme.primary.withOpacity(0.1),
                              theme.secondary.withOpacity(0.1),
                            ],
                          ),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '${(progress * 100).toInt()}%',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: theme.primary,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // Remaining calories
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                currentCalories >= targetCalories
                    ? Icons.check_circle
                    : Icons.trending_up,
                size: 18,
                color: currentCalories >= targetCalories
                    ? Colors.green
                    : theme.primary,
              ),
              const SizedBox(width: 8),
              Text(
                currentCalories >= targetCalories
                    ? 'Goal reached! 🎉'
                    : '${targetCalories - currentCalories} kcal remaining',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: theme.inversePrimary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _CircularProgressPainter extends CustomPainter {
  final double progress;
  final Color primaryColor;
  final Color secondaryColor;
  final Color backgroundColor;

  _CircularProgressPainter({
    required this.progress,
    required this.primaryColor,
    required this.secondaryColor,
    required this.backgroundColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    final strokeWidth = 16.0;

    // Draw background circle
    final backgroundPaint = Paint()
      ..color = backgroundColor
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius - strokeWidth / 2, backgroundPaint);

    // Draw progress arc with gradient
    if (progress > 0) {
      final rect = Rect.fromCircle(center: center, radius: radius - strokeWidth / 2);
      final gradient = SweepGradient(
        startAngle: -math.pi / 2,
        endAngle: -math.pi / 2 + (2 * math.pi * progress),
        colors: [primaryColor, secondaryColor],
      );

      final progressPaint = Paint()
        ..shader = gradient.createShader(rect)
        ..strokeWidth = strokeWidth
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      canvas.drawArc(
        rect,
        -math.pi / 2,
        2 * math.pi * progress,
        false,
        progressPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}