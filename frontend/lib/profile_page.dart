import 'package:flutter/material.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: Column(
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
          
          // --- Interests Section ---
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16.0),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Interests', 
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.grey),
              ),
            ),
          ),
          const SizedBox(height: 8),
          const Wrap(
            spacing: 8.0,
            children: [
              Chip(label: Text('Soccer')),
              Chip(label: Text('Water Polo')),
              Chip(label: Text('Yoga')),
            ],
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
    );
  }
}