import 'package:flutter/material.dart';

class FriendsPage extends StatefulWidget {
  const FriendsPage({super.key});

  @override
  State<FriendsPage> createState() => _FriendsPageState();
}

class _FriendsPageState extends State<FriendsPage> {
  // Store the currently selected friend
  Map<String, String>? _selectedFriend;

  final List<Map<String, String>> friends = [
    {'name': 'Alex Johnson', 'status': 'Active 5m ago'},
    {'name': 'Jordan Smith', 'status': 'Online'},
    {'name': 'Taylor Reed', 'status': 'Busy'},
    {'name': 'Sam Wilson', 'status': 'Online'},
    {'name': 'Casey Brown', 'status': 'Offline'},
    {'name': 'Riley Davis', 'status': 'Active now'},
  ];

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      // Use a transition builder for a "slide-in" effect from the right
      transitionBuilder: (Widget child, Animation<double> animation) {
        final offsetAnimation = Tween<Offset>(
          begin: const Offset(1.0, 0.0),
          end: Offset.zero,
        ).animate(animation);
        return SlideTransition(position: offsetAnimation, child: child);
      },
      child: _selectedFriend == null 
        ? _buildFriendsList() 
        : _buildFriendProfile(_selectedFriend!),
    );
  }

  // --- View 1: Friends List ---
  Widget _buildFriendsList() {
    return Scaffold(
      key: const ValueKey('list'),
      appBar: AppBar(title: const Text('Friends')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 16, right: 16, top: 16, bottom: 16),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Search friends...',
                prefixIcon: const Icon(Icons.search, size: 20),
                filled: true,
                fillColor: Colors.deepPurple.withOpacity(0.05),
                contentPadding: const EdgeInsets.symmetric(vertical: 0),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(30),
                  borderSide: BorderSide.none,
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(30),
                  borderSide: BorderSide(color: Colors.deepPurple.withOpacity(0.1)),
                ),
              ),
              onSubmitted: (value) {
                print('Searching for: $value');
              },
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView.separated(
              itemCount: friends.length,
              separatorBuilder: (context, index) => const Divider(height: 1, indent: 70),
              itemBuilder: (context, index) {
                final friend = friends[index];
                return ListTile(
                  onTap: () {
                    setState(() {
                      _selectedFriend = friend;
                    });
                  },
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  leading: CircleAvatar(
                    radius: 24,
                    backgroundColor: Colors.deepPurple.shade100,
                    child: Text(
                      friend['name']![0],
                      style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.deepPurple),
                    ),
                  ),
                  title: Text(
                    friend['name']!,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    friend['status']!,
                    style: TextStyle(
                      color: friend['status'] == 'Online' || friend['status'] == 'Active now' 
                        ? Colors.green 
                        : Colors.grey,
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  // --- View 2: Friend Profile ---
  Widget _buildFriendProfile(Map<String, String> friend) {
    return Scaffold(
      key: const ValueKey('profile'),
      appBar: AppBar(
        title: const Text('Profile'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            setState(() {
              _selectedFriend = null;
            });
          },
        ),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircleAvatar(
              radius: 60,
              backgroundColor: Colors.deepPurple.shade50,
              child: Text(
                friend['name']![0],
                style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Colors.deepPurple),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              friend['name']!,
              style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              friend['status']!,
              style: const TextStyle(fontSize: 18, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}