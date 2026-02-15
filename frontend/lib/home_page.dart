import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'create_event_page.dart'; // Import the new creation page

// --- Data Models matching the FastAPI schemas ---

class ForecastDTO {
  final double temperature;
  final double precipitation;
  final double wind;
  final String description;

  ForecastDTO({
    required this.temperature,
    required this.precipitation,
    required this.wind,
    required this.description,
  });

  factory ForecastDTO.fromJson(Map<String, dynamic> json) {
    return ForecastDTO(
      temperature: (json['temperature'] as num).toDouble(),
      precipitation: (json['precipitation'] as num).toDouble(),
      wind: (json['wind'] as num).toDouble(),
      description: json['description'] ?? "",
    );
  }
}

class WeatherResponseDTO {
  final List<ForecastDTO> forecast;

  WeatherResponseDTO({required this.forecast});

  factory WeatherResponseDTO.fromJson(Map<String, dynamic> json) {
    var list = json['forecast'] as List;
    return WeatherResponseDTO(
      forecast: list.map((i) => ForecastDTO.fromJson(i)).toList(),
    );
  }
}

// New Models for Recommendations
class RecommendationItemDTO {
  final String activityName;
  final String activityDescription;

  RecommendationItemDTO({
    required this.activityName,
    required this.activityDescription,
  });

  factory RecommendationItemDTO.fromJson(Map<String, dynamic> json) {
    return RecommendationItemDTO(
      activityName: json['activity_name'],
      activityDescription: json['activity_description'],
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  // State variables
  WeatherResponseDTO? _weatherData;
  List<RecommendationItemDTO> _personalRecommendations = [];
  List<RecommendationItemDTO> _groupRecommendations = [];
  
  bool _isLoadingWeather = true;
  bool _isLoadingRecommendations = true;
  String? _weatherError;

  @override
  void initState() {
    super.initState();
    _fetchWeather();
    _fetchRecommendations();
  }

  String _getBaseUrl() {
    if (kIsWeb) return 'http://127.0.0.1:8000';
    if (defaultTargetPlatform == TargetPlatform.android) return 'http://10.0.2.2:8000';
    return 'http://127.0.0.1:8000';
  }

  Future<String?> _getToken() async {
    return await _storage.read(key: 'jwt_token');
  }

  /// Fetches weather from the backend using lat/lon
  Future<void> _fetchWeather() async {
    setState(() {
      _isLoadingWeather = true;
      _weatherError = null;
    });

    final baseUrl = _getBaseUrl();
    const double lat = 35.7721;
    const double lon = -78.6382;

    final url = Uri.parse('$baseUrl/weather?lat=$lat&lon=$lon');

    try {
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _weatherData = WeatherResponseDTO.fromJson(data);
          _isLoadingWeather = false;
        });
      } else {
        setState(() {
          _weatherError = 'Weather unavailable (${response.statusCode})';
          _isLoadingWeather = false;
        });
      }
    } catch (e) {
      setState(() {
        _weatherError = 'Connection Error';
        _isLoadingWeather = false;
      });
    }
  }

  /// Fetches AI recommendations for User and their first Circle
  Future<void> _fetchRecommendations() async {
    setState(() => _isLoadingRecommendations = true);
    final baseUrl = _getBaseUrl();
    final token = await _getToken();

    if (token == null) {
      setState(() => _isLoadingRecommendations = false);
      return;
    }

    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };

    try {
      // 1. Fetch Personal Recommendations (POST /gemini/recommendations)
      final personalResponse = await http.post(
        Uri.parse('$baseUrl/gemini/recommendations'),
        headers: headers,
      );

      if (personalResponse.statusCode == 200) {
        final data = json.decode(personalResponse.body);
        final list = data['recommendations'] as List;
        _personalRecommendations = list.map((i) => RecommendationItemDTO.fromJson(i)).toList();
      }

      // 2. Fetch User Circles to get an ID for Group Recommendations
      final circlesResponse = await http.get(
        Uri.parse('$baseUrl/me/circles'),
        headers: headers,
      );

      if (circlesResponse.statusCode == 200) {
        final List circlesData = json.decode(circlesResponse.body);
        if (circlesData.isNotEmpty) {
          // Pick the first circle found
          final int firstCircleId = circlesData[0]['id'];
          
          // 3. Fetch Group Recommendations (POST /gemini/recommendations/{id})
          final groupRecResponse = await http.post(
            Uri.parse('$baseUrl/gemini/recommendations/$firstCircleId'),
            headers: headers,
          );

          if (groupRecResponse.statusCode == 200) {
            final groupData = json.decode(groupRecResponse.body);
            final groupList = groupData['recommendations'] as List;
            _groupRecommendations = groupList.map((i) => RecommendationItemDTO.fromJson(i)).toList();
          }
        }
      }
    } catch (e) {
      debugPrint("Recommendation Fetch Error: $e");
    } finally {
      if (mounted) {
        setState(() => _isLoadingRecommendations = false);
      }
    }
  }

  // Navigation Logic for Sliding Window
  void _openCreateEventPage(String name, String description) {
    Navigator.of(context).push(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => CreateEventPage(
          initialTitle: name,
          initialDescription: description,
        ),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          const begin = Offset(0.0, 1.0); // Slide up from bottom
          const end = Offset.zero;
          const curve = Curves.easeOutCubic;

          var tween = Tween(begin: begin, end: end).chain(CurveTween(curve: curve));

          return SlideTransition(
            position: animation.drive(tween),
            child: child,
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Home'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              _fetchWeather();
              _fetchRecommendations();
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          const Text(
            'Welcome back!',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 20),
          
          _buildWeatherSection(),
          
          const SizedBox(height: 24),
          const Text(
            'Recommendations',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),

          _buildRecommendationSection(),
          
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildWeatherSection() {
    if (_isLoadingWeather) {
      return Container(
        height: 160,
        decoration: BoxDecoration(
          color: Colors.grey.shade200,
          borderRadius: BorderRadius.circular(24),
        ),
        child: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_weatherError != null || _weatherData == null || _weatherData!.forecast.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: Colors.red.shade50,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.red.shade100),
        ),
        child: Column(
          children: [
            const Icon(Icons.cloud_off, color: Colors.red, size: 40),
            const SizedBox(height: 8),
            Text(_weatherError ?? 'Weather data empty', style: const TextStyle(color: Colors.red)),
            TextButton(onPressed: _fetchWeather, child: const Text("Retry")),
          ],
        ),
      );
    }

    final current = _weatherData!.forecast.first;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.orange.shade300, Colors.orange.shade600],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.orange.withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'CURRENT FORECAST',
                      style: TextStyle(
                        color: Colors.white70,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${current.temperature.round()}° Degrees',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                _getWeatherIcon(current.description),
                size: 60,
                color: Colors.white.withOpacity(0.9),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            current.description,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              height: 1.3,
            ),
          ),
          const Divider(color: Colors.white24, height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildSmallDetail(Icons.water_drop, "${current.precipitation.round()}%"),
              _buildSmallDetail(Icons.air, "${current.wind.round()} mph"),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildRecommendationSection() {
    if (_isLoadingRecommendations) {
      return const Center(child: Padding(
        padding: EdgeInsets.all(20.0),
        child: CircularProgressIndicator(),
      ));
    }

    if (_personalRecommendations.isEmpty && _groupRecommendations.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.grey.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
        ),
        child: const Text(
          "Unable to generate recommendations. Please ensure you have added interests in your Profile.",
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey),
        ),
      );
    }

    return Column(
      children: [
        // Personal Recommendations
        ..._personalRecommendations.map((rec) => _buildInfoCard(
          context,
          title: 'Personal Recommendation',
          content: rec.activityName,
          description: rec.activityDescription,
          icon: Icons.person_outline,
          iconColor: Colors.blue,
          onTap: () => _openCreateEventPage(rec.activityName, rec.activityDescription),
        )),

        // Group Recommendations
        ..._groupRecommendations.map((rec) => _buildInfoCard(
          context,
          title: 'Group Recommendation',
          content: rec.activityName,
          description: rec.activityDescription,
          icon: Icons.groups_outlined,
          iconColor: Colors.deepPurple,
          onTap: () => _openCreateEventPage(rec.activityName, rec.activityDescription),
        )),
      ],
    );
  }

  Widget _buildSmallDetail(IconData icon, String value) {
    return Row(
      children: [
        Icon(icon, color: Colors.white70, size: 16),
        const SizedBox(width: 4),
        Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ],
    );
  }

  IconData _getWeatherIcon(String description) {
    final d = description.toLowerCase();
    if (d.contains('sun') || d.contains('clear')) return Icons.wb_sunny_rounded;
    if (d.contains('rain') || d.contains('shower')) return Icons.umbrella_rounded;
    if (d.contains('storm')) return Icons.thunderstorm_rounded;
    if (d.contains('snow')) return Icons.ac_unit_rounded;
    return Icons.cloud_rounded;
  }

  Widget _buildInfoCard(BuildContext context,
      {required String title,
      required String content,
      String? description,
      required IconData icon,
      required Color iconColor,
      required VoidCallback onTap}) {
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: iconColor),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: iconColor.withOpacity(0.8),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      content,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (description != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: const TextStyle(
                          fontSize: 14,
                          color: Colors.grey,
                        ),
                      ),
                    ]
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}