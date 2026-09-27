import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;

class ImageStorageService {
  // Save image permanently to app directory
  static Future<String> saveImagePermanently(String tempImagePath) async {
    try {
      // Get app's documents directory (persists across app restarts)
      final appDir = await getApplicationDocumentsDirectory();
      final foodImagesDir = Directory('${appDir.path}/food_images');

      // Create directory if it doesn't exist
      if (!await foodImagesDir.exists()) {
        await foodImagesDir.create(recursive: true);
      }

      // Generate unique filename with timestamp
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final extension = path.extension(tempImagePath);
      final newFileName = 'food_$timestamp$extension';
      final newPath = '${foodImagesDir.path}/$newFileName';

      // Copy image to permanent location
      final tempFile = File(tempImagePath);
      await tempFile.copy(newPath);

      print('✅ Image saved permanently: $newPath');
      return newPath;
    } catch (e) {
      print('❌ Error saving image: $e');
      rethrow;
    }
  }

  // Delete image
  static Future<void> deleteImage(String imagePath) async {
    try {
      final file = File(imagePath);
      if (await file.exists()) {
        await file.delete();
        print('🗑️ Image deleted: $imagePath');
      }
    } catch (e) {
      print('❌ Error deleting image: $e');
    }
  }

  // Check if image exists
  static Future<bool> imageExists(String imagePath) async {
    try {
      return await File(imagePath).exists();
    } catch (e) {
      return false;
    }
  }

  // Clean up old images (optional maintenance)
  static Future<void> cleanupOldImages({int daysOld = 30}) async {
    try {
      final appDir = await getApplicationDocumentsDirectory();
      final foodImagesDir = Directory('${appDir.path}/food_images');

      if (!await foodImagesDir.exists()) return;

      final now = DateTime.now();
      final files = foodImagesDir.listSync();

      for (var file in files) {
        if (file is File) {
          final stat = await file.stat();
          final age = now.difference(stat.modified).inDays;

          if (age > daysOld) {
            await file.delete();
            print('🗑️ Cleaned up old image: ${file.path}');
          }
        }
      }
    } catch (e) {
      print('❌ Error cleaning up images: $e');
    }
  }
}