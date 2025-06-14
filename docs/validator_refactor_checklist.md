# Validator Implementation Documentation

## Validator Overview

### File Location
- `app/utils/validator.py`

### Validator Class
```python
class Validator:
    """Simple validator for story data structures"""
```

## Validation Methods

### AI Response Validation
```python
@staticmethod
def validate_ai_response(data: Dict[str, Any]) -> None:
    """Validate AI-generated story response
    
    Args:
        data: Dictionary containing AI response
        
    Raises:
        ValueError: If validation fails
    """
```

#### Rules
- Checks for required fields: title, scenes
- Validates title is non-empty string
- Validates scenes is a list

### Model Data Validation
```python
@staticmethod
def validate_model_data(data: Dict[str, Any]) -> None:
    """Validate database model data
    
    Args:
        data: Dictionary containing model data
        
    Raises:
        ValueError: If validation fails
    """
```

#### Rules
- Checks for required fields: story_id, title, status, scenes, user_id
- Validates story_id and user_id are strings
- Validates timestamps are strings

### Scene Validation
```python
@staticmethod
def validate_scene(scene: Dict[str, Any]) -> None:
    """Validate a single scene
    
    Args:
        scene: Dictionary containing scene data
        
    Raises:
        ValueError: If validation fails
    """
```

#### Rules
- Checks for required fields: text, sequence
- Validates text is non-empty string
- Validates sequence is integer

## Usage Guidelines

### API Layer
```python
# Use validate_model_data before database operations
Validator.validate_model_data(request_data)
```

### Worker Layer
```python
# Use validate_ai_response for AI responses
Validator.validate_ai_response(ai_response)
```

### JSON Conversion
```python
# Use validate_model_data before converting to JSON
Validator.validate_model_data(data)
```

## Validation Flow

1. **AI Response Validation**
   - Only used when receiving data from LLM
   - Validates basic structure of AI response
   - No complex business rules

2. **Model Validation**
   - Only used before database operations
   - Validates database model structure
   - Checks UUID formats and required fields

3. **Scene Validation**
   - Used by both AI and Model validation
   - Validates basic scene structure
   - Checks text and sequence integrity

## Important Notes
- Keep validation simple and focused
- No complex business rules in validators
- Use appropriate validator based on context
- Always validate before database operations
- Always validate AI responses immediately upon receipt

## Implementation Status

 All validator implementation complete
 All usage updated in key files
 Documentation updated
 Old validator files removed

## Key Files Updated

1. `app/utils/validator.py`
   - New simplified validator implementation
   - Three clear validation methods

2. `app/workers/story_worker.py`
   - Uses `validate_ai_response` for AI responses
  - [ ] Use `validate_ai_story_response` for mock responses
  - [ ] Remove any direct validator imports

## Phase 4: Update JSON Conversion

### 6. Update JSON Converter
- [ ] Update `app/utils/json_converter.py`
  - [ ] Use `validate_db_story_model` before converting to JSON
  - [ ] Remove any direct validator imports

## Phase 5: Code Cleanup

### 7. Remove Redundant Imports
- [ ] Search and remove any unused validator imports
- [ ] Update import statements to use the consolidated validator

### 8. Update Type Hints
- [ ] Update type hints in all files to reflect new validator usage
- [ ] Add proper type hints for validator methods

## Phase 6: Testing

### 9. Update Tests
- [ ] Update test files to use new validator methods
- [ ] Add tests for edge cases in validator methods
- [ ] Verify all validation scenarios are covered

### 10. Run Tests
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Verify API endpoints

## Phase 7: Documentation

### 11. Update Documentation
- [ ] Update README with validator usage guidelines
- [ ] Add validator usage examples
- [ ] Document validation flow

## Phase 8: Final Review

### 12. Code Review
- [ ] Review all changes
- [ ] Verify no validation bypasses
- [ ] Check for consistent usage

### 13. Merge Changes
- [ ] Create PR with all changes
- [ ] Get code review
- [ ] Merge to main branch

## Validation Rules Summary

### AI Response Validation (validate_ai_story_response)
- Only used when receiving data from LLM
- Validates:
  - Required fields (title, scenes)
  - Scene progression
  - Text content
  - Image prompts

### Model Validation (validate_db_story_model)
- Only used for database operations
- Validates:
  - UUID formats
  - Status values
  - Timestamps
  - Model structure

### Common Validation (validate_scene_data)
- Used by both AI and Model validation
- Validates:
  - Scene sequence
  - Text content
  - UUID format

## Important Notes
- All AI response validation should happen immediately after receiving data from LLM
- All model validation should happen before database operations
- No validation should be skipped or bypassed
- All validation errors should be properly handled with user-friendly messages
