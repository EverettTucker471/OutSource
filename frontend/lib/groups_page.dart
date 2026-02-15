import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

// Data model for Circles/Groups
class CircleDTO {
  final int id;
  final String name;
  final String? description;
  final String type; // e.g., "Public" or "Private"

  CircleDTO({
    required this.id,
    required this.name,
    this.description,
    this.type = 'Public Group',
  });

  factory CircleDTO.fromJson(Map<String, dynamic> json) {
    return CircleDTO(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      type: json['type'] ?? 'Public Group',
    );
  }
}

// Data model for Circle Members
class MemberDTO {
  final int id;
  final String username;
  final String name;

  MemberDTO({
    required this.id,
    required this.username,
    required this.name,
  });

  factory MemberDTO.fromJson(Map<String, dynamic> json) {
    return MemberDTO(
      id: json['id'],
      username: json['username'],
      name: json['name'],
    );
  }
}

class GroupsPage extends StatefulWidget {
  const GroupsPage({super.key});

  @override
  State<GroupsPage> createState() => _GroupsPageState();
}

class _GroupsPageState extends State<GroupsPage> {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  // State variables
  List<CircleDTO> _circles = [];
  CircleDTO? _selectedCircle;
  List<MemberDTO> _currentMembers = [];
  
  bool _isLoading = true;
  bool _isLoadingMembers = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchCircles();
  }

  String _getBaseUrl() {
    if (kIsWeb) return 'app7-lb-123017161.us-east-1.elb.amazonaws.com:8000';
    if (defaultTargetPlatform == TargetPlatform.android) return 'http://10.0.2.2:8000';
    return 'app7-lb-123017161.us-east-1.elb.amazonaws.com:8000';
  }

  /// Fetches the circles a user belongs to via GET /me/circles
  Future<void> _fetchCircles() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final baseUrl = _getBaseUrl();
    final token = await _storage.read(key: 'jwt_token');

    if (token == null) {
      setState(() {
        _errorMessage = 'Auth session not found.';
        _isLoading = false;
      });
      return;
    }

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/me/circles'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          _circles = data.map((j) => CircleDTO.fromJson(j)).toList();
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = 'Failed to load circles (${response.statusCode})';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Connection Failed';
        _isLoading = false;
      });
    }
  }

  /// Fetches members for a specific circle
  Future<void> _fetchMembers(int circleId) async {
    setState(() => _isLoadingMembers = true);
    
    final baseUrl = _getBaseUrl();
    final token = await _storage.read(key: 'jwt_token');

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/circles/$circleId/members'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          _currentMembers = data.map((j) => MemberDTO.fromJson(j)).toList();
          _isLoadingMembers = false;
        });
      } else {
        setState(() => _isLoadingMembers = false);
      }
    } catch (e) {
      setState(() => _isLoadingMembers = false);
    }
  }

  void _onCircleSelected(CircleDTO circle) {
    setState(() {
      _selectedCircle = circle;
      _currentMembers = []; // Reset members list
    });
    _fetchMembers(circle.id);
  }

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
      child: _selectedCircle == null 
        ? _buildGroupsGrid() 
        : _buildGroupProfile(_selectedCircle!),
    );
  }

  Widget _buildGroupsGrid() {
    return Scaffold(
      key: const ValueKey('groups_list'),
      appBar: AppBar(
        title: const Text('Groups'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchCircles,
          ),
        ],
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.all(16.0),
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
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator())
              : _errorMessage != null
                ? _buildErrorView()
                : _circles.isEmpty
                  ? _buildEmptyView()
                  : RefreshIndicator(
                      onRefresh: _fetchCircles,
                      child: GridView.builder(
                        padding: const EdgeInsets.all(16.0),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2,
                          crossAxisSpacing: 16,
                          mainAxisSpacing: 16,
                        ),
                        itemCount: _circles.length,
                        itemBuilder: (context, index) {
                          final circle = _circles[index];
                          return _buildGroupCard(circle);
                        },
                      ),
                    ),
          ),
        ],
      ),
    );
  }

  Widget _buildGroupCard(CircleDTO circle) {
    return InkWell(
      onTap: () => _onCircleSelected(circle),
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
                circle.name, 
                textAlign: TextAlign.center,
                style: const TextStyle(fontWeight: FontWeight.bold),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, color: Colors.red, size: 40),
          const SizedBox(height: 12),
          Text(_errorMessage!, style: const TextStyle(color: Colors.red)),
          TextButton(onPressed: _fetchCircles, child: const Text("Retry")),
        ],
      ),
    );
  }

  Widget _buildEmptyView() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.group_off_outlined, color: Colors.grey, size: 40),
          SizedBox(height: 12),
          Text("You aren't in any groups yet.", style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildGroupProfile(CircleDTO circle) {
    return Scaffold(
      key: const ValueKey('group_profile'),
      appBar: AppBar(
        title: const Text('Group Profile'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => setState(() => _selectedCircle = null),
        ),
      ),
      body: ListView(
        children: [
          const SizedBox(height: 40),
          Center(
            child: Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: Colors.deepPurple.shade50,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.groups_rounded, size: 80, color: Colors.deepPurple),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            circle.name,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            circle.type,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 16, color: Colors.grey),
          ),
          if (circle.description != null && circle.description!.isNotEmpty) ...[
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Text(
                circle.description!,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 15, color: Colors.black87),
              ),
            ),
          ],
          const SizedBox(height: 20),
          
          // Members Section
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'MEMBERS',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey, letterSpacing: 1.2),
                ),
                if (_isLoadingMembers)
                  const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
              ],
            ),
          ),
          const SizedBox(height: 12),
          
          if (_currentMembers.isEmpty && !_isLoadingMembers)
            const Center(child: Text("No members found.", style: TextStyle(color: Colors.grey)))
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _currentMembers.length,
              separatorBuilder: (context, index) => const Divider(indent: 72, height: 1),
              itemBuilder: (context, index) {
                final member = _currentMembers[index];
                return ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Colors.deepPurple.shade50,
                    child: Text(
                      member.name[0].toUpperCase(),
                      style: const TextStyle(color: Colors.deepPurple, fontWeight: FontWeight.bold),
                    ),
                  ),
                  title: Text(member.name, style: const TextStyle(fontWeight: FontWeight.w500)),
                  subtitle: Text("@${member.username}"),
                );
              },
            ),
            
          const SizedBox(height: 40),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40),
            child: ElevatedButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.chat_bubble_outline),
              label: const Text("Open Group Chat"),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepPurple,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }
}