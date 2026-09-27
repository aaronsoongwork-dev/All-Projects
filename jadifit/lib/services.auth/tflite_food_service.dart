import 'dart:io';
import 'package:flutter/services.dart';
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:image/image.dart' as img;

class TFLiteFoodService {
  Interpreter? _interpreter;
  List<String>? _labels;
  bool _isInitialized = false;

  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      _interpreter = await Interpreter.fromAsset('assets/models/food101_model.tflite');

      final labelsData = await rootBundle.loadString('assets/models/labels.txt');
      _labels = labelsData.split('\n').where((label) => label.isNotEmpty).toList();

      _isInitialized = true;
      print('✅ TFLite model loaded');
    } catch (e) {
      print('❌ Error loading model: $e');
      rethrow;
    }
  }

  Future<Map<String, dynamic>?> detectFood(File imageFile) async {
    if (!_isInitialized) {
      throw Exception('Model not initialized');
    }

    try {
      final imageBytes = await imageFile.readAsBytes();
      img.Image? image = img.decodeImage(imageBytes);

      if (image == null) {
        throw Exception('Failed to decode image');
      }

      final input = _preprocessImage(image);
      final output = _runInference(input);
      return _getTopPrediction(output);
    } catch (e) {
      print('❌ Detection error: $e');
      return null;
    }
  }

  List<List<List<List<double>>>> _preprocessImage(img.Image image) {
    const inputSize = 224; // Standard size for most food models

    final resizedImage = img.copyResize(
      image,
      width: inputSize,
      height: inputSize,
    );

    // FIX: Use getPixelSafe() and extract RGB properly
    final input = List.generate(
      1,
          (i) => List.generate(
        inputSize,
            (y) => List.generate(
          inputSize,
              (x) {
            final pixel = resizedImage.getPixelSafe(x, y);
            // Extract RGB from the int color value
            final r = pixel.r / 255.0;
            final g = pixel.g / 255.0;
            final b = pixel.b / 255.0;
            return [r, g, b];
          },
        ),
      ),
    );

    return input;
  }

  List<double> _runInference(List<List<List<List<double>>>> input) {
    final outputShape = _interpreter!.getOutputTensor(0).shape;
    final output = List.filled(outputShape[1], 0.0).reshape([1, outputShape[1]]);
    _interpreter!.run(input, output);
    return output[0];
  }

  Map<String, dynamic> _getTopPrediction(List<double> output) {
    double maxScore = 0.0;
    int maxIndex = 0;

    for (int i = 0; i < output.length; i++) {
      if (output[i] > maxScore) {
        maxScore = output[i];
        maxIndex = i;
      }
    }

    return {
      'label': _labels![maxIndex],
      'confidence': maxScore,
      'index': maxIndex,
    };
  }

  void dispose() {
    _interpreter?.close();
  }
}