### 1. Environment Variable Handling
- **Issue**: Environment variables were not being properly loaded from `.env` file, they are cached due to pydantic implementation

### 2. Supabase Client Initialization
- **Issue**: Incorrect handling of async operations and Supabase responses
- **Changes**:
  ```python
  # In supabase_client.py
  async def __init__(self):
      try:
          # Use count="exact" for better health check
          health_response = self.client.table("stories").select("*", count="exact").execute()
          if health_response.error:
              logger.error(f"Supabase health check failed: {health_response.error}")
              raise Exception(f"Supabase health check failed: {health_response.error}")
          
          self.storage = self.client.storage
  ```

### 3. Bucket Management
- **Issue**: Incorrect bucket creation and access handling
- **Changes**:
  ```python
  async def _ensure_bucket_exists(self, bucket_name: str):
      try:
          response = await self.storage.get_bucket(bucket_name)
          if response.error:
              logger.error(f"Error getting bucket: {response.error}")
              raise Exception(f"Error getting bucket: {response.error}")
          
          if not response.data:
              response = await self.storage.create_bucket(bucket_name)
              if response.error:
                  logger.error(f"Error creating bucket: {response.error}")
                  raise Exception(f"Error creating bucket: {response.error}")
  ```

### 4. Celery Worker Configuration
- **Issue**: Worker crashing with async operations
- **Changes**:
  ```python
  # In celery_app.py
  celery_app = Celery(
      "storymimi",
      broker=settings.REDIS_URL,
      backend=settings.REDIS_URL
  )
  
  celery_app.conf.update(
      task_serializer="json",
      accept_content=["json"],
      result_serializer="json",
      timezone="UTC",
      enable_utc=True
  )
  ```

### 5. Error Handling Improvements
- Add proper error checking for Supabase responses
- Add detailed logging for debugging
- Implement proper async/await handling


1. **Environment Variables**:
   - Always use `load_dotenv()` before accessing environment variables
   - Use Pydantic BaseSettings for type-safe configuration
   - Ensure proper error handling for missing environment variables

2. **Async Operations**:
   - Properly await all async operations
   - Handle async responses correctly
   - Use proper error checking for async operations

3. **Supabase Integration**:
   - Use `count="exact"` for health checks
   - Properly handle Supabase response objects
   - Ensure proper bucket management
   - Add proper error handling for storage operations