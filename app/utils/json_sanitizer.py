import json
import re
import logging
from typing import Union, Optional, Dict, Any
from functools import wraps
from time import sleep

try:
    import rapidjson
    HAS_RAPIDJSON = True
except ImportError:
    HAS_RAPIDJSON = False

logger = logging.getLogger(__name__)

def fix_common_json_issues(text: str) -> str:
    """
    Cleans common LLM JSON formatting issues.
    
    Args:
        text: Raw JSON text from LLM
        
    Returns:
        Cleaned JSON text
    """
    text = text.strip()

    # Remove code block fences like ```json
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.IGNORECASE)

    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Replace double-double quotes with single quote
    text = re.sub(r'""(?=\w)', '"', text)

    # Fix common LLM formatting issues
    text = re.sub(r'(?<!\\)"(?=\s*[,}])', '\\"', text)  # Escape quotes before commas/braces
    text = re.sub(r'\n\s*(["\'])[^\n]*?["\']:\s*(["\'])[^\n]*?["\'],?\s*\n', 
                 lambda m: m.group().replace('\n', ' '), text)  # Join multi-line string values
    
    return text

def validate_and_parse_llm_json(raw_text: str, max_retries: int = 3) -> Union[dict, list]:
    """
    Attempts to parse LLM-generated JSON, auto-correcting common issues.
    
    Args:
        raw_text: Raw JSON text from LLM
        max_retries: Maximum number of retries for parsing
        
    Returns:
        Parsed JSON data
        
    Raises:
        ValueError: If parsing fails after all attempts
    """
    errors = []

    # First try raw JSON directly
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        errors.append(f"Standard JSON parse failed: {str(e)}")

    # Try after cleaning common issues
    cleaned = fix_common_json_issues(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        errors.append(f"Cleaned JSON parse failed: {str(e)}")

    # Try rapidjson fallback if available
    if HAS_RAPIDJSON:
        try:
            return rapidjson.loads(cleaned, parse_mode=rapidjson.PM_JSON5)
        except Exception as e:
            errors.append(f"RapidJSON parse failed: {str(e)}")

    error_msg = "Failed to parse LLM output as valid JSON:\n" + "\n".join(errors)
    logger.error(error_msg)
    logger.error("Raw text:\n%s", raw_text)
    raise ValueError(error_msg)

def retry_on_json_error(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry a function on JSON parsing errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except ValueError as e:
                    if "JSON" in str(e):
                        last_error = e
                        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                        if attempt < max_retries - 1:
                            sleep(delay * (attempt + 1))  # Exponential backoff
                            continue
                    raise e
            raise last_error
        return wrapper
    return decorator

def validate_json_structure(data: Dict[str, Any], required_structure: Dict[str, Any], path: str = "") -> None:
    """
    Validates that a JSON object matches a required structure.
    
    Args:
        data: JSON data to validate
        required_structure: Dictionary describing required structure
        path: Current path in the JSON structure (for error messages)
        
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValueError(f"Expected dictionary at {path or 'root'}, got {type(data)}")

    for key, expected_type in required_structure.items():
        current_path = f"{path}.{key}" if path else key
        
        if key not in data:
            raise ValueError(f"Missing required field: {current_path}")
            
        value = data[key]
        
        if isinstance(expected_type, dict):
            validate_json_structure(value, expected_type, current_path)
        elif isinstance(expected_type, list):
            if not isinstance(value, list):
                raise ValueError(f"Expected list at {current_path}, got {type(value)}")
            if expected_type:  # If we have a type specification for list items
                item_type = expected_type[0]
                for i, item in enumerate(value):
                    if isinstance(item_type, dict):
                        validate_json_structure(item, item_type, f"{current_path}[{i}]")
                    elif not isinstance(item, item_type):
                        raise ValueError(f"Invalid type in list at {current_path}[{i}]: expected {item_type}, got {type(item)}")
        elif not isinstance(value, expected_type):
            raise ValueError(f"Invalid type at {current_path}: expected {expected_type}, got {type(value)}") 