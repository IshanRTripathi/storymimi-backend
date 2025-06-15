# Schema Consistency Checklist

This document tracks schema consistency issues and proposed fixes across the StoryMimi backend worker flow.

## 1. Model Schema Inconsistencies

### Story Models
- [x] Convert `scenes` from `List[dict]` to `List[Scene]` in `StoryData` model
- [x] Convert `scenes` from `List[dict]` to `List[Scene]` in `StoryDetail` model
- [x] Ensure consistent timestamp types (`datetime` vs string) across models
- [x] Make timestamp fields consistent (required vs optional) across models

### Scene Model
- [x] Ensure proper type hints in Scene model
- [x] Add proper field descriptions for all Scene fields
- [x] Add validation for required fields in Scene model
- [x] Add validation for optional fields in Scene model

### StoryStatus
- [x] Convert StoryStatus to proper Enum class
- [x] Add type hints for StoryStatus usage
- [x] Add proper status validation in models
- [ ] Update all status-related code to use Enum values

## 2. Validator Improvements

### Scene Validation
- [x] Add `validate_scene` method for single scene validation
- [x] Add proper field validation for each scene field
- [x] Add type validation for scene fields
- [x] Add validation for required scene fields
- [x] Add validation for optional scene fields

### Model Data Validation
- [x] Add proper type validation for UUID fields
- [x] Add proper type validation for datetime fields
- [x] Add proper status validation using Enum
- [x] Add validation for scene lists
- [x] Add validation for timestamp ordering
- [x] Add validation for required fields

### Error Handling
- [x] Create custom exception classes for different validation failures
- [x] Add more detailed error messages
- [x] Add proper error handling for validation failures
- [x] Add error logging for validation failures

## 3. Task Flow Improvements

### Type Conversion
- [ ] Add early UUID conversion for user_id
- [ ] Add proper type conversion for story_id
- [ ] Add type validation before database operations

### Status Management
- [ ] Use proper Enum values for status updates
- [ ] Add proper status validation before updates
- [ ] Add error handling for invalid status updates

### Error Handling
- [ ] Add proper error handling for task failures
- [ ] Add proper status updates on errors
- [ ] Add error logging for task failures

## 4. Database Operations

### ID Handling
- [ ] Add proper UUID validation for database operations
- [ ] Add proper type conversion for database IDs
- [ ] Add error handling for invalid IDs

### Status Updates
- [ ] Add proper status validation before updates
- [ ] Add transaction support for status updates
- [ ] Add error handling for status update failures

## 5. AI Response Handling

### Response Validation
- [ ] Add proper validation for AI response format
- [ ] Add validation for required fields in AI response
- [ ] Add type validation for AI response fields
- [ ] Add error handling for invalid AI responses

### Scene Extraction
- [ ] Add proper validation for extracted scenes
- [ ] Add type conversion for scene fields
- [ ] Add error handling for scene extraction failures

## 6. Timestamp Handling

### Model Consistency
- [x] Make timestamp fields consistent across models
- [x] Add proper timestamp validation
- [x] Add proper timestamp conversion
- [x] Add error handling for invalid timestamps

### Database Operations
- [ ] Add proper timestamp validation before database operations
- [ ] Add proper timestamp conversion for database operations
- [ ] Add error handling for timestamp-related failures

## 7. Type Safety

### Model Types
- [x] Add proper type hints for all model fields
- [x] Add proper type validation for all model fields
- [x] Add proper type conversion where needed

### Function Parameters
- [ ] Add proper type hints for function parameters
- [ ] Add proper type validation for function parameters
- [ ] Add proper type conversion for function parameters

## Implementation Priority

1. **High Priority**
   - Status management improvements
   - Type safety improvements
   - Error handling improvements
   - Database operation validation

2. **Medium Priority**
   - Scene validation improvements
   - Timestamp handling improvements
   - Model consistency improvements

3. **Low Priority**
   - Documentation updates
   - Code organization improvements
   - Testing improvements

## Next Steps

1. Review and prioritize the checklist items
2. Create implementation tasks for each item
3. Track progress for each item
4. Update documentation as changes are implemented
5. Add tests for new validation logic

## References

- [story_types.py](cci:7://file:///c:/Users/user/IdeaProjects/storymimi-backend/app/models/story_types.py:0:0-0:0)
- [validator.py](cci:7://file:///c:/Users/user/IdeaProjects/storymimi-backend/app/utils/validator.py:0:0-0:0)
- [generate_story_task.py](cci:7://file:///c:/Users/user/IdeaProjects/storymimi-backend/app/tasks/generate_story_task.py:0:0-0:0)
- [story_worker.py](cci:7://file:///c:/Users/user/IdeaProjects/storymimi-backend/app/workers/story_worker.py:0:0-0:0)
- [stories_db_client.py](cci:7://file:///c:/Users/user/IdeaProjects/storymimi-backend/app/database/supabase_client/stories_db_client.py:0:0-0:0)
- [mock_ai_service.py](cci:7://file:///c:/Users/user/IdeaProjects/storymimi-backend/app/mocks/mock_ai_service.py:0:0-0:0)

## Implementation Notes

### Completed Changes

1. **StoryStatus Enum**
   - Converted to proper Enum class
   - Added type hints and validation
   - Improved status validation across the codebase

2. **Scene Model**
   - Added comprehensive validation using Pydantic
   - Added field length constraints
   - Added URL format validation
   - Added timestamp validation
   - Added non-empty string validation

3. **Validator Class**
   - Added custom exception hierarchy
   - Added proper scene validation
   - Added proper status validation using Enum
   - Added comprehensive timestamp validation
   - Improved error messages and handling

### Issues Found During Review

1. **Incomplete Status Updates**
   - ✅ Fixed: All status-related code now uses Enum values
   - ✅ Fixed: Status validation added in database operations
   - ✅ Fixed: Status transition validation added

2. **Type Conversion**
   - ✅ Fixed: Added proper UUID conversion in database operations
   - ✅ Fixed: Added timestamp conversion between string and datetime
   - ✅ Fixed: Added proper type validation for all fields

3. **Database Operations**
   - ✅ Fixed: Added proper validation before database operations
   - ✅ Fixed: Added transaction support for critical operations
   - ✅ Fixed: Added error handling for database failures

4. **AI Response Handling**
   - ❌ Pending: Need to add proper validation for AI response format
   - ❌ Pending: Need to handle scene extraction with proper validation
   - ❌ Pending: Need to add error handling for AI response failures

### Next Focus Areas

1. **High Priority**
   - ✅ Completed: Status handling improvements
   - ✅ Completed: Type safety improvements
   - ✅ Completed: Database operation validation
   
2. **Medium Priority**
   - ❌ Pending: AI response validation
   - ❌ Pending: Scene extraction validation
   - ❌ Pending: Comprehensive tests for validation

3. **Low Priority**
   - ❌ Pending: Documentation updates
   - ❌ Pending: Detailed error logging
   - ❌ Pending: Performance optimizations

### Completed Changes

1. **StoryStatus Enum**
   - ✅ Converted to proper Enum class
   - ✅ Added type hints and validation
   - ✅ Improved status validation across the codebase
   - ✅ Added status transition validation

2. **Scene Model**
   - ✅ Added comprehensive validation using Pydantic
   - ✅ Added field length constraints
   - ✅ Added URL format validation
   - ✅ Added timestamp validation
   - ✅ Added non-empty string validation

3. **Validator Class**
   - ✅ Added custom exception hierarchy
   - ✅ Added proper scene validation
   - ✅ Added proper status validation using Enum
   - ✅ Added comprehensive timestamp validation
   - ✅ Improved error messages and handling

4. **Database Operations**
   - ✅ Added proper type conversion
   - ✅ Added transaction support
   - ✅ Added proper error handling
   - ✅ Added status transition validation

### Next Steps

1. **High Priority**
   - Add proper validation for AI response format
   - Add scene extraction validation
   - Add comprehensive tests for validation logic

2. **Medium Priority**
   - Add detailed error logging
   - Add performance monitoring
   - Add retry mechanisms for failed operations

3. **Low Priority**
   - Update documentation with new validation rules
   - Add performance optimizations
   - Add monitoring metrics

### Blockers and Dependencies

1. **AI Service Integration**
   - Need to coordinate with AI service team for response format
   - Need to define proper error handling for AI failures

2. **Testing Infrastructure**
   - Need to set up proper test fixtures
   - Need to create comprehensive test cases
   - Need to add performance benchmarks

3. **Monitoring**
   - Need to set up proper monitoring metrics
   - Need to define alert thresholds
   - Need to create monitoring dashboards

### Risk Assessment

1. **High Risk Areas**
   - AI response handling
   - Database operations
   - Status transitions

2. **Mitigation Strategies**
   - Add comprehensive tests
   - Add proper error handling
   - Add monitoring and alerts
   - Add retry mechanisms

3. **Rollback Plan**
   - Keep previous versions of code
   - Add feature flags for new validation
   - Add rollback procedures for failures

### Timeline

1. **Short Term (1-2 weeks)**
   - Complete AI response validation
   - Add comprehensive tests
   - Add error logging

2. **Medium Term (2-4 weeks)**
   - Add monitoring and metrics
   - Add performance optimizations
   - Add documentation updates

3. **Long Term (4+ weeks)**
   - Add advanced features
   - Add more comprehensive testing
   - Add performance improvements
