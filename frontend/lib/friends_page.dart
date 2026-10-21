import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

// Data model for friends (confirmed)
class FriendDTO {
  final int id;
  final String username;
  final String name;
  final String status;

  FriendDTO({
    required this.id,
    required this.username,
    required this.name,
    this.status = 'Online',
  });

  factory FriendDTO.fromJson(Map<String, dynamic> json) {
    return FriendDTO(
      id: json['id'],
      username: json['username'],
      name: json['name'],
      status: json['status'] ?? 'Active now',
    );
  }
}

// Data model for requests (matching FriendRequestWithUserDTO)
class FriendRequestDTO {
  final int id;
  final String username;
  final String name;
  final String status; // "pending" or "accepted"

  FriendRequestDTO({
    required this.id,
    required this.username,
    required this.name,
    required this.status,
  });

  factory FriendRequestDTO.fromJson(Map<String, dynamic> json) {
    final userData = json['user'];
    return FriendRequestDTO(
      id: json['id'],
      username: userData['username'],
      name: userData['name'],
      status: json['status'] ?? 'pending',
    );
  }
}

class FriendsPage extends StatefulWidget {
  const FriendsPage({super.key});

  @override
  State<FriendsPage> createState() => _FriendsPageState();
}

class _FriendsPageState extends State<FriendsPage> {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  List<FriendDTO> _friends = [];
  List<FriendRequestDTO> _incomingRequests = [];
  List<FriendRequestDTO> _outgoingRequests = [];
  
  FriendDTO? _selectedFriend;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchAllData();
  }

  String _getBaseUrl() {
    if (kIsWeb) return 'app7-lb-123017161.us-east-1.elb.amazonaws.com:8000';
    if (defaultTargetPlatform == TargetPlatform.android) return 'http://10.0.2.2:8000';
    return 'app7-lb-123017161.us-east-1.elb.amazonaws.com:8000';
  }

  Future<void> _fetchAllData() async {
    setState(() => _isLoading = true);
    final baseUrl = _getBaseUrl();
    final token = await _storage.read(key: 'jwt_token');

    if (token == null) {
      setState(() {
        _errorMessage = 'Auth session not found.';
        _isLoading = false;
      });
      return;
    }

    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };

    try {
      final results = await Future.wait([
        http.get(Uri.parse('$baseUrl/me/friends'), headers: headers),
        http.get(Uri.parse('$baseUrl/me/friend-requests/incoming'), headers: headers),
        http.get(Uri.parse('$baseUrl/me/friend-requests/outgoing'), headers: headers),
      ]);

      if (results.every((res) => res.statusCode == 200)) {
        setState(() {
          _friends = (json.decode(results[0].body) as List)
              .map((j) => FriendDTO.fromJson(j)).toList();
          
          _incomingRequests = (json.decode(results[1].body) as List)
              .map((j) => FriendRequestDTO.fromJson(j)).toList();
          
          _outgoingRequests = (json.decode(results[2].body) as List)
              .map((j) => FriendRequestDTO.fromJson(j)).toList();
          
          _isLoading = false;
          _errorMessage = null;
        });
      } else {
        setState(() {
          _errorMessage = 'Failed to fetch data';
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
      child: _selectedFriend == null 
        ? _buildFriendsListView() 
        : _buildFriendProfile(_selectedFriend!),
    );
  }

  Widget _buildFriendsListView() {
    // Filter pending vs accepted if necessary
    final pendingIncoming = _incomingRequests.where((r) => r.status == 'pending').toList();
    final acceptedIncoming = _incomingRequests.where((r) => r.status == 'accepted').toList();
    final pendingOutgoing = _outgoingRequests.where((r) => r.status == 'pending').toList();
    final acceptedOutgoing = _outgoingRequests.where((r) => r.status == 'accepted').toList();

    return Scaffold(
      key: const ValueKey('list'),
      appBar: AppBar(
        title: const Text('Friends'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _fetchAllData),
        ],
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? _buildErrorView()
              : RefreshIndicator(
                  onRefresh: _fetchAllData,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      _buildSearchBar(),

                      // 1. Incoming Pending
                      if (pendingIncoming.isNotEmpty) ...[
                        _buildSectionHeader("Incoming Requests (${pendingIncoming.length})", Colors.orange),
                        ...pendingIncoming.map((req) => _buildRequestTile(req, isIncoming: true)),
                        const Divider(),
                      ],

                      // 2. Friends List (Confirmed)
                      _buildSectionHeader("My Friends (${_friends.length})", Colors.deepPurple),
                      if (_friends.isEmpty && acceptedIncoming.isEmpty && acceptedOutgoing.isEmpty)
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 20),
                          child: Center(child: Text("No friends yet.", style: TextStyle(color: Colors.grey))),
                        )
                      else ...[
                        ..._friends.map((f) => _buildFriendTile(f)),
                        // Displaying accepted requests as friends if they aren't in the main friends list yet
                        ...acceptedIncoming.map((req) => _buildFriendTileFromRequest(req)),
                        ...acceptedOutgoing.map((req) => _buildFriendTileFromRequest(req)),
                      ],

                      // 3. Outgoing Pending
                      if (pendingOutgoing.isNotEmpty) ...[
                        const Divider(),
                        _buildSectionHeader("Sent Requests (${pendingOutgoing.length})", Colors.blueGrey),
                        ...pendingOutgoing.map((req) => _buildRequestTile(req, isIncoming: false)),
                      ],
                      
                      const SizedBox(height: 40),
                    ],
                  ),
                ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: TextField(
        decoration: InputDecoration(
          hintText: 'Search friends...',
          prefixIcon: const Icon(Icons.search, size: 20),
          filled: true,
          fillColor: Colors.deepPurple.withOpacity(0.05),
          contentPadding: EdgeInsets.zero,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(30), borderSide: BorderSide.none),
        ),
      ),
    );
  }

  Widget _buildErrorView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(_errorMessage!, style: const TextStyle(color: Colors.red)),
          const SizedBox(height: 10),
          ElevatedButton(onPressed: _fetchAllData, child: const Text("Retry")),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Text(title.toUpperCase(), style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color, letterSpacing: 1.1)),
    );
  }

  Widget _buildFriendTile(FriendDTO friend) {
    return ListTile(
      onTap: () => setState(() => _selectedFriend = friend),
      leading: CircleAvatar(
        backgroundColor: Colors.deepPurple.shade100,
        child: Text(friend.name[0].toUpperCase(), style: const TextStyle(color: Colors.deepPurple, fontWeight: FontWeight.bold)),
      ),
      title: Text(friend.name, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(friend.status, style: TextStyle(color: friend.status.contains('now') ? Colors.green : Colors.grey, fontSize: 13)),
      trailing: const Icon(Icons.chevron_right, size: 20),
    );
  }

  // Helper for requests that have been "accepted" but are being displayed in the list
  Widget _buildFriendTileFromRequest(FriendRequestDTO req) {
    return _buildFriendTile(FriendDTO(id: req.id, username: req.username, name: req.name, status: "Recently Added"));
  }

  Widget _buildRequestTile(FriendRequestDTO req, {required bool isIncoming}) {
    return ListTile(
      leading: CircleAvatar(
        backgroundColor: isIncoming ? Colors.orange.shade50 : Colors.blueGrey.shade50,
        child: Text(req.name[0].toUpperCase(), style: TextStyle(color: isIncoming ? Colors.orange : Colors.blueGrey, fontWeight: FontWeight.bold)),
      ),
      title: Text(req.name, style: const TextStyle(fontWeight: FontWeight.w500)),
      subtitle: Text("@${req.username}", style: const TextStyle(fontSize: 12)),
      trailing: isIncoming 
          ? Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(icon: const Icon(Icons.check_circle, color: Colors.green), onPressed: () {}),
                IconButton(icon: const Icon(Icons.cancel, color: Colors.redAccent), onPressed: () {}),
              ],
            )
          : Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(color: Colors.blueGrey.shade50, borderRadius: BorderRadius.circular(12)),
              child: const Text("Pending", style: TextStyle(fontSize: 11, color: Colors.blueGrey, fontWeight: FontWeight.bold)),
            ),
    );
  }

  Widget _buildFriendProfile(FriendDTO friend) {
    return Scaffold(
      key: const ValueKey('profile'),
      appBar: AppBar(
        title: const Text('Profile'),
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => setState(() => _selectedFriend = null)),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircleAvatar(
              radius: 60,
              backgroundColor: Colors.deepPurple.shade50,
              child: Text(friend.name[0].toUpperCase(), style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Colors.deepPurple)),
            ),
            const SizedBox(height: 24),
            Text(friend.name, style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
            Text("@${friend.username}", style: const TextStyle(fontSize: 18, color: Colors.deepPurple)),
            const SizedBox(height: 40),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildActionButton(Icons.message, "Message"),
                const SizedBox(width: 20),
                _buildActionButton(Icons.calendar_month, "Invite"),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton(IconData icon, String label) {
    return Column(
      children: [
        ElevatedButton(
          onPressed: () {},
          style: ElevatedButton.styleFrom(shape: const CircleBorder(), padding: const EdgeInsets.all(20), backgroundColor: Colors.deepPurple, foregroundColor: Colors.white),
          child: Icon(icon),
        ),
        const SizedBox(height: 8),
        Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
      ],
    );
  }
}