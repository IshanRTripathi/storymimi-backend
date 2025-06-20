# Flutter Integration Guide for StoryMimi Backend

This guide provides detailed steps for integrating your Flutter Android app with the StoryMimi backend API. It covers authentication, endpoint usage, error handling, and best practices.

## 1. API Base URL

The base URL for all API endpoints is:
```
https://storymimi-api-165490622852.us-central1.run.app
```

⚠️ **IMPORTANT**: The backend is currently under development. Only the `/stories/public/categorized` endpoint is fully functional. Other endpoints are either broken or not implemented yet.

## 2. Working API Endpoints

### 2.1 Get Categorized Public Stories
Endpoint: `GET /stories/public/categorized`

This is the only fully functional endpoint. It returns stories grouped by category.

Example Response:
```json
{
  "categories": ["fantasy", "science-fiction", "adventure"],
  "stories": {
    "fantasy": [
      {
        "id": "049ee9be-2dd9-4335-bc18-05e78ad02c11",
        "title": "The Magical Forest Adventure",
        "description": "Join Luna as she discovers an enchanted forest...",
        "cover_image_url": "https://mmzddstjikbpvtqlkesz.supabase.co/storage/v1/object/public/images/...",
        "tags": [...],
        "duration": "4 minutes",
        "featured": true,
        "view_count": 1250,
        "age_rating": "ALL",
        "category": "fantasy",
        "difficulty_level": "beginner",
        "created_at": "2025-06-20T10:02:15.449901",
        "updated_at": "2025-06-20T10:02:15.449901"
      }
    ],
    "science-fiction": [...],
    "adventure": [...]
  }
}
```

Example Request:
```dart
final response = await http.get(
  Uri.parse('https://storymimi-api-165490622852.us-central1.run.app/stories/public/categorized'),
  headers: {
    'Content-Type': 'application/json',
  },
);
```

## 3. Broken/Not Implemented Endpoints

⚠️ **WARNING**: The following endpoints are currently broken or not implemented:

1. `GET /stories/public` - Routing conflict with story detail endpoint
2. `POST /users/` - Method not allowed (405 error)
3. `GET /users/{user_id}/stories` - Python import error with Validator

## 4. Error Handling

The API returns standard HTTP status codes:
- 200: Success
- 404: Not Found (for story detail)
- 405: Method Not Allowed (for broken endpoints)
- 500: Internal Server Error

Example error handling:
```dart
try {
  final response = await http.get(uri);
  if (response.statusCode == 200) {
    // Handle success
    final data = jsonDecode(response.body);
    // Process data
  } else {
    // Handle error
    throw Exception('Failed to load data: ${response.statusCode}');
  }
} catch (e) {
  // Handle network error
  throw Exception('Error: $e');
}
```

## 5. Data Models

### 5.1 Story Data Model
```dart
class StoryData {
  final String id;
  final String title;
  final String? description;
  final String? coverImageUrl;
  final List<String> tags;
  final String duration;
  final bool featured;
  final int viewCount;
  final String ageRating;
  final String category;
  final String difficultyLevel;
  final DateTime createdAt;
  final DateTime updatedAt;

  StoryData({
    required this.id,
    required this.title,
    this.description,
    this.coverImageUrl,
    required this.tags,
    required this.duration,
    required this.featured,
    required this.viewCount,
    required this.ageRating,
    required this.category,
    required this.difficultyLevel,
    required this.createdAt,
    required this.updatedAt,
  });

  factory StoryData.fromJson(Map<String, dynamic> json) {
    return StoryData(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      coverImageUrl: json['cover_image_url'],
      tags: List<String>.from(json['tags'] ?? []),
      duration: json['duration'],
      featured: json['featured'] ?? false,
      viewCount: json['view_count'] ?? 0,
      ageRating: json['age_rating'],
      category: json['category'],
      difficultyLevel: json['difficulty_level'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}
```

## 2. Authentication

The API uses token-based authentication. You'll need to include an Authorization header with your requests:

```dart
final headers = {
  'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
  'Content-Type': 'application/json',
};
```

## 3. User Management

### 3.1 Create User
Endpoint: `POST /users/`

Request Body:
```dart
class UserCreate {
  final String email;
  final String username;

  UserCreate({required this.email, required this.username});

  Map<String, dynamic> toJson() {
    return {
      'email': email,
      'username': username,
    };
  }
}
```

Example Request:
```dart
final response = await http.post(
  Uri.parse('https://api.storymimi.com/users/'),
  headers: headers,
  body: jsonEncode(userCreate.toJson()),
);
```

### 3.2 Get User Stories
Endpoint: `GET /users/{user_id}/stories`

Example Request:
```dart
final response = await http.get(
  Uri.parse('https://api.storymimi.com/users/$userId/stories'),
  headers: headers,
);
```

## 4. Public Stories

### 4.1 Get All Public Stories
Endpoint: `GET /stories/public`

Optional Query Parameters:
- `category`: Filter by story category
- `tags`: Filter by tags (comma-separated)
- `featured`: Filter featured stories
- `age_rating`: Filter by age rating
- `difficulty`: Filter by difficulty level
- `limit`: Number of stories to return (default: 20)
- `offset`: Offset for pagination

Example Request:
```dart
final response = await http.get(
  Uri.parse(
    'https://api.storymimi.com/stories/public?category=adventure&limit=10'
  ),
  headers: headers,
);
```

### 4.2 Get Categorized Stories
Endpoint: `GET /stories/public/categorized`

Example Request:
```dart
final response = await http.get(
  Uri.parse('https://api.storymimi.com/stories/public/categorized'),
  headers: headers,
);
```

### 4.3 Get Story Details
Endpoint: `GET /stories/public/{story_id}`

Example Request:
```dart
final response = await http.get(
  Uri.parse('https://api.storymimi.com/stories/public/$storyId'),
  headers: headers,
);
```

## 5. Error Handling

The API returns standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

Example error handling:
```dart
try {
  final response = await http.get(uri, headers: headers);
  if (response.statusCode == 200) {
    // Handle success
    final data = jsonDecode(response.body);
    // Process data
  } else {
    // Handle error
    throw Exception('Failed to load data: ${response.statusCode}');
  }
} catch (e) {
  // Handle network error
  throw Exception('Error: $e');
}
```

## 6. Data Models

### 6.1 Public Story Summary
```dart
class PublicStorySummary {
  final String id;
  final String title;
  final String? description;
  final String? coverImageUrl;
  final List<String> tags;
  final String duration;
  final bool featured;
  final int viewCount;
  final String ageRating;
  final String category;
  final String difficultyLevel;
  final DateTime createdAt;
  final DateTime updatedAt;

  PublicStorySummary({
    required this.id,
    required this.title,
    this.description,
    this.coverImageUrl,
    required this.tags,
    required this.duration,
    required this.featured,
    required this.viewCount,
    required this.ageRating,
    required this.category,
    required this.difficultyLevel,
    required this.createdAt,
    required this.updatedAt,
  });

  factory PublicStorySummary.fromJson(Map<String, dynamic> json) {
    return PublicStorySummary(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      coverImageUrl: json['cover_image_url'],
      tags: List<String>.from(json['tags'] ?? []),
      duration: json['duration'],
      featured: json['featured'] ?? false,
      viewCount: json['view_count'] ?? 0,
      ageRating: json['age_rating'],
      category: json['category'],
      difficultyLevel: json['difficulty_level'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}
```

### 6.2 Public Story Detail
```dart
class PublicStoryScene {
  final int sequence;
  final String text;
  final String? imageUrl;
  final String? audioUrl;

  PublicStoryScene({
    required this.sequence,
    required this.text,
    this.imageUrl,
    this.audioUrl,
  });

  factory PublicStoryScene.fromJson(Map<String, dynamic> json) {
    return PublicStoryScene(
      sequence: json['sequence'],
      text: json['text'],
      imageUrl: json['image_url'],

1. **Error Handling**
   - Always implement proper error handling
   - Use try-catch blocks for network requests
   - Show user-friendly error messages
   - Handle broken endpoints gracefully

2. **State Management**
   - Use a state management solution (e.g., Provider, Riverpod, Bloc)
   - Cache frequently accessed data
   - Implement pagination for large lists

3. **Network Requests**
   - Use Dio or http package for network requests
   - Implement request timeouts
   - Add retry logic for failed requests
   - Cache responses where appropriate

4. **UI/UX**
   - Show loading indicators during requests
   - Implement pull-to-refresh
   - Cache images using cached_network_image
   - Handle offline scenarios gracefully

## 7. Example Integration

Here's a complete example of integrating with the working public stories endpoint:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class StoryMimiApi {
  static const String baseUrl = 'https://storymimi-api-165490622852.us-central1.run.app';

  Map<String, String> get headers => {
    'Content-Type': 'application/json',
  };

  Future<Map<String, List<StoryData>>> getCategorizedStories() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/stories/public/categorized'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final storiesMap = data['stories'] as Map<String, dynamic>;
        
        Map<String, List<StoryData>> result = {};
        for (String category in storiesMap.keys) {
          final stories = storiesMap[category] as List;
          result[category] = stories
              .map((story) => StoryData.fromJson(story))
              .toList();
        }
        return result;
      } else {
        throw Exception('Failed to load stories: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error loading stories: $e');
    }
  }

  // Note: These methods are placeholders until backend is fixed
  Future<void> createUser() async {
    throw UnimplementedError('User creation endpoint not implemented yet');
  }

  Future<List<StoryData>> getUserStories(String userId) async {
    throw UnimplementedError('User stories endpoint not implemented yet');
  }
}

// Usage example
final api = StoryMimiApi();
try {
  final stories = await api.getCategorizedStories();
  // Process stories
} catch (e) {
  // Handle error
  print('Error: $e');
}
```

## 8. Troubleshooting

1. **Common Issues**
   - 404 Not Found: Verify the endpoint URL
   - 405 Method Not Allowed: The endpoint is not implemented yet
   - 500 Internal Server Error: Contact support with error details

2. **Debugging**
   - Add logging to track requests
   - Check network tab in Flutter DevTools
   - Verify request headers and body
   - Test working endpoints using Postman or curl

3. **Known Issues**
   - `/stories/public` endpoint has routing conflict
   - `/users/` endpoints are not implemented yet
   - Some endpoints may return 405 Method Not Allowed

## 9. Security Considerations

1. **Token Management**
   - Store tokens securely using Flutter Secure Storage
   - Never hardcode tokens in code
   - Implement token refresh logic

2. **Data Validation**
   - Validate all incoming data
   - Handle null values gracefully
   - Implement proper type checking

3. **Network Security**
   - Use HTTPS for all requests
   - Validate SSL certificates
   - Implement proper timeout settings

This guide provides a comprehensive overview of integrating your Flutter app with the StoryMimi backend. For more specific use cases or additional features, please refer to the API documentation or contact the development team.
