# StoryMimi Backend Architecture Analysis

## Overview

This document provides a comprehensive analysis of the StoryMimi backend architecture based on code examination. The application follows a layered architecture with clear separation of concerns between data models, repositories, services, and API endpoints.

## Core Configuration

### Configuration Management
- `config.py` manages:
  - Environment variable loading with Pydantic Settings
  - Supabase database configuration
  - Redis connection settings
  - AI Service integrations (OpenRouter, Together AI)
  - Application settings and debug flags
  - Dynamic settings reloading capability

## AI Service Integration

### AI Service Layer
- `ai_service.py` handles:
  - Integration with OpenRouter API for text generation
  - Integration with Together AI for model inference
  - Integration with ElevenLabs for audio generation
  - API key management and rate limiting
  - Error handling for AI service failures

### Mock AI Service
- `mock_ai_service.py` provides:
  - Testable implementation of AI service
  - Configurable delay simulation
  - Static data responses for testing
  - Mock data directory management
  - Async context management

## Data Models

### Story-related Models
- `story_types.py` defines the core data structures:
  - `StoryStatus`: Enum-like class with constants for story states (pending, processing, completed, failed)
  - `Scene`: Represents a single scene in a story with text, image prompt, and sequence
  - `StoryRequest`: Input model for story creation requests
  - `StoryResponse`: Output model for story creation responses
  - `StoryData`: Model for AI-generated story content
  - `StoryDetail`: Complete story model with all details including scenes

### User-related Models
- `user.py` defines:
  - `User`: Core user model with ID, email, username, and timestamps
  - `UserCreate`: Input model for user creation
  - `UserResponse`: Output model for user data
  - `UserStoriesResponse`: Model for returning a user's stories

## Database Layer

The application uses Supabase as its database and storage solution, with a well-structured repository pattern:

### Base Client
- `base_client.py` provides:
  - Common initialization for Supabase client
  - Logging utilities for database operations
  - Connection pool management
  - Error handling utilities

### Story Repository
- `stories_db_client.py` implements:
  - CRUD operations for stories and scenes
  - Search and filtering capabilities
  - Counting and pagination functions
  - Error handling with detailed logging
  - Transaction management

### Storage Repository
- `storage_db_client.py` handles:
  - File upload and download operations
  - Bucket management
  - File metadata storage
  - Content type handling
  - Error handling for storage operations

### Error Handling
- `exceptions.py` defines a comprehensive hierarchy of exceptions:
  - Base `SupabaseError` class
  - Specialized errors for authentication, API, storage operations
  - Classification of errors as retryable or non-retryable
  - Custom error messages for debugging

## Worker Layer

### Story Generation Worker
- `story_worker.py` implements:
  - Async story generation pipeline
  - AI service integration
  - Story extraction and validation
  - Storage operations
  - Error handling and retries
  - Task status updates
  - Logging with context information

## Service Layer

### Story Service
- `story_service.py` orchestrates:
  - Story creation and dispatching to Celery
  - Story retrieval, searching, and deletion
  - User story management
  - Status updates and progress tracking

### Utilities

#### Validation
- `validator.py` provides:
  - Validation for AI responses
  - Model data validation
  - Scene validation with detailed error messages
  - Type checking and format validation

#### JSON Conversion
- `json_converter.py` handles:
  - Conversion between JSON and Python objects
  - Specialized converters for different model types
  - Error handling for parsing failures
  - Data sanitization

## API Layer

### Story Endpoints
- `stories.py` exposes:
  - Story creation, retrieval, and deletion
  - Status updates and searching
  - Recent stories listing
  - Progress tracking

### User Endpoints
- `users.py` exposes:
  - User creation and retrieval
  - User story listing
  - User information updates
  - Profile management

## Key Architectural Patterns

1. **Repository Pattern**: Clean separation of data access logic
2. **Service Layer**: Business logic encapsulation
3. **Dependency Injection**: Services injected into API routes
4. **Async/Await**: Asynchronous processing throughout
5. **Error Handling**: Comprehensive exception hierarchy
6. **Logging**: Detailed operation logging with timing information
7. **Validation**: Input validation at multiple levels
8. **Worker Pattern**: Background task processing with Celery
9. **Configuration Management**: Dynamic settings with environment variables
10. **Mocking**: Testable implementations for external services

## Notable Implementation Details

### Error Handling
The application implements a sophisticated error handling system with a hierarchy of exception types. This allows for precise error classification and appropriate handling strategies, including retry logic for transient errors.

### Logging
Extensive logging is implemented throughout the codebase, with detailed operation tracking, timing information, and error reporting. This facilitates debugging and performance monitoring.

### Asynchronous Processing
The application leverages Python's async/await syntax for non-blocking I/O operations, improving scalability and responsiveness. Long-running tasks like story generation are offloaded to Celery for background processing.

### Data Validation
Multi-layered validation ensures data integrity at various points in the application flow, from API input to database operations.

### AI Integration
The application uses multiple AI services (OpenRouter, Together AI, ElevenLabs) with fallback mechanisms and mock implementations for testing.

## Conclusion

The StoryMimi backend demonstrates good software engineering practices with clear separation of concerns, comprehensive error handling, and detailed logging throughout the codebase. The architecture is well-structured for maintainability and scalability, with special attention to AI service integration and testing capabilities.

## Service Layer

### Story Service
- `story_service.py` orchestrates:
  - Story creation and dispatching to Celery for async processing
  - Story retrieval, searching, and deletion
  - User story management

### Utilities

#### Validation
- `validator.py` provides:
  - Validation for AI responses
  - Model data validation
  - Scene validation with detailed error messages

#### JSON Conversion
- `json_converter.py` handles:
  - Conversion between JSON and Python objects
  - Specialized converters for different model types
  - Error handling for parsing failures

## API Layer

### Story Endpoints
- `stories.py` exposes:
  - Story creation, retrieval, and deletion
  - Status updates and searching
  - Recent stories listing

### User Endpoints
- `users.py` exposes:
  - User creation and retrieval
  - User story listing
  - User information updates

## Key Architectural Patterns

1. **Repository Pattern**: Clean separation of data access logic
2. **Service Layer**: Business logic encapsulation
3. **Dependency Injection**: Services injected into API routes
4. **Async/Await**: Asynchronous processing throughout
5. **Error Handling**: Comprehensive exception hierarchy
6. **Logging**: Detailed operation logging with timing information
7. **Validation**: Input validation at multiple levels

## Notable Implementation Details

### Error Handling
The application implements a sophisticated error handling system with a hierarchy of exception types. This allows for precise error classification and appropriate handling strategies, including retry logic for transient errors.

### Logging
Extensive logging is implemented throughout the codebase, with detailed operation tracking, timing information, and error reporting. This facilitates debugging and performance monitoring.

### Asynchronous Processing
The application leverages Python's async/await syntax for non-blocking I/O operations, improving scalability and responsiveness. Long-running tasks like story generation are offloaded to Celery for background processing.

### Data Validation
Multi-layered validation ensures data integrity at various points in the application flow, from API input to database operations.

## Conclusion

The StoryMimi backend demonstrates good software engineering practices with clear separation of concerns, comprehensive error handling, and detailed logging throughout the codebase. The architecture is well-structured for maintainability and scalability.