from typing import Dict, Any

# not yet implemented in any class
def validate_story_data(story_data: Dict[str, Any]) -> None:
    """
    Validate the structure of the story data.

    Args:
        story_data: The story data dictionary to validate.

    Raises:
        ValueError: If the story data is not in the expected format.
    """
    if not isinstance(story_data, dict):
        raise ValueError("Story data must be a dictionary")

    if "title" not in story_data:
        raise ValueError("Story data must contain a title")

    if "scenes" not in story_data:
        raise ValueError("Story data must contain scenes array")

    if not isinstance(story_data["scenes"], list):
        raise ValueError("Scenes must be a list")

    for scene in story_data["scenes"]:
        if not isinstance(scene, dict):
            raise ValueError("Each scene must be a dictionary")
        if "text" not in scene:
            raise ValueError("Each scene must contain text")
        if "image_prompt" not in scene:
            raise ValueError("Each scene must contain image_prompt")
