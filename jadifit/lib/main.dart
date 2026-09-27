import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:jadi_fit_app/pages/welcome_screen.dart';
import 'package:jadi_fit_app/pages/home_page.dart';
import 'package:jadi_fit_app/pages/edit_profile_page.dart';  // ✅ ADD THIS
import 'package:jadi_fit_app/firebase_options.dart';
import 'package:jadi_fit_app/services.auth/food_service.dart';
import 'package:jadi_fit_app/services.auth/user_provider.dart';
import 'package:provider/provider.dart';
import 'themes/theme_selector.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await dotenv.load(fileName: ".env");
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (context) => ThemeProvider()),
        ChangeNotifierProvider(create: (context) => FoodProvider()),
        ChangeNotifierProvider(create: (context) => UserProvider()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: const AuthGate(),
      theme: Provider.of<ThemeProvider>(context).themeData.copyWith(
        textTheme: GoogleFonts.plusJakartaSansTextTheme(
          Provider.of<ThemeProvider>(context).themeData.textTheme,
        ),
      ),
    );
  }
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snapshot) {
        // Show loading while checking auth state
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        // User is logged in
        if (snapshot.hasData) {
          // Load user data when logged in
          WidgetsBinding.instance.addPostFrameCallback((_) {
            context.read<UserProvider>().loadUserData();
          });

          // ✅ FIX: Check if profile is complete
          return Consumer<UserProvider>(
            builder: (context, userProvider, _) {
              // Show loading while fetching user data
              if (userProvider.isLoading) {
                return const Scaffold(
                  body: Center(child: CircularProgressIndicator()),
                );
              }

              // ✅ If profile incomplete, show EditProfilePage with isFirstTime: true
              if (!userProvider.isProfileComplete || userProvider.isNewUser) {
                return const EditProfilePage(isFirstTime: true);
              }


              // Profile complete - show home page
              return const HomePage();
            },
          );
        }

        // User not logged in
        return const WelcomeScreen();
      },
    );
  }
}