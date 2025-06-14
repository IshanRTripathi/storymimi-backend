# Supabase Storage Integration Guide

This document provides comprehensive guidance on integrating Supabase Storage in the storymimi-backend application, focusing on correct async/sync patterns and best practices.

## 1. Client Initialization

### Current Implementation Issues
```python
# Incorrect initialization
def __init__(self):
    self.client = create_client(
        settings.SUPABASE_URL, 
        settings.SUPABASE_KEY,
        is_async=True  # Invalid parameter
    )
```

### Correct Implementation
```python
# Correct initialization
def __init__(self):
    self.client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )
    self.storage = self.client.storage
```

## 2. Storage Operations

### Common Issues
1. Mixing async/sync operations
2. Incorrect file upload parameters
3. Missing error handling
4. Improper bucket management

### Correct Storage Pattern
```python
class StorageService:
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.storage = self.client.storage

    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """Ensure storage bucket exists"""
        try:
            # Create bucket (idempotent operation)
            self.storage.create_bucket(bucket_name)
        except Exception as e:
            # Check if bucket already exists
            try:
                self.storage.from_(bucket_name).list()
            except:
                raise e

    def upload_image(self, story_id: str, scene_index: int, image_bytes: bytes) -> str:
        """Upload image to storage"""
        filename = f"scene_{scene_index}_{uuid.uuid4()}.png"
        bucket_name = "story-images"
        
        try:
            # Ensure bucket exists
            self._ensure_bucket_exists(bucket_name)
            
            # Upload with proper headers
            response = self.storage.from_(bucket_name).upload(
                file=image_bytes,
                path=filename,
                file_options={"Content-Type": "image/png"}
            )
            
            # Construct public URL
            public_url = f"https://{settings.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload image: {str(e)}")
            raise
```

## 3. Service Layer Integration

### Correct Service Pattern
```python
class StoryService:
    def __init__(self, db_client: StoryRepository, storage_service: StorageService):
        self.db_client = db_client
        self.storage_service = storage_service

    async def create_new_story(self, request: StoryRequest) -> Dict[str, Any]:
        # Create story record
        story = await self.db_client.create_story(
            title=request.title,
            prompt=request.prompt,
            user_id=request.user_id
        )
        
        # Generate scenes and images
        scenes = await ai_service.generate_scenes(story.title, story.prompt)
        for i, scene in enumerate(scenes):
            image_bytes = await ai_service.generate_image(scene.text)
            image_url = self.storage_service.upload_image(story.id, i, image_bytes)
            scene.image_url = image_url
        
        # Update story with scenes
        await self.db_client.update_story(story.id, scenes=scenes)
        
        return {
            "story_id": story.id,
            "title": story.title,
            "scenes": scenes,
            "created_at": story.created_at.isoformat(),
            "updated_at": story.updated_at.isoformat(),
            "user_id": story.user_id
        }
```

## 4. Key Best Practices

### Client Management
1. Initialize Supabase client without async parameters
2. Use separate clients for storage and database operations
3. Always handle client initialization errors

### Storage Operations
1. Keep storage operations synchronous
2. Use proper Content-Type headers
3. Implement bucket existence checks
4. Handle file upload errors gracefully

### Error Handling
1. Log all storage operations
2. Propagate errors with context
3. Implement retry logic for transient failures
4. Validate file types and sizes before upload

### Security Considerations
1. Use proper authentication for storage operations
2. Set appropriate bucket permissions
3. Validate URLs before use
4. Implement rate limiting

## 5. Common Pitfalls to Avoid

1. ❌ Mixing async and sync operations
   - Storage operations are synchronous
   - Database operations are async

2. ❌ Using incorrect client initialization
   - Don't use is_async=True
   - Don't mix async storage operations

3. ❌ Missing error handling
   - Always catch and log errors
   - Provide meaningful error messages

4. ❌ Improper bucket management
   - Always check bucket existence
   - Handle bucket creation failures

## 6. Troubleshooting Guide

### Common Errors and Solutions

1. `TypeError: create_client() got an unexpected keyword argument 'is_async'`
   - Solution: Remove is_async parameter
   - Use: `create_client(url, key)`

2. `Storage upload failed`
   - Check bucket permissions
   - Verify Content-Type headers
   - Check file size limits

3. `Bucket not found`
   - Implement bucket existence check
   - Handle bucket creation errors
   - Verify bucket name format

## 7. Performance Considerations

1. Batch operations when possible
2. Implement caching for frequently accessed files
3. Use async for database operations
4. Optimize image processing pipeline

## 8. Testing Recommendations

1. Test storage operations in isolation
2. Verify bucket creation and deletion
3. Test error scenarios
4. Validate URL construction
5. Check file size limits

## 9. Maintenance Checklist

1. Regularly check storage usage
2. Monitor error logs
3. Update client libraries
4. Review security settings
5. Test backup procedures
