import 'dart:convert';
import 'package:flutter/foundation.dart'; // Changed from dart:io
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

// 1. Data Model based on your Pydantic schema
class UserBasicDTO {
  final int id;
  final String username;
  final String name;

  UserBasicDTO({
    required this.id,
    required this.username,
    required this.name,
  });

  factory UserBasicDTO.fromJson(Map<String, dynamic> json) {
    return UserBasicDTO(
      id: json['id'],
      username: json['username'],
      name: json['name'],
    );
  }
}

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  // State variables
  List<UserBasicDTO> _fetchedUsers = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchUsers();
  }

  // 2. Async method to fetch data
  Future<void> _fetchUsers() async {
    // Determine the base URL based on the platform
    String baseUrl;
    // We must check kIsWeb FIRST because checking TargetPlatform.android on web throws an error
    if (kIsWeb) {
      baseUrl = 'http://127.0.0.1:8000';
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      baseUrl = 'http://10.0.2.2:8000';
    } else {
      baseUrl = 'http://127.0.0.1:8000';
    }

    final url = Uri.parse('$baseUrl/users/');

    try {
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          _fetchedUsers = data.map((json) => UserBasicDTO.fromJson(json)).toList();
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
        print('API Error: $e'); 
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 40),
            const Center(
              child: CircleAvatar(
                radius: 50,
                backgroundColor: Colors.deepPurple,
                child: Icon(Icons.person, size: 50, color: Colors.white),
              ),
            ),
            const SizedBox(height: 16),
            const Text('Wendy Wizard', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            
            // --- Dynamic API Content Section ---
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16.0),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Fetched Users (API Test)', 
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.grey),
                ),
              ),
            ),
            const SizedBox(height: 8),
            
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: _buildContent(),
            ),
            
            const SizedBox(height: 24),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.settings),
              title: const Text('Settings'),
              onTap: () {},
            ),
            ListTile(
              leading: const Icon(Icons.logout, color: Colors.red),
              title: const Text('Logout', style: TextStyle(color: Colors.red)),
              onTap: () {},
            ),
          ],
        ),
      ),
    );
  }

  // 3. Helper widget to handle Loading/Error/Success states
  Widget _buildContent() {
    if (_isLoading) {
      return const Padding(
        padding: EdgeInsets.all(8.0),
        child: CircularProgressIndicator(),
      );
    }

    if (_errorMessage != null) {
      return Text(
        _errorMessage!,
        style: const TextStyle(color: Colors.red),
      );
    }

    if (_fetchedUsers.isEmpty) {
      return const Text("No users found.");
    }

    return SizedBox(
      width: double.infinity,
      child: Wrap(
        spacing: 8.0,
        runSpacing: 8.0,
        children: _fetchedUsers.map((user) => Chip(
          avatar: CircleAvatar(
            backgroundColor: Colors.deepPurple.shade100,
            child: Text(
              user.username.isNotEmpty ? user.username[0].toUpperCase() : '?',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.deepPurple),
            ),
          ),
          label: Text(user.name),
          backgroundColor: Colors.white,
          side: const BorderSide(color: Colors.deepPurple, width: 0.5),
        )).toList(),
      ),
    );
  }
}