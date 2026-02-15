import 'package:flutter/material.dart';

class GroupsPage extends StatefulWidget {
  const GroupsPage({super.key});

  @override
  State<GroupsPage> createState() => _GroupsPageState();
}

class _GroupsPageState extends State<GroupsPage> {
  String? _selectedGroup;

  final List<String> groups = [
    'Downtown Paddleboarders',
    'Weekend Basketball',
    'Morning Swimmers',
    'Water Polo League',
  ];

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      transitionBuilder: (Widget child, Animation<double> animation) {
        final offsetAnimation = Tween<Offset>(
          begin: const Offset(1.0, 0.0),
          end: Offset.zero,
        ).animate(animation);
        return SlideTransition(position: offsetAnimation, child: child);
      },
      child: _selectedGroup == null 
        ? _buildGroupsGrid() 
        : _buildGroupProfile(_selectedGroup!),
    );
  }

  Widget _buildGroupsGrid() {
    return Scaffold(
      key: const ValueKey('groups_list'),
      appBar: AppBar(title: const Text('Groups')),
      body: Column(
        children: [
          // Search Bar identical to Friends page
          Padding(
            padding: const EdgeInsets.only(left: 16, right: 16, top: 16, bottom: 16),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Search groups...',
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
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: GridView.builder(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                ),
                itemCount: groups.length,
                itemBuilder: (context, index) => InkWell(
                  onTap: () {
                    setState(() {
                      _selectedGroup = groups[index];
                    });
                  },
                  borderRadius: BorderRadius.circular(16),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.deepPurple.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.deepPurple.withOpacity(0.1)),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.groups_rounded, size: 40, color: Colors.deepPurple),
                        const SizedBox(height: 12),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 8.0),
                          child: Text(
                            groups[index], 
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGroupProfile(String groupName) {
    return Scaffold(
      key: const ValueKey('group_profile'),
      appBar: AppBar(
        title: const Text('Group Profile'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            setState(() {
              _selectedGroup = null;
            });
          },
        ),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: Colors.deepPurple.shade50,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.groups_rounded, size: 80, color: Colors.deepPurple),
            ),
            const SizedBox(height: 24),
            Text(
              groupName,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Public Group',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}