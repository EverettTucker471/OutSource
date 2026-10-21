import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

// 1. Updated Data Model matching UserResponseDTO
class UserResponseDTO {
  final int id;
  final String username;
  final String name;
  final List<String> preferences;

  UserResponseDTO({
    required this.id,
    required this.username,
    required this.name,
    required this.preferences,
  });

  factory UserResponseDTO.fromJson(Map<String, dynamic> json) {
    return UserResponseDTO(
      id: json['id'],
      username: json['username'],
      name: json['name'],
      // Handle the list of strings safely
      preferences: List<String>.from(json['preferences'] ?? []),
    );
  }
}

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  // State variables
  UserResponseDTO? _currentUser;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchMyProfile();
  }

  // 2. Async method to fetch authenticated user data
  Future<void> _fetchMyProfile() async {
    String baseUrl;
    if (kIsWeb) {
      baseUrl = 'app7-lb-123017161.us-east-1.elb.amazonaws.com:8000';
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      baseUrl = 'http://10.0.2.2:8000';
    } else {
      baseUrl = 'app7-lb-123017161.us-east-1.elb.amazonaws.com:8000';
    }

    final url = Uri.parse('$baseUrl/me');

    try {
      // Retrieve the saved JWT token
      final String? token = await _storage.read(key: 'jwt_token');

      if (token == null) {
        setState(() {
          _errorMessage = 'No session found. Please login again.';
          _isLoading = false;
        });
        return;
      }

      final response = await http.get(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token', // Essential for /me endpoint
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        setState(() {
          _currentUser = UserResponseDTO.fromJson(data);
          _isLoading = false;
        });
      } else if (response.statusCode == 401) {
        setState(() {
          _errorMessage = 'Session expired. Please log in.';
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = 'Error: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Connection Failed';
        debugPrint('API Error: $e'); 
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        elevation: 0,
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(child: Text(_errorMessage!, style: const TextStyle(color: Colors.red)))
              : _buildProfileContent(),
    );
  }

  Widget _buildProfileContent() {
    if (_currentUser == null) return const SizedBox.shrink();

    return SingleChildScrollView(
      child: Column(
        children: [
          const SizedBox(height: 30),
          // Profile Picture / Avatar
          Center(
            child: Stack(
              children: [
                CircleAvatar(
                  radius: 60,
                  backgroundColor: Colors.deepPurple.shade100,
                  child: Text(
                    _currentUser!.name[0].toUpperCase(),
                    style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Colors.deepPurple),
                  ),
                ),
                Positioned(
                  bottom: 0,
                  right: 0,
                  child: CircleAvatar(
                    radius: 18,
                    backgroundColor: Theme.of(context).primaryColor,
                    child: const Icon(Icons.edit, size: 18, color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          
          // Name and Username
          Text(
            _currentUser!.name,
            style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
          ),
          Text(
            '@${_currentUser!.username}',
            style: const TextStyle(fontSize: 16, color: Colors.grey, fontWeight: FontWeight.w500),
          ),
          
          const SizedBox(height: 32),
          
          // Interests / Preferences Section
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.auto_awesome, size: 20, color: Colors.amber),
                    SizedBox(width: 8),
                    Text(
                      'Interests & Preferences', 
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                
                _currentUser!.preferences.isEmpty
                  ? const Text("No interests added yet.", style: TextStyle(color: Colors.grey))
                  : Wrap(
                      spacing: 10.0,
                      runSpacing: 10.0,
                      children: _currentUser!.preferences.map((interest) => Chip(
                        label: Text(interest),
                        backgroundColor: Colors.deepPurple.withOpacity(0.05),
                        side: BorderSide(color: Colors.deepPurple.withOpacity(0.2)),
                        padding: const EdgeInsets.symmetric(horizontal: 4),
                        labelStyle: const TextStyle(color: Colors.deepPurple, fontWeight: FontWeight.w600),
                      )).toList(),
                    ),
              ],
            ),
          ),
          
          const SizedBox(height: 40),
          const Divider(),
          
          // Settings and Actions
          ListTile(
            leading: const Icon(Icons.settings_outlined),
            title: const Text('Account Settings'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.notifications_none_rounded),
            title: const Text('Notifications'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.redAccent),
            title: const Text('Logout', style: TextStyle(color: Colors.redAccent)),
            onTap: () async {
              // Clear token and go back to login
              await _storage.delete(key: 'jwt_token');
              if (mounted) Navigator.of(context).pushReplacementNamed('/');
            },
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}