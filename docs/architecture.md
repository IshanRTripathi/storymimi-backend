# StoryMimi Backend Architecture Documentation

## 1. API Contracts (Swagger/OpenAPI)

### Stories API Endpoints

#### POST /stories/
- **Description**: Create a new story based on the provided prompt
- **Request Body**: StoryRequest
- **Response**: StoryResponse (202 Accepted)
- **Error Response**: StoryResponse with error status

#### GET /stories/{story_id}
- **Description**: Retrieve a story by ID
- **Response**: StoryDetail

#### PATCH /stories/{story_id}
- **Description**: Update story status or details
- **Response**: StoryDetail

### Models

```python
# Request Models
class StoryRequest(BaseModel):
    title: str
    prompt: str
    style: Optional[str]
    num_scenes: int
    user_id: Optional[UUID]

# Response Models
class StoryResponse(BaseModel):
    story_id: UUID
    status: StoryStatus
    title: str
    created_at: datetime
    error: Optional[str]

# Detailed Response
class StoryDetail(BaseModel):
    story_id: UUID
    title: str
    status: StoryStatus
    user_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]
    scenes: List[Scene]

# Scene Model
class Scene(BaseModel):
    scene_id: UUID
    story_id: UUID
    sequence: int
    text: str
    image_url: Optional[str]
    audio_url: Optional[str]
    created_at: datetime
```

## 2. Backend Implementation

### Service Layer

#### StoryService
- Manages story lifecycle
- Coordinates with AI services
- Handles database operations
- Implements business logic

#### AIService
- Interfaces with AI APIs (OpenRouter, Together.ai, ElevenLabs)
- Handles text generation
- Handles image generation
- Handles audio generation

#### StoryGenerator
- Orchestrates story generation process
- Manages scene extraction
- Coordinates media generation
- Handles error handling

### Worker Layer

#### Celery Tasks
- Asynchronous story generation
- Task queue management
- Retry mechanisms
- Status updates

## 3. Database Schema Design

### Supabase Tables

#### stories
- story_id (UUID)
- title (text)
- status (enum: PENDING, PROCESSING, COMPLETE, FAILED)
- user_id (UUID, nullable)
- created_at (timestamp)
- updated_at (timestamp, nullable)

#### scenes
- scene_id (UUID)
- story_id (UUID, foreign key)
- sequence (integer)
- text (text)
- image_url (text, nullable)
- audio_url (text, nullable)
- created_at (timestamp)

### Storage Buckets
- story-images
  - Stores scene images
  - Public access
  - Versioned

- story-audio
  - Stores scene audio
  - Public access
  - Versioned

## 4. Syncing Documentation and Implementation

### Recommended Tools and Practices

1. **OpenAPI/Swagger Generation**
   - Use FastAPI's automatic OpenAPI generation
   - Keep API documentation in sync with code
   - Generate client SDKs from OpenAPI spec

2. **Database Schema Validation**
   - Use Alembic for migrations
   - Validate models against database schema
   - Generate database diagrams from schema

3. **Model Validation**
   - Use Pydantic for request/response validation
   - Keep models in sync with database schema
   - Use shared models across services

### Best Practices

1. **Documentation Updates**
   - Update API docs with each endpoint change
   - Keep model definitions in sync
   - Document database schema changes

2. **Testing**
   - Write integration tests for API endpoints
   - Test database operations
   - Validate JSON schemas

3. **Version Control**
   - Version API contracts
   - Track database schema changes
   - Maintain changelog

4. **Continuous Integration**
   - Run validation checks in CI
   - Generate documentation automatically
   - Test API compatibility

### Common Pitfalls to Avoid

1. **Documentation Drift**
   - Don't let documentation fall out of sync with code
   - Regularly review and update
   - Use automated tools to detect discrepancies

2. **Schema Inconsistency**
   - Avoid divergent database schemas
   - Use proper migration tools
   - Document schema changes

3. **Model Mismatch**
   - Keep Pydantic models in sync with database
   - Validate model changes
   - Test model serialization/deserialization

This documentation should be maintained alongside code changes to ensure consistency across the system.
