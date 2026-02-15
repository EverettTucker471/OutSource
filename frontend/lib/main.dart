import 'package:flutter/material.dart';
import 'splash.dart'; // Imports the login page we created

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aura',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          toolbarHeight: 80,
          titleTextStyle: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: Colors.black54,
          ),
          centerTitle: true,
        ),
      ),
      // We start at the LoginSplashPage. 
      // It will handle navigation to MainNavigationScreen upon success.
      home: const LoginSplashPage(),
    );
  }
}