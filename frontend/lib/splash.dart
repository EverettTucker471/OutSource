import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'main.dart'; // Import to access MainNavigationScreen

class LoginSplashPage extends StatefulWidget {
  const LoginSplashPage({super.key});

  @override
  State<LoginSplashPage> createState() => _LoginSplashPageState();
}

class _LoginSplashPageState extends State<LoginSplashPage> {
  // CONFIGURATION: Ensure this matches your backend IP/Domain
  final String _baseUrl = "http://localhost:8000"; 

  final Dio _dio = Dio();
  final _formKey = GlobalKey<FormState>();
  
  // State variables
  bool _isLogin = true; 
  bool _isLoading = false;
  bool _obscurePassword = true;

  // Controllers
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  /// Navigates to the main app dashboard upon successful auth
  void _navigateToHome() {
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const MainNavigationScreen()),
    );
  }

  /// Handles JWT Login/Signup via Backend
  Future<void> _handleAuth() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    // Endpoints as requested: /auth/login and /auth/signup
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
          validateStatus: (status) => status! < 500, // Handle 4xx manually
        ),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        if (!_isLogin) {
            // If we just signed up, we don't have a token yet. 
            // We must call the login logic now.
            _isLogin = true; 
            await _handleAuth(); 
            return;
        }
        final token = response.data['access_token'] ?? response.data['token'];
        debugPrint("JWT: $token");
        _navigateToHome();
      }
    } on DioException catch (e) {
      debugPrint("Auth Error: ${e.message}");
      _showErrorSnackBar("Could not connect to server. Ensure backend is running.");
    } catch (e) {
      _showErrorSnackBar("An unexpected error occurred.");
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
    ));
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