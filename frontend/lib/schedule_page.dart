import 'dart:convert';
import 'dart:io';
import 'dart:js_interop';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:web/web.dart' as web;

class EventResponseDTO {
  final int id;
  final String name;
  final String? description;
  final DateTime startAt;
  final DateTime endAt;
  final String state;

  EventResponseDTO({
    required this.id,
    required this.name,
    this.description,
    required this.startAt,
    required this.endAt,
    required this.state,
  });

  factory EventResponseDTO.fromJson(Map<String, dynamic> json) {
    return EventResponseDTO(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      startAt: DateTime.parse(json['start_at']),
      endAt: DateTime.parse(json['end_at']),
      state: json['state'],
    );
  }
}

class SchedulePage extends StatefulWidget {
  const SchedulePage({super.key});

  @override
  State<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends State<SchedulePage> {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  List<EventResponseDTO> _events = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchEvents();
  }

  Future<void> _fetchEvents() async {
    String baseUrl;
    if (kIsWeb) {
      baseUrl = 'http://127.0.0.1:8000';
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      baseUrl = 'http://10.0.2.2:8000';
    } else {
      baseUrl = 'http://127.0.0.1:8000';
    }

    final url = Uri.parse('$baseUrl/me/events');

    try {
      final String? token = await _storage.read(key: 'jwt_token');

      if (token == null) {
        setState(() {
          _errorMessage = 'Login required to see events.';
          _isLoading = false;
        });
        return;
      }

      final response = await http.get(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          _events = data.map((e) => EventResponseDTO.fromJson(e)).toList();
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = 'Failed to load events: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Network error. Is your backend running?';
        _isLoading = false;
      });
      debugPrint("Schedule Fetch Error: $e");
    }
  }

  String _formatDateTime(DateTime dt) {
    // Format: Feb 15, 8:00 AM
    return DateFormat('MMM d, h:mm a').format(dt);
  }

  String _generateICalContent(EventResponseDTO event) {
    // Format dates for iCal (YYYYMMDDTHHMMSSZ format)
    String formatDateForICal(DateTime dt) {
      return DateFormat('yyyyMMddTHHmmss').format(dt);
    }

    final startDt = formatDateForICal(event.startAt);
    final endDt = formatDateForICal(event.endAt);
    final now = formatDateForICal(DateTime.now());
    
    return '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//OutSource App//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
UID:event-${event.id}-@outsource.app
DTSTAMP:${now}Z
DTSTART:$startDt
DTEND:$endDt
SUMMARY:${event.name}
DESCRIPTION:${event.description ?? ''}
STATUS:${event.state.toUpperCase()}
END:VEVENT
END:VCALENDAR''';
  }

  Future<void> _exportEventAsICal(EventResponseDTO event) async {
    try {
      final iCalContent = _generateICalContent(event);
      final safeEventName = event.name
          .replaceAll(RegExp(r'[<>:"/\\|?*]'), '')
          .replaceAll(' ', '_');
      final fileName = '${safeEventName}_${event.id}.ics';
      
      if (kIsWeb) {
        // On web, create a download with proper MIME type
        _downloadICalFileWeb(iCalContent, fileName);
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Downloading $fileName')),
          );
        }
      } else {
        // On mobile/desktop, save to file and open with calendar app
        final Directory directory = await getApplicationDocumentsDirectory();
        final filePath = '${directory.path}/$fileName';

        // Write the file
        final file = File(filePath);
        await file.writeAsString(iCalContent);

        // Try to open the file with the default calendar app
        final uri = Uri.file(filePath);
        if (await canLaunchUrl(uri)) {
          await launchUrl(uri);
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Opening $fileName')),
            );
          }
        } else {
          // Fallback: just show the path
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Saved to: $filePath'),
                duration: const Duration(seconds: 4),
              ),
            );
          }
        }
      }
    } catch (e) {
      debugPrint('Export error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to export event')),
        );
      }
    }
  }

  void _downloadICalFileWeb(String content, String fileName) {
    if (kIsWeb) {
      // Create a blob with text/calendar MIME type
      final bytes = utf8.encode(content);
      final blob = web.Blob([bytes.toJS].toJS, web.BlobPropertyBag(type: 'text/calendar;charset=utf-8'));
      final url = web.URL.createObjectURL(blob);
      final anchor = web.document.createElement('a') as web.HTMLAnchorElement
        ..href = url
        ..download = fileName
        ..style.display = 'none';
      
      web.document.body?.appendChild(anchor);
      anchor.click();
      anchor.remove();
      web.URL.revokeObjectURL(url);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Schedule'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              setState(() => _isLoading = true);
              _fetchEvents();
            },
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Text(_errorMessage!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.red)),
                ))
              : _events.isEmpty
                  ? _buildEmptyState()
                  : _buildEventList(),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.calendar_today_outlined, size: 64, color: Colors.grey.shade300),
          const SizedBox(height: 16),
          const Text("No events scheduled yet!", style: TextStyle(color: Colors.grey, fontSize: 16)),
        ],
      ),
    );
  }

  Widget _buildEventList() {
    return RefreshIndicator(
      onRefresh: _fetchEvents,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
        itemCount: _events.length,
        itemBuilder: (context, index) {
          final event = _events[index];
          return Container(
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.02),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                )
              ]
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildStateIndicator(event.state),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          event.name,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold, 
                            fontSize: 17,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            Icon(Icons.access_time, size: 14, color: Theme.of(context).colorScheme.primary),
                            const SizedBox(width: 4),
                            Text(
                              _formatDateTime(event.startAt),
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.primary, 
                                fontWeight: FontWeight.w600,
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                        if (event.description != null && event.description!.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Text(
                            event.description!,
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey.shade700,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  IconButton(
                    icon: const Icon(Icons.download),
                    tooltip: 'Export event',
                    onPressed: () => _exportEventAsICal(event),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildStateIndicator(String state) {
    // Map backend state to UI colors
    Color color = Colors.blue;
    IconData icon = Icons.event;
    
    if (state.toLowerCase() == 'confirmed') {
      color = Colors.green;
      icon = Icons.check_circle_outline;
    } else if (state.toLowerCase() == 'pending') {
      color = Colors.orange;
      icon = Icons.hourglass_empty;
    }

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        shape: BoxShape.circle,
      ),
      child: Icon(icon, size: 20, color: color),
    );
  }
}