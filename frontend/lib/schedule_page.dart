import 'package:flutter/material.dart';

class SchedulePage extends StatelessWidget {
  const SchedulePage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<Map<String, dynamic>> events = [
      {
        'name': 'Morning Paddleboard',
        'time': 'Feb 15, 8:00 AM',
        'desc': 'Catching the calm water before the wind picks up.',
        'type': 'solo'
      },
      {
        'name': 'Brunch with Taylor',
        'time': 'Feb 15, 11:30 AM',
        'desc': 'Checking out that new cafe downtown.',
        'type': 'friend'
      },
      {
        'name': 'Group Basketball',
        'time': 'Feb 16, 6:00 PM',
        'desc': 'Weekly pickup game at the community center.',
        'type': 'group'
      },
      {
        'name': 'Solo Gym Session',
        'time': 'Feb 17, 7:00 AM',
        'desc': 'Leg day and some light cardio.',
        'type': 'solo'
      },
      {
        'name': 'Water Polo Match',
        'time': 'Feb 18, 5:30 PM',
        'desc': 'Indoor pool session with the local league.',
        'type': 'group'
      },
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Schedule')),
      body: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
        itemCount: events.length,
        itemBuilder: (context, index) {
          final event = events[index];
          return Container(
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(top: 4.0),
                    child: _buildTypeIcon(event['type']),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          event['name'],
                          style: const TextStyle(
                            fontWeight: FontWeight.bold, 
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          event['time'],
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.primary, 
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          event['desc'],
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey.shade700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildTypeIcon(String type) {
    switch (type) {
      case 'solo':
        return const CircleAvatar(
          radius: 18,
          backgroundColor: Color(0xFFE3F2FD),
          child: Icon(Icons.person, size: 18, color: Colors.blue),
        );
      case 'friend':
        return Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(color: Colors.green.withOpacity(0.1), shape: BoxShape.circle),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.circle, size: 8, color: Colors.green),
              SizedBox(width: 2),
              Icon(Icons.circle, size: 8, color: Colors.green),
            ],
          ),
        );
      case 'group':
        return Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(color: Colors.deepPurple.withOpacity(0.1), shape: BoxShape.circle),
          child: const Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.circle, size: 6, color: Colors.deepPurple),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.circle, size: 6, color: Colors.deepPurple),
                  SizedBox(width: 2),
                  Icon(Icons.circle, size: 6, color: Colors.deepPurple),
                ],
              ),
            ],
          ),
        );
      default:
        return const Icon(Icons.event);
    }
  }
}