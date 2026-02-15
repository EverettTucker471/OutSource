import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
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
  // static const String _serverClientId = "320153364438-lo4msgmc9besqd636rpleqdcaqemcfcb.apps.googleusercontent.com";
  static const String _serverClientId = "320153364438-ebv8qiupap6pjkd4a76c4vibmrt1f47a.apps.googleusercontent.com";
  final FirebaseAuth _firebaseAuth = FirebaseAuth.instance;

  Future<void> signOut() async {
    return await _firebaseAuth.signOut();
  }

  Future<void> initGoogleSignIn() async {
    print("Initializing Sign-in");
    await GoogleSignIn.instance.initialize(
      serverClientId: _serverClientId,
    );
  }

  bool _isLoading = false;

  /// Initiates the Google Sign-In flow and retrieves a one-time server auth code.
  Future<void> _handleSignIn() async {
  try {
    initGoogleSignIn();
    
    setState(() => _isLoading = true);

    // 1. SIGN IN (Authentication)
    // In v7, this is the part that triggers the native account picker.
    final GoogleSignInAccount? gUser = await GoogleSignIn.instance.authenticate();

    if (gUser == null) {
      setState(() => _isLoading = false);
      return; // User canceled
    }

    // 2. GET AUTHENTICATION (ID Token)
    // Note: In v7, this is a synchronous getter.
    final String? idToken = gUser.authentication.idToken;

    // 3. AUTHORIZE SCOPES (Access Token)
    // This is the NEW step. You MUST explicitly authorize scopes to get an accessToken.
    final List<String> scopes = ['email', 'profile'];
    final authorization = await gUser.authorizationClient.authorizeScopes(scopes);
    final String? accessToken = authorization.accessToken;

    // 4. FIREBASE SIGN IN
    if (idToken != null && accessToken != null) {
      final credential = GoogleAuthProvider.credential(
        accessToken: accessToken,
        idToken: idToken,
      );
      await _firebaseAuth.signInWithCredential(credential);
    } else {
      throw "Missing tokens: ID($idToken) or Access($accessToken)";
    }

    } catch (e) {
      print("Google Sign-In Failure: $e");
      // If you see "No credential available" here, it's still likely the SHA-1 mismatch.
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
      // Use resizeToAvoidBottomInset to prevent the keyboard from causing overflows
      resizeToAvoidBottomInset: true, 
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
          // FIX 1: Wrap in SingleChildScrollView to allow vertical scrolling
          child: SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(height: 60), // Top spacing for scroll view
                  
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
                    textAlign: TextAlign.center,
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
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 16,
                      fontWeight: FontWeight.w300,
                    ),
                  ),
                  
                  // FIX 2: Reduce this massive spacer so it fits on small screens
                  const SizedBox(height: 60), 

                  // Sign In Button
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
                              // Error handling for network images
                              errorBuilder: (context, error, stackTrace) => const Icon(Icons.login),
                            ),
                            label: const Text(
                              "Continue with Google",
                              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                            ),
                          ),
                  ),
                  
                  const SizedBox(height: 40),
                  const Text(
                    "By signing in, you agree to allow Aura to read your calendar events to provide weather-optimized scheduling.",
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white38, fontSize: 12),
                  ),
                  const SizedBox(height: 20), // Bottom padding for scroll view
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}