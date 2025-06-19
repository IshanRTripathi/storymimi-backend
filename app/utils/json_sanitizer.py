import json
import re
import logging
from typing import Union, Optional, Dict, Any, Callable, Awaitable
from functools import wraps
from time import sleep
from json_repair import repair_json

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> str:
    """
    Extract the first JSON object or array from the text, removing code block fences and extra whitespace.
    """
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text.strip())
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def auto_correct_list_fields(data: Any, schema: Any, path: str = "") -> Any:
    """
    Recursively auto-corrects fields that are expected to be lists but are strings.
    """
    if isinstance(schema, dict) and isinstance(data, dict):
        corrected = {}
        for key, expected_type in schema.items():
            if key in data:
                corrected[key] = auto_correct_list_fields(data[key], expected_type, path + f".{key}" if path else key)
        for k, v in data.items():
            if k not in corrected:
                corrected[k] = v
        return corrected
    elif isinstance(schema, list) and schema and isinstance(data, (str, dict)):
        logger.info(f"Auto-correcting field at {path}: wrapping value in list.")
        return [data]
    elif isinstance(schema, list) and schema and isinstance(data, list):
        return [auto_correct_list_fields(item, schema[0], path + "[]") for item in data]
    else:
        return data

async def robust_llm_schema_parse(
    raw_text: str,
    schema: Any,
    llm_fix_func: Callable[[str, str], Awaitable[str]],
    max_retries: int = 5
) -> Union[dict, list]:
    """
    Try to repair, parse, and validate LLM JSON, auto-correcting list fields, and if schema validation fails, ask the LLM to fix it up to max_retries times.
    """
    cleaned = extract_json_from_text(raw_text)
    try:
        data = repair_json(cleaned, return_objects=True)
        logger.info("[json-repair] Successfully repaired and parsed JSON on first attempt.")
    except Exception as e:
        logger.warning(f"[json-repair] Failed to repair/parse JSON: {e}. Escalating to LLM correction.")
        last_error = str(e)
        for attempt in range(max_retries):
            logger.info(f"[LLM JSON Correction] Attempt {attempt+1}/{max_retries}")
            fix_prompt = (
                "The following is supposed to be valid JSON, but it is not. "
                "Please return only valid JSON, fixing any formatting errors. "
                "Do NOT use markdown or code blocks. "
                f"Error: {last_error}\n\nJSON:\n{cleaned}"
            )
            fixed_json = await llm_fix_func(fix_prompt, cleaned)
            fixed_cleaned = extract_json_from_text(fixed_json)
            try:
                data = repair_json(fixed_cleaned, return_objects=True)
                logger.info(f"[json-repair] Successfully repaired JSON after LLM correction attempt {attempt+1}.")
                break
            except Exception as e:
                logger.warning(f"[json-repair] Attempt {attempt+1} failed: {e}")
                last_error = str(e)
        else:
            logger.error(f"Failed to parse LLM output as valid JSON after {max_retries} correction attempts. Last error: {last_error}")
            logger.error("Raw text:\n%s", raw_text)
            raise ValueError(f"Failed to parse LLM output as valid JSON after {max_retries} correction attempts. Last error: {last_error}")
    data = auto_correct_list_fields(data, schema)
    try:
        validate_json_structure(data, schema)
        return data
    except Exception as e:
        logger.warning(f"Schema validation failed: {e}. Attempting LLM schema correction.")
        last_error = str(e)
        for attempt in range(max_retries):
            logger.info(f"[LLM Schema Correction] Attempt {attempt+1}/{max_retries}")
            fix_prompt = (
                "The following JSON does not match the required schema. "
                "Please return only valid JSON, strictly following the schema types. "
                "If a field is a list, always return a JSON array, even if it has only one item. "
                "Do NOT use markdown or code blocks. "
                f"Error: {last_error}\n\nSchema: {schema}\n\nJSON:\n{json.dumps(data, ensure_ascii=False)}"
            )
            fixed_json = await llm_fix_func(fix_prompt, json.dumps(data, ensure_ascii=False))
            fixed_cleaned = extract_json_from_text(fixed_json)
            try:
                fixed_data = repair_json(fixed_cleaned, return_objects=True)
                validate_json_structure(fixed_data, schema)
                logger.info(f"[json-repair] Successfully repaired JSON after LLM schema correction attempt {attempt+1}.")
                return fixed_data
            except Exception as e2:
                logger.warning(f"[json-repair] Schema correction attempt {attempt+1} failed: {e2}")
                last_error = str(e2)
        logger.error(f"Failed to validate LLM output as matching schema after {max_retries} correction attempts. Last error: {last_error}")
        logger.error("Raw text:\n%s", raw_text)
        raise ValueError(f"Failed to validate LLM output as matching schema after {max_retries} correction attempts. Last error: {last_error}")

def validate_and_parse_llm_json(raw_text: str, max_retries: int = 3) -> Union[dict, list]:
    """
    Attempts to parse LLM-generated JSON, auto-correcting common issues.
    """
    errors = []
    cleaned = extract_json_from_text(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        errors.append(f"Standard JSON parse failed: {str(e)}")
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

def repair_json_with_json_repair(text: str) -> str:
    """
    Repairs JSON using the json-repair library and returns the repaired JSON string.
    
    Args:
        text: Raw JSON text from LLM
        
    Returns:
        Repaired JSON string
    """
    try:
        repaired_json = repair_json(text, return_objects=True)
        return repaired_json
    except Exception as e:
        logger.warning(f"Failed to repair JSON: {e}")
        return text

def sanitize_llm_json(raw_text: str, max_retries: int = 3) -> Union[dict, list]:
    """
    Attempts to parse LLM-generated JSON, auto-correcting common issues and using json-repair for robust repair.
    """
    errors = []
    cleaned = extract_json_from_text(raw_text)
    try:
        repaired_json = repair_json_with_json_repair(cleaned)
        return json.loads(repaired_json)
    except json.JSONDecodeError as e:
        errors.append(f"Standard JSON parse failed: {str(e)}")
    error_msg = "Failed to parse LLM output as valid JSON:\n" + "\n".join(errors)
    logger.error(error_msg)
    logger.error("Raw text:\n%s", raw_text)
    raise ValueError(error_msg) 