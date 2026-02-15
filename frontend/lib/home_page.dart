import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

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

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  // State variables
  WeatherResponseDTO? _weatherData;
  bool _isLoadingWeather = true;
  String? _weatherError;

  @override
  void initState() {
    super.initState();
    _fetchWeather();
  }

  String _getBaseUrl() {
    if (kIsWeb) return 'http://127.0.0.1:8000';
    if (defaultTargetPlatform == TargetPlatform.android) return 'http://10.0.2.2:8000';
    return 'http://127.0.0.1:8000';
  }

  /// Fetches weather from the backend using lat/lon
  Future<void> _fetchWeather() async {
    setState(() {
      _isLoadingWeather = true;
      _weatherError = null;
    });

    final baseUrl = _getBaseUrl();
    // Defaulting to Raleigh, NC as per your schema defaults
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Home'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchWeather,
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

          _buildInfoCard(
            context,
            title: 'Personal Recommendation',
            content: "It's a great day to paddleboard!",
            icon: Icons.surfing_rounded,
            iconColor: Colors.blue,
            onTap: () {},
          ),
          _buildInfoCard(
            context,
            title: 'Group Recommendation',
            content: "Your group likes basketball, check the court availability!",
            icon: Icons.sports_basketball_rounded,
            iconColor: Colors.deepPurple,
            onTap: () {},
          ),
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

    // Use the first period of the forecast for the main display
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
                        fontSize: 15,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
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