import 'package:flutter/foundation.dart'; // For kIsWeb check
import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart'; // Import storage
import 'main_navigation_screen.dart';

class LoginSplashPage extends StatefulWidget {
  const LoginSplashPage({super.key});

  @override
  State<LoginSplashPage> createState() => _LoginSplashPageState();
}

class _LoginSplashPageState extends State<LoginSplashPage> {
  final Dio _dio = Dio();
  // Create the storage instance
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  final _formKey = GlobalKey<FormState>();
  
  // State variables
  bool _isLogin = true; 
  bool _isLoading = false;
  bool _obscurePassword = true;

  // Controllers
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  /// Helper to get the correct URL for Android, iOS, and Web
  String get _baseUrl {
    if (kIsWeb) {
      return "app7-lb-123017161.us-east-1.elb.amazonaws.com:8000"; // Localhost for Web
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      return "http://10.0.2.2:8000"; // Android Emulator
    }
    return "app7-lb-123017161.us-east-1.elb.amazonaws.com:8000"; // iOS Simulator or Desktop
  }

  /// Navigates to the main app dashboard upon successful auth
  void _navigateToHome() {
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      // Removed 'const' to prevent potential constructor issues
      MaterialPageRoute(builder: (_) => MainNavigationScreen()),
    );
  }

  /// Handles JWT Login/Signup via Backend
  Future<void> _handleAuth() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    // Endpoints: /auth/login and /auth/signup
    final String endpoint = _isLogin ? "/auth/login" : "/auth/signup";
    
    final Map<String, dynamic> data = {
      "username": _usernameController.text.trim(),
      "password": _passwordController.text.trim(),
      "name": "New User"
    };

    try {
      final response = await _dio.post(
        "$_baseUrl$endpoint",
        data: data,
        options: Options(
          headers: {"Content-Type": "application/json"},
          // We allow 4xx so we can handle the error message manually below
          validateStatus: (status) => status! < 500, 
        ),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        if (!_isLogin) {
            // If we just signed up successfully, immediately log in
            _isLogin = true; 
            await _handleAuth(); // Recursive call to login
            return;
        }
        
        // Login Success
        final token = response.data['access_token'] ?? response.data['token'];
        debugPrint("JWT: $token");
        
        // Save token to SecureStorage
        await _storage.write(key: 'jwt_token', value: token);
        
        _navigateToHome();
      } else {
        // Handle 400/401 errors specifically
        final msg = response.data['detail'] ?? "Authentication failed";
        _showErrorSnackBar(msg.toString());
      }
    } on DioException catch (e) {
      debugPrint("Auth Error: ${e.message}");
      _showErrorSnackBar("Could not connect to server. Ensure backend is running.");
    } catch (e) {
      _showErrorSnackBar("An unexpected error occurred: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message), 
        backgroundColor: Colors.redAccent,
        behavior: SnackBarBehavior.floating,
      ),
    );
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
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 30),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 400),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Branding
                    const CircleAvatar(
                      radius: 45,
                      backgroundColor: Colors.white10,
                      child: Icon(Icons.auto_awesome, size: 45, color: Colors.cyanAccent),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      "Aura",
                      style: TextStyle(
                        fontSize: 40,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                        letterSpacing: 2.0,
                      ),
                    ),
                    const Text(
                      "Smart Weather & Scheduling",
                      style: TextStyle(color: Colors.white54, fontSize: 14),
                    ),
                    const SizedBox(height: 40),

                    // Auth Card
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.08),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: Colors.white10),
                      ),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          children: [
                            Text(
                              _isLogin ? "Welcome Back" : "Create Account",
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 24),
                            
                            _buildTextField(
                              controller: _usernameController,
                              label: "Username",
                              icon: Icons.person_outline,
                              validator: (v) => v!.isEmpty ? "Enter username" : null,
                            ),
                            const SizedBox(height: 16),
                            
                            _buildTextField(
                              controller: _passwordController,
                              label: "Password",
                              icon: Icons.lock_outline,
                              isPassword: true,
                              validator: (v) => v!.length < 6 ? "Minimum 6 characters" : null,
                            ),
                            const SizedBox(height: 24),

                            SizedBox(
                              width: double.infinity,
                              height: 55,
                              child: ElevatedButton(
                                onPressed: _isLoading ? null : _handleAuth,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.cyanAccent,
                                  foregroundColor: Colors.black,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                                  elevation: 0,
                                ),
                                child: _isLoading 
                                  ? const SizedBox(
                                      height: 24, 
                                      width: 24, 
                                      child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2)
                                    )
                                  : Text(
                                      _isLogin ? "Login" : "Sign Up", 
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)
                                    ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 32),

                    // Toggle Login/Signup
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _isLogin = !_isLogin;
                          // Optional: Clear fields when switching
                          _usernameController.clear();
                          _passwordController.clear();
                        });
                      },
                      child: RichText(
                        text: TextSpan(
                          style: const TextStyle(color: Colors.white70, fontSize: 14),
                          children: [
                            TextSpan(text: _isLogin ? "Don't have an account? " : "Already have an account? "),
                            TextSpan(
                              text: _isLogin ? "Sign Up" : "Login",
                              style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    bool isPassword = false,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      obscureText: isPassword && _obscurePassword,
      style: const TextStyle(color: Colors.white),
      validator: validator,
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: Colors.white60, fontSize: 14),
        prefixIcon: Icon(icon, color: Colors.white60, size: 22),
        suffixIcon: isPassword 
          ? IconButton(
              icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility, color: Colors.white60, size: 20),
              onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
            )
          : null,
        filled: true,
        fillColor: Colors.white.withOpacity(0.05),
        contentPadding: const EdgeInsets.symmetric(vertical: 18),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: Colors.white10)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: Colors.cyanAccent, width: 1)),
        errorStyle: const TextStyle(color: Colors.redAccent),
      ),
    );
  }
}