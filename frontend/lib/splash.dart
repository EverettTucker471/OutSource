import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:dio/dio.dart';

// Main Entry Point for the Splash Page
class LoginSplashPage extends StatefulWidget {
  const LoginSplashPage({super.key});

  @override
  State<LoginSplashPage> createState() => _LoginSplashPageState();
}

class _LoginSplashPageState extends State<LoginSplashPage> {
  // CONFIGURATION: Ensure this matches your Web Client ID from the Google Cloud Console.
  // Using a Web Client ID is mandatory for the 'serverAuthCode' exchange pattern.
  static const String _serverClientId = "YOUR_WEB_CLIENT_ID.apps.googleusercontent.com";
  
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    serverClientId: _serverClientId,
    scopes: [
      'email',
      'https://www.googleapis.com/auth/calendar.readonly',
    ],
  );

  bool _isLoading = false;

  /// Initiates the Google Sign-In flow and retrieves a one-time server auth code.
  Future<void> _handleSignIn() async {
    setState(() => _isLoading = true);
    try {
      // 1. Trigger the native/web Google Sign-In overlay
      final GoogleSignInAccount? user = await _googleSignIn.signIn();
      
      if (user != null) {
        // 2. Retrieve the Server Auth Code (not the Access Token)
        final String? serverAuthCode = user.serverAuthCode;

        if (serverAuthCode != null) {
          // 3. Forward the code to your FastAPI backend on AWS ECS
          await _sendCodeToBackend(serverAuthCode);
          
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text("Account linked! Fetching calendar data..."),
                backgroundColor: Colors.green,
              ),
            );
            // Logic to navigate to your main app screen would go here
          }
        } else {
          throw Exception("Failed to retrieve Server Auth Code from Google.");
        }
      }
    } catch (error) {
      debugPrint("Sign-in error: $error");
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Sign-in failed: $error")),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  /// POSTs the auth code to the backend for exchange and persistence.
  Future<void> _sendCodeToBackend(String code) async {
    final dio = Dio();
    
    // Replace this with your actual ECS Load Balancer URL or local IP for testing
    const String backendUrl = "http://localhost:8000/auth/google"; 
    
    try {
      final response = await dio.post(
        backendUrl, 
        data: {"code": code},
        options: Options(headers: {"Content-Type": "application/json"}),
      );
      
      if (response.statusCode != 200) {
        throw Exception("Backend rejected the auth code.");
      }
    } catch (e) {
      debugPrint("Backend communication error: $e");
      rethrow;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0F2027), Color(0xFF203A43), Color(0xFF2C5364)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Hero Icon / Logo
              const CircleAvatar(
                radius: 60,
                backgroundColor: Colors.white10,
                child: Icon(Icons.auto_awesome, size: 60, color: Colors.cyanAccent),
              ),
              const SizedBox(height: 32),
              
              // App Title
              const Text(
                "Aura Weather",
                style: TextStyle(
                  fontSize: 40,
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                "Intelligent Schedule & Weather Sync",
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 16,
                  fontWeight: FontWeight.w300,
                ),
              ),
              const SizedBox(height: 80),

              // Sign In Button or Loading State
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 300),
                child: _isLoading
                    ? const Column(
                        children: [
                          CircularProgressIndicator(color: Colors.cyanAccent),
                          SizedBox(height: 16),
                          Text("Securing tokens...", style: TextStyle(color: Colors.white54)),
                        ],
                      )
                    : ElevatedButton.icon(
                        onPressed: _handleSignIn,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: Colors.black87,
                          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(50),
                          ),
                          elevation: 10,
                        ),
                        icon: Image.network(
                          'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_Color_Icon.svg/1200px-Google_Color_Icon.svg.png',
                          height: 24,
                        ),
                        label: const Text(
                          "Continue with Google",
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                      ),
              ),
              
              const SizedBox(height: 40),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 40),
                child: Text(
                  "By signing in, you agree to allow Aura to read your calendar events to provide weather-optimized scheduling.",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white38, fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}