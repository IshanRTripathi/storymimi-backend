# Flutter Implementation Guide
## Practical Code Examples for Story Generation App

### Project Structure

```
lib/
├── core/
│   ├── api/
│   │   ├── api_client.dart
│   │   ├── conversation_api.dart
│   │   └── story_api.dart
│   ├── cache/
│   │   ├── cache_manager.dart
│   │   └── media_cache.dart
│   ├── models/
│   │   ├── conversation.dart
│   │   ├── story.dart
│   │   └── user.dart
│   └── services/
│       ├── conversation_service.dart
│       ├── story_service.dart
│       └── media_service.dart
├── features/
│   ├── conversation/
│   │   ├── bloc/
│   │   ├── widgets/
│   │   └── screens/
│   ├── story/
│   │   ├── bloc/
│   │   ├── widgets/
│   │   └── screens/
│   └── home/
└── main.dart
```

### 1. Core API Client Setup

#### `lib/core/api/api_client.dart`

```dart
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:dio_retry/dio_retry.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio _dio;
  static const String baseUrl = 'https://your-api-domain.com';
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(minutes: 2);

  ApiClient._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: connectTimeout,
      receiveTimeout: receiveTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    _setupInterceptors();
  }

  void _setupInterceptors() {
    // Cache interceptor
    _dio.interceptors.add(DioCacheInterceptor(
      options: CacheOptions(
        store: MemCacheStore(),
        policy: CachePolicy.request,
        hitCacheOnErrorExcept: [401, 403],
        maxStale: const Duration(days: 7),
        priority: CachePriority.normal,
      ),
    ));

    // Retry interceptor
    _dio.interceptors.add(RetryInterceptor(
      dio: _dio,
      logPrint: print,
      retries: 3,
      retryDelays: const [
        Duration(seconds: 1),
        Duration(seconds: 2),
        Duration(seconds: 3),
      ],
    ));

    // Logging interceptor
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
        logPrint: (obj) => print(obj),
      ));
    }

    // Auth interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _getAuthToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          // Handle token refresh
          await _refreshToken();
          // Retry request
          final clonedRequest = await _dio.request(
            error.requestOptions.path,
            options: Options(
              method: error.requestOptions.method,
              headers: error.requestOptions.headers,
            ),
            data: error.requestOptions.data,
            queryParameters: error.requestOptions.queryParameters,
          );
          handler.resolve(clonedRequest);
        } else {
          handler.next(error);
        }
      },
    ));
  }

  Future<String?> _getAuthToken() async {
    // Implement token retrieval from secure storage
    return null;
  }

  Future<void> _refreshToken() async {
    // Implement token refresh logic
  }

  Dio get dio => _dio;
}
```

#### `lib/core/api/conversation_api.dart`

```dart
import 'package:dio/dio.dart';
import '../models/conversation.dart';
import 'api_client.dart';

class ConversationApi {
  final Dio _dio = ApiClient().dio;

  Future<Conversation> createConversation(String userId) async {
    try {
      final response = await _dio.post('/conversations/', data: {
        'user_id': userId,
      });
      return Conversation.fromJson(response.data);
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<List<ConversationMessage>> getConversationHistory(
    String conversationId, {
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final response = await _dio.get(
        '/conversations/$conversationId',
        queryParameters: {
          'limit': limit,
          'offset': offset,
        },
      );
      return (response.data['messages'] as List)
          .map((json) => ConversationMessage.fromJson(json))
          .toList();
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<ConversationMessage> sendMessage(
    String conversationId,
    String content, {
    String messageType = 'user',
  }) async {
    try {
      final response = await _dio.post(
        '/conversations/$conversationId/messages',
        data: {
          'content': content,
          'message_type': messageType,
        },
      );
      return ConversationMessage.fromJson(response.data);
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<StoryRequirements> extractRequirements(String conversationId) async {
    try {
      final response = await _dio.post(
        '/conversations/$conversationId/extract-requirements',
      );
      return StoryRequirements.fromJson(response.data);
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<List<ConversationMessage>> getRecentTranscripts(
    String conversationId,
    int limit,
  ) async {
    try {
      final response = await _dio.get(
        '/conversations/$conversationId/transcripts/recent/$limit',
      );
      return (response.data as List)
          .map((json) => ConversationMessage.fromJson(json))
          .toList();
    } catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(dynamic error) {
    if (error is DioException) {
      switch (error.type) {
        case DioExceptionType.connectionTimeout:
        case DioExceptionType.sendTimeout:
        case DioExceptionType.receiveTimeout:
          return NetworkException('Connection timeout');
        case DioExceptionType.badResponse:
          return ServerException(
            'Server error: ${error.response?.statusCode}',
            error.response?.statusCode,
          );
        case DioExceptionType.unknown:
          return NetworkException('Network error');
        default:
          return UnknownException('Unknown error occurred');
      }
    }
    return UnknownException(error.toString());
  }
}

// Custom exceptions
class NetworkException implements Exception {
  final String message;
  NetworkException(this.message);
}

class ServerException implements Exception {
  final String message;
  final int? statusCode;
  ServerException(this.message, this.statusCode);
}

class UnknownException implements Exception {
  final String message;
  UnknownException(this.message);
}
```

### 2. Data Models

#### `lib/core/models/conversation.dart`

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'conversation.freezed.dart';
part 'conversation.g.dart';

@freezed
class Conversation with _$Conversation {
  const factory Conversation({
    required String conversationId,
    required String userId,
    String? title,
    @Default('active') String status,
    required DateTime createdAt,
    required DateTime updatedAt,
    @Default(0) int messageCount,
  }) = _Conversation;

  factory Conversation.fromJson(Map<String, dynamic> json) =>
      _$ConversationFromJson(json);
}

@freezed
class ConversationMessage with _$ConversationMessage {
  const factory ConversationMessage({
    required String messageId,
    required String conversationId,
    required String userId,
    required String content,
    @Default('user') String messageType,
    required DateTime timestamp,
    Map<String, dynamic>? metadata,
  }) = _ConversationMessage;

  factory ConversationMessage.fromJson(Map<String, dynamic> json) =>
      _$ConversationMessageFromJson(json);
}

@freezed
class StoryRequirements with _$StoryRequirements {
  const factory StoryRequirements({
    required String title,
    String? genre,
    List<String>? characters,
    String? setting,
    String? tone,
    String? length,
    String? specialRequests,
    required String extractedPrompt,
  }) = _StoryRequirements;

  factory StoryRequirements.fromJson(Map<String, dynamic> json) =>
      _$StoryRequirementsFromJson(json);
}
```

#### `lib/core/models/story.dart`

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'story.freezed.dart';
part 'story.g.dart';

enum StoryStatus {
  @JsonValue('pending')
  pending,
  @JsonValue('processing')
  processing,
  @JsonValue('completed')
  completed,
  @JsonValue('failed')
  failed,
}

@freezed
class Story with _$Story {
  const factory Story({
    required String storyId,
    required String title,
    required StoryStatus status,
    required String userId,
    required DateTime createdAt,
    required DateTime updatedAt,
    String? error,
    @Default([]) List<Scene> scenes,
    Map<String, dynamic>? storyMetadata,
  }) = _Story;

  factory Story.fromJson(Map<String, dynamic> json) => _$StoryFromJson(json);
}

@freezed
class Scene with _$Scene {
  const factory Scene({
    required String sceneId,
    required String storyId,
    required int sequence,
    required String title,
    required String text,
    required String imagePrompt,
    String? imageUrl,
    String? audioUrl,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _Scene;

  factory Scene.fromJson(Map<String, dynamic> json) => _$SceneFromJson(json);
}

@freezed
class StoryStatusDetail with _$StoryStatusDetail {
  const factory StoryStatusDetail({
    required String storyId,
    required StoryStatus status,
    @Default(0) int progressPercentage,
    String? currentStep,
    DateTime? estimatedCompletion,
    String? errorDetails,
  }) = _StoryStatusDetail;

  factory StoryStatusDetail.fromJson(Map<String, dynamic> json) =>
      _$StoryStatusDetailFromJson(json);
}
```

### 3. Conversation Feature Implementation

#### `lib/features/conversation/bloc/conversation_bloc.dart`

```dart
import 'package:bloc/bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../core/models/conversation.dart';
import '../../../core/services/conversation_service.dart';

part 'conversation_bloc.freezed.dart';
part 'conversation_event.dart';
part 'conversation_state.dart';

class ConversationBloc extends Bloc<ConversationEvent, ConversationState> {
  final ConversationService _conversationService;

  ConversationBloc(this._conversationService) : super(const ConversationState()) {
    on<_StartConversation>(_onStartConversation);
    on<_SendMessage>(_onSendMessage);
    on<_LoadHistory>(_onLoadHistory);
    on<_ExtractRequirements>(_onExtractRequirements);
    on<_ClearConversation>(_onClearConversation);
  }

  Future<void> _onStartConversation(
    _StartConversation event,
    Emitter<ConversationState> emit,
  ) async {
    emit(state.copyWith(isLoading: true, error: null));
    
    try {
      final conversation = await _conversationService.createConversation(event.userId);
      emit(state.copyWith(
        conversation: conversation,
        isLoading: false,
        messages: [],
      ));
    } catch (e) {
      emit(state.copyWith(
        isLoading: false,
        error: e.toString(),
      ));
    }
  }

  Future<void> _onSendMessage(
    _SendMessage event,
    Emitter<ConversationState> emit,
  ) async {
    if (state.conversation == null) return;

    // Add user message immediately
    final userMessage = ConversationMessage(
      messageId: DateTime.now().millisecondsSinceEpoch.toString(),
      conversationId: state.conversation!.conversationId,
      userId: state.conversation!.userId,
      content: event.content,
      messageType: 'user',
      timestamp: DateTime.now(),
    );

    emit(state.copyWith(
      messages: [...state.messages, userMessage],
      isTyping: true,
    ));

    try {
      final response = await _conversationService.sendMessage(
        state.conversation!.conversationId,
        event.content,
      );

      emit(state.copyWith(
        messages: [...state.messages, response],
        isTyping: false,
      ));
    } catch (e) {
      emit(state.copyWith(
        isTyping: false,
        error: e.toString(),
      ));
    }
  }

  Future<void> _onLoadHistory(
    _LoadHistory event,
    Emitter<ConversationState> emit,
  ) async {
    if (state.conversation == null) return;

    try {
      final messages = await _conversationService.getConversationHistory(
        state.conversation!.conversationId,
        limit: event.limit,
        offset: event.offset,
      );

      emit(state.copyWith(
        messages: event.offset == 0 ? messages : [...messages, ...state.messages],
        isLoading: false,
      ));
    } catch (e) {
      emit(state.copyWith(
        isLoading: false,
        error: e.toString(),
      ));
    }
  }

  Future<void> _onExtractRequirements(
    _ExtractRequirements event,
    Emitter<ConversationState> emit,
  ) async {
    if (state.conversation == null) return;

    emit(state.copyWith(isExtracting: true));

    try {
      final requirements = await _conversationService.extractRequirements(
        state.conversation!.conversationId,
      );

      emit(state.copyWith(
        storyRequirements: requirements,
        isExtracting: false,
      ));
    } catch (e) {
      emit(state.copyWith(
        isExtracting: false,
        error: e.toString(),
      ));
    }
  }

  Future<void> _onClearConversation(
    _ClearConversation event,
    Emitter<ConversationState> emit,
  ) async {
    emit(const ConversationState());
  }
}
```

#### `lib/features/conversation/screens/conversation_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:dash_chat_2/dash_chat_2.dart';
import '../bloc/conversation_bloc.dart';
import '../widgets/typing_indicator.dart';
import '../widgets/voice_input_button.dart';
import '../../story/screens/story_generation_screen.dart';

class ConversationScreen extends StatefulWidget {
  final String userId;

  const ConversationScreen({
    Key? key,
    required this.userId,
  }) : super(key: key);

  @override
  State<ConversationScreen> createState() => _ConversationScreenState();
}

class _ConversationScreenState extends State<ConversationScreen> {
  final TextEditingController _messageController = TextEditingController();
  late final ChatUser _user;
  late final ChatUser _assistant;

  @override
  void initState() {
    super.initState();
    _user = ChatUser(id: widget.userId, firstName: 'You');
    _assistant = ChatUser(
      id: 'assistant',
      firstName: 'Story Assistant',
      profileImage: 'assets/images/assistant_avatar.png',
    );

    context.read<ConversationBloc>().add(
      ConversationEvent.startConversation(widget.userId),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Story Assistant'),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome),
            onPressed: _extractRequirements,
            tooltip: 'Generate Story',
          ),
        ],
      ),
      body: BlocConsumer<ConversationBloc, ConversationState>(
        listener: (context, state) {
          if (state.error != null) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.error!)),
            );
          }

          if (state.storyRequirements != null) {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (context) => StoryGenerationScreen(
                  requirements: state.storyRequirements!,
                  userId: widget.userId,
                ),
              ),
            );
          }
        },
        builder: (context, state) {
          if (state.isLoading && state.conversation == null) {
            return const Center(child: CircularProgressIndicator());
          }

          final messages = _convertToChateMessages(state.messages);

          return Column(
            children: [
              Expanded(
                child: DashChat(
                  currentUser: _user,
                  messages: messages,
                  onSend: _onSendMessage,
                  messageOptions: MessageOptions(
                    showTime: true,
                    avatarBuilder: _avatarBuilder,
                    messageTextBuilder: _messageTextBuilder,
                  ),
                  inputOptions: InputOptions(
                    inputDecoration: InputDecoration(
                      hintText: 'Tell me about your story idea...',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(25),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                    ),
                    trailing: [
                      VoiceInputButton(
                        onTranscription: _onSendMessage,
                      ),
                    ],
                  ),
                ),
              ),
              if (state.isTyping) const TypingIndicator(),
              if (state.isExtracting)
                Container(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: const [
                      CircularProgressIndicator(),
                      SizedBox(width: 16),
                      Text('Analyzing your requirements...'),
                    ],
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  List<ChatMessage> _convertToChateMessages(List<ConversationMessage> messages) {
    return messages.map((msg) {
      return ChatMessage(
        text: msg.content,
        user: msg.messageType == 'user' ? _user : _assistant,
        createdAt: msg.timestamp,
      );
    }).toList();
  }

  Widget _avatarBuilder(ChatUser user, Function? onAvatarTap, Function? onAvatarLongPress) {
    if (user.id == 'assistant') {
      return CircleAvatar(
        backgroundColor: Theme.of(context).primaryColor,
        child: const Icon(Icons.auto_awesome, color: Colors.white),
      );
    }
    return CircleAvatar(
      backgroundColor: Colors.grey[300],
      child: Text(user.firstName?[0] ?? 'U'),
    );
  }

  Widget _messageTextBuilder(ChatMessage message, ChatMessage? previousMessage, ChatMessage? nextMessage) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: message.user.id == widget.userId 
            ? Theme.of(context).primaryColor
            : Colors.grey[200],
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        message.text,
        style: TextStyle(
          color: message.user.id == widget.userId ? Colors.white : Colors.black87,
        ),
      ),
    );
  }

  void _onSendMessage(ChatMessage message) {
    context.read<ConversationBloc>().add(
      ConversationEvent.sendMessage(message.text),
    );
  }

  void _extractRequirements() {
    context.read<ConversationBloc>().add(
      const ConversationEvent.extractRequirements(),
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }
}
```

### 4. Story Status Polling Implementation

#### `lib/features/story/bloc/story_bloc.dart`

```dart
import 'dart:async';
import 'package:bloc/bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../core/models/story.dart';
import '../../../core/services/story_service.dart';

part 'story_bloc.freezed.dart';
part 'story_event.dart';
part 'story_state.dart';

class StoryBloc extends Bloc<StoryEvent, StoryState> {
  final StoryService _storyService;
  Timer? _statusTimer;

  StoryBloc(this._storyService) : super(const StoryState()) {
    on<_CreateStory>(_onCreateStory);
    on<_StartStatusPolling>(_onStartStatusPolling);
    on<_StopStatusPolling>(_onStopStatusPolling);
    on<_UpdateStatus>(_onUpdateStatus);
    on<_LoadStory>(_onLoadStory);
  }

  Future<void> _onCreateStory(
    _CreateStory event,
    Emitter<StoryState> emit,
  ) async {
    emit(state.copyWith(isLoading: true, error: null));

    try {
      final story = await _storyService.createStory(
        title: event.title,
        prompt: event.prompt,
        userId: event.userId,
      );

      emit(state.copyWith(
        story: story,
        isLoading: false,
      ));

      // Start status polling
      add(StoryEvent.startStatusPolling(story.storyId));
    } catch (e) {
      emit(state.copyWith(
        isLoading: false,
        error: e.toString(),
      ));
    }
  }

  Future<void> _onStartStatusPolling(
    _StartStatusPolling event,
    Emitter<StoryState> emit,
  ) async {
    _statusTimer?.cancel();
    
    // Initial status check
    await _checkStatus(event.storyId, emit);

    // Start polling with exponential backoff
    int pollInterval = 2; // Start with 2 seconds
    const maxInterval = 30; // Max 30 seconds

    _statusTimer = Timer.periodic(Duration(seconds: pollInterval), (timer) async {
      await _checkStatus(event.storyId, emit);

      // Stop polling if completed or failed
      if (state.story?.status == StoryStatus.completed ||
          state.story?.status == StoryStatus.failed) {
        timer.cancel();
        return;
      }

      // Increase interval (exponential backoff)
      if (pollInterval < maxInterval) {
        timer.cancel();
        pollInterval = (pollInterval * 1.5).round().clamp(2, maxInterval);
        _statusTimer = Timer.periodic(Duration(seconds: pollInterval), (newTimer) async {
          await _checkStatus(event.storyId, emit);
          if (state.story?.status == StoryStatus.completed ||
              state.story?.status == StoryStatus.failed) {
            newTimer.cancel();
          }
        });
      }
    });
  }

  Future<void> _checkStatus(String storyId, Emitter<StoryState> emit) async {
    try {
      final statusDetail = await _storyService.getStoryStatus(storyId);
      
      emit(state.copyWith(
        story: state.story?.copyWith(status: statusDetail.status),
        statusDetail: statusDetail,
      ));

      // If completed, load full story details
      if (statusDetail.status == StoryStatus.completed) {
        final fullStory = await _storyService.getStory(storyId);
        emit(state.copyWith(story: fullStory));
        
        // Preload media assets
        _preloadStoryAssets(fullStory);
      }
    } catch (e) {
      emit(state.copyWith(error: e.toString()));
    }
  }

  void _onStopStatusPolling(_StopStatusPolling event, Emitter<StoryState> emit) {
    _statusTimer?.cancel();
    _statusTimer = null;
  }

  Future<void> _onUpdateStatus(
    _UpdateStatus event,
    Emitter<StoryState> emit,
  ) async {
    emit(state.copyWith(statusDetail: event.statusDetail));
  }

  Future<void> _onLoadStory(
    _LoadStory event,
    Emitter<StoryState> emit,
  ) async {
    emit(state.copyWith(isLoading: true));

    try {
      final story = await _storyService.getStory(event.storyId);
      emit(state.copyWith(
        story: story,
        isLoading: false,
      ));

      _preloadStoryAssets(story);
    } catch (e) {
      emit(state.copyWith(
        isLoading: false,
        error: e.toString(),
      ));
    }
  }

  void _preloadStoryAssets(Story story) {
    // Preload images and audio in background
    for (final scene in story.scenes) {
      if (scene.imageUrl != null) {
        _storyService.preloadImage(scene.imageUrl!);
      }
      if (scene.audioUrl != null) {
        _storyService.preloadAudio(scene.audioUrl!);
      }
    }
  }

  @override
  Future<void> close() {
    _statusTimer?.cancel();
    return super.close();
  }
}
```

### 5. Media Caching and Download

#### `lib/core/cache/media_cache.dart`

```dart
import 'dart:io';
import 'package:flutter_cache_manager/flutter_cache_manager.dart';
import 'package:path/path.dart' as path;
import 'package:path_provider/path_provider.dart';

class MediaCacheManager {
  static final MediaCacheManager _instance = MediaCacheManager._internal();
  factory MediaCacheManager() => _instance;

  late final CacheManager _imageCacheManager;
  late final CacheManager _audioCacheManager;

  MediaCacheManager._internal() {
    _imageCacheManager = CacheManager(
      Config(
        'story_images',
        stalePeriod: const Duration(days: 30),
        maxNrOfCacheObjects: 500,
        repo: JsonCacheInfoRepository(databaseName: 'story_images'),
        fileService: HttpFileService(),
      ),
    );

    _audioCacheManager = CacheManager(
      Config(
        'story_audio',
        stalePeriod: const Duration(days: 7),
        maxNrOfCacheObjects: 100,
        repo: JsonCacheInfoRepository(databaseName: 'story_audio'),
        fileService: HttpFileService(),
      ),
    );
  }

  Future<File> downloadAndCacheImage(String url) async {
    return await _imageCacheManager.getSingleFile(url);
  }

  Future<File> downloadAndCacheAudio(String url) async {
    return await _audioCacheManager.getSingleFile(url);
  }

  Future<void> preloadImage(String url) async {
    await _imageCacheManager.downloadFile(url);
  }

  Future<void> preloadAudio(String url) async {
    await _audioCacheManager.downloadFile(url);
  }

  Stream<FileResponse> getImageFile(String url) {
    return _imageCacheManager.getFileStream(url);
  }

  Stream<FileResponse> getAudioFile(String url) {
    return _audioCacheManager.getFileStream(url);
  }

  Future<void> clearImageCache() async {
    await _imageCacheManager.emptyCache();
  }

  Future<void> clearAudioCache() async {
    await _audioCacheManager.emptyCache();
  }

  Future<void> clearAllCache() async {
    await clearImageCache();
    await clearAudioCache();
  }

  Future<int> getImageCacheSize() async {
    final cacheDir = await getTemporaryDirectory();
    final imageCacheDir = Directory(path.join(cacheDir.path, 'story_images'));
    
    if (!await imageCacheDir.exists()) return 0;
    
    int totalSize = 0;
    await for (final file in imageCacheDir.list(recursive: true)) {
      if (file is File) {
        totalSize += await file.length();
      }
    }
    return totalSize;
  }

  Future<int> getAudioCacheSize() async {
    final cacheDir = await getTemporaryDirectory();
    final audioCacheDir = Directory(path.join(cacheDir.path, 'story_audio'));
    
    if (!await audioCacheDir.exists()) return 0;
    
    int totalSize = 0;
    await for (final file in audioCacheDir.list(recursive: true)) {
      if (file is File) {
        totalSize += await file.length();
      }
    }
    return totalSize;
  }
}
```

### 6. Story Rendering Components

#### `lib/features/story/widgets/scene_widget.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:audioplayers/audioplayers.dart';
import '../../../core/models/story.dart';
import '../../../core/cache/media_cache.dart';

class SceneWidget extends StatefulWidget {
  final Scene scene;
  final bool autoPlayAudio;
  final VoidCallback? onImageTap;

  const SceneWidget({
    Key? key,
    required this.scene,
    this.autoPlayAudio = false,
    this.onImageTap,
  }) : super(key: key);

  @override
  State<SceneWidget> createState() => _SceneWidgetState();
}

class _SceneWidgetState extends State<SceneWidget>
    with AutomaticKeepAliveClientMixin {
  late final AudioPlayer _audioPlayer;
  bool _isPlaying = false;
  bool _isLoading = false;
  Duration _duration = Duration.zero;
  Duration _position = Duration.zero;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    _audioPlayer = AudioPlayer();
    _setupAudioPlayer();
    
    if (widget.autoPlayAudio && widget.scene.audioUrl != null) {
      _playAudio();
    }
  }

  void _setupAudioPlayer() {
    _audioPlayer.onDurationChanged.listen((duration) {
      setState(() => _duration = duration);
    });

    _audioPlayer.onPositionChanged.listen((position) {
      setState(() => _position = position);
    });

    _audioPlayer.onPlayerStateChanged.listen((state) {
      setState(() {
        _isPlaying = state == PlayerState.playing;
        _isLoading = state == PlayerState.playing && _position == Duration.zero;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    
    return Card(
      margin: const EdgeInsets.all(16),
      elevation: 8,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (widget.scene.imageUrl != null) _buildImageSection(),
          _buildContentSection(),
          if (widget.scene.audioUrl != null) _buildAudioSection(),
        ],
      ),
    );
  }

  Widget _buildImageSection() {
    return ClipRRect(
      borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      child: GestureDetector(
        onTap: widget.onImageTap,
        child: Hero(
          tag: 'scene_image_${widget.scene.sceneId}',
          child: CachedNetworkImage(
            imageUrl: widget.scene.imageUrl!,
            cacheManager: MediaCacheManager()._imageCacheManager,
            width: double.infinity,
            height: 250,
            fit: BoxFit.cover,
            placeholder: (context, url) => Container(
              height: 250,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Colors.grey[300]!,
                    Colors.grey[100]!,
                  ],
                ),
              ),
              child: const Center(
                child: CircularProgressIndicator(),
              ),
            ),
            errorWidget: (context, url, error) => Container(
              height: 250,
              color: Colors.grey[200],
              child: const Center(
                child: Icon(
                  Icons.error_outline,
                  size: 48,
                  color: Colors.grey,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildContentSection() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            widget.scene.title,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).primaryColor,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            widget.scene.text,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              height: 1.6,
              color: Colors.grey[800],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAudioSection() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: const BorderRadius.vertical(bottom: Radius.circular(16)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              IconButton(
                onPressed: _isLoading ? null : _toggleAudio,
                icon: _isLoading
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Icon(_isPlaying ? Icons.pause : Icons.play_arrow),
                iconSize: 32,
                color: Theme.of(context).primaryColor,
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SliderTheme(
                      data: SliderTheme.of(context).copyWith(
                        thumbShape: const RoundSliderThumbShape(
                          enabledThumbRadius: 6,
                        ),
                        trackHeight: 4,
                      ),
                      child: Slider(
                        value: _duration.inMilliseconds > 0
                            ? _position.inMilliseconds / _duration.inMilliseconds
                            : 0.0,
                        onChanged: (value) {
                          final position = Duration(
                            milliseconds: (value * _duration.inMilliseconds).round(),
                          );
                          _audioPlayer.seek(position);
                        },
                      ),
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          _formatDuration(_position),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        Text(
                          _formatDuration(_duration),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));
    return '$minutes:$seconds';
  }

  Future<void> _toggleAudio() async {
    if (_isPlaying) {
      await _audioPlayer.pause();
    } else {
      await _playAudio();
    }
  }

  Future<void> _playAudio() async {
    try {
      setState(() => _isLoading = true);
      
      // Get cached audio file
      final audioFile = await MediaCacheManager().downloadAndCacheAudio(
        widget.scene.audioUrl!,
      );
      
      await _audioPlayer.play(DeviceFileSource(audioFile.path));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to play audio: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }
}
```

This implementation guide provides a comprehensive foundation for building the Flutter app with all the required features including conversation handling, status polling, media caching, and story rendering. The code follows Flutter best practices and includes proper error handling, state management, and performance optimizations.