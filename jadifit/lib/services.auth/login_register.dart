import 'package:flutter/material.dart';
import 'package:jadi_fit_app/pages/register_page.dart';  // LoginScreen
import 'package:jadi_fit_app/pages/sign_up.dart';        // SignUpScreen

class LoginOrRegister extends StatefulWidget {
  const LoginOrRegister({super.key});

  @override
  State<LoginOrRegister> createState() => _LoginOrRegister();
}

class _LoginOrRegister extends State<LoginOrRegister> {
  // initially, show sign in page (LoginScreen)
  bool showLoginPage = true;

  //toggle between login and sign up page
  void togglePages() {
    setState(() {
      showLoginPage = !showLoginPage;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (showLoginPage) {
      return LoginScreen(onTap: togglePages);  // This is your main login
    } else {
      return SignUpScreen(onTap: togglePages);  // This is your sign-up
    }
  }
}