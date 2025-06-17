import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime

from app.database.supabase_client import StoryRepository, StorageService
from app.models.story_types import StoryRequest, StoryStatus, Scene, StoryDetail
from app.services.ai_service import AIService
from app.services.story_prompt_service import StoryPromptService
from app.services.story_generator import generate_story_async, process_single_scene, generate_and_store_media, complete_story, handle_story_error

# Mock data for testing
TEST_STORY_ID = str(uuid4())
TEST_USER_ID = str(uuid4())
TEST_PROMPT = "A magical adventure with a brave knight and a wise dragon."

MOCK_STRUCTURED_STORY_METADATA = {
    "child_profile": {"name": "Leo", "age": 5, "gender": "male"},
    "side_character": {"exists": True, "description": "a wise old dragon"},
    "story_meta": {"value_to_teach": "bravery", "setting_description": "a fantastical kingdom", "scene_count": 3, "tone": "adventurous", "story_title": "Leo and the Dragon"},
    "scenes": [
        {"scene_number": 1, "text": "Leo meets the wise dragon in a shimmering cave."},
        {"scene_number": 2, "text": "They fly over the enchanted forest."},
        {"scene_number": 3, "text": "Leo and the dragon save the kingdom."}
    ]
}

MOCK_VISUAL_PROFILE = {
    "character_prompt": "a small boy with bright eyes and a blue tunic",
    "side_character_prompt": "a large, green dragon with shimmering scales"
}

MOCK_BASE_STYLE = "a vibrant, fantastical art style, similar to Studio Ghibli"

MOCK_SCENE_MOMENT_PROMPT = "Leo bravely approaches the dragon"
MOCK_IMAGE_URL = "http://example.com/image.png"
MOCK_AUDIO_URL = "http://example.com/audio.mp3"

@pytest.fixture
def mock_db_client():
    mock = AsyncMock(spec=StoryRepository)
    mock.get_story.return_value = {
        "story_id": TEST_STORY_ID,
        "title": "Original Title",
        "prompt": TEST_PROMPT,
        "status": StoryStatus.PENDING,
        "user_id": TEST_USER_ID,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "story_metadata": None
    }
    mock.update_story.return_value = None  # Mock update to do nothing for simplicity
    mock.update_story_status.return_value = True
    mock.create_scene.return_value = MagicMock(spec=dict)
    return mock

@pytest.fixture
def mock_storage_service():
    mock = MagicMock(spec=StorageService)
    mock.upload_image.return_value = MOCK_IMAGE_URL
    mock.upload_audio.return_value = MOCK_AUDIO_URL
    return mock

@pytest.fixture
def mock_ai_service():
    mock = AsyncMock(spec=AIService)
    mock.generate_image.return_value = b"mock_image_bytes"
    mock.generate_audio.return_value = b"mock_audio_bytes"
    return mock

@pytest.fixture
def mock_story_prompt_service():
    mock = AsyncMock(spec=StoryPromptService)
    mock.generate_structured_story.return_value = MOCK_STRUCTURED_STORY_METADATA
    mock.generate_visual_profile.return_value = MOCK_VISUAL_PROFILE
    mock.generate_base_style.return_value = MOCK_BASE_STYLE
    mock.generate_scene_moment.return_value = MOCK_SCENE_MOMENT_PROMPT
    return mock

@pytest.mark.asyncio
async def test_generate_story_async_success(
    mock_db_client, 
    mock_storage_service, 
    mock_ai_service, 
    mock_story_prompt_service
):
    with (
        patch('app.database.supabase_client.StoryRepository', return_value=mock_db_client),
        patch('app.database.supabase_client.StorageService', return_value=mock_storage_service),
        patch('app.services.ai_service.AIService', return_value=mock_ai_service),
        patch('app.services.story_prompt_service.StoryPromptService', return_value=mock_story_prompt_service)
    ):
        request = StoryRequest(title="Test Story", prompt=TEST_PROMPT, user_id=UUID(TEST_USER_ID))
        result = await generate_story_async(TEST_STORY_ID, request, TEST_USER_ID)

        assert result["status"] == StoryStatus.COMPLETED
        assert result["story_id"] == TEST_STORY_ID
        assert result["title"] == MOCK_STRUCTURED_STORY_METADATA["story_meta"]["story_title"]
        assert len(result["scenes"]) == len(MOCK_STRUCTURED_STORY_METADATA["scenes"])

        mock_db_client.get_story.assert_called_once_with(TEST_STORY_ID)
        mock_story_prompt_service.generate_structured_story.assert_called_once_with(TEST_PROMPT)
        mock_db_client.update_story.assert_any_call(TEST_STORY_ID, {"story_metadata": MOCK_STRUCTURED_STORY_METADATA}, user_id=UUID(TEST_USER_ID))
        mock_db_client.update_story_status.assert_any_call(TEST_STORY_ID, StoryStatus.PROCESSING, user_id=UUID(TEST_USER_ID))
        mock_story_prompt_service.generate_visual_profile.assert_called_once_with(
            MOCK_STRUCTURED_STORY_METADATA["child_profile"],
            MOCK_STRUCTURED_STORY_METADATA["side_character"]
        )
        mock_story_prompt_service.generate_base_style.assert_called_once_with(
            MOCK_STRUCTURED_STORY_METADATA["story_meta"]["setting_description"],
            MOCK_STRUCTURED_STORY_METADATA["story_meta"]["tone"]
        )
        # Check scene processing loop
        assert mock_story_prompt_service.generate_scene_moment.call_count == len(MOCK_STRUCTURED_STORY_METADATA["scenes"])
        assert mock_ai_service.generate_image.call_count == len(MOCK_STRUCTURED_STORY_METADATA["scenes"])
        assert mock_storage_service.upload_image.call_count == len(MOCK_STRUCTURED_STORY_METADATA["scenes"])
        assert mock_ai_service.generate_audio.call_count == len(MOCK_STRUCTURED_STORY_METADATA["scenes"])
        assert mock_storage_service.upload_audio.call_count == len(MOCK_STRUCTURED_STORY_METADATA["scenes"])
        assert mock_db_client.create_scene.call_count == len(MOCK_STRUCTURED_STORY_METADATA["scenes"])
        
        # Verify update to COMPLETED status
        mock_db_client.update_story_status.assert_called_with(TEST_STORY_ID, StoryStatus.COMPLETED)

@pytest.mark.asyncio
async def test_generate_story_async_story_not_found(mock_db_client, mock_story_prompt_service):
    mock_db_client.get_story.return_value = None
    request = StoryRequest(title="Test Story", prompt=TEST_PROMPT, user_id=UUID(TEST_USER_ID))
    
    with (
        patch('app.database.supabase_client.StoryRepository', return_value=mock_db_client),
        patch('app.services.story_prompt_service.StoryPromptService', return_value=mock_story_prompt_service)
    ):
        result = await generate_story_async(TEST_STORY_ID, request, TEST_USER_ID)

        assert result["status"] == StoryStatus.FAILED
        assert "Story not found" in result["error"]
        mock_db_client.update_story_status.assert_called_once_with(TEST_STORY_ID, StoryStatus.FAILED)

@pytest.mark.asyncio
async def test_generate_story_async_llm_failure(mock_db_client, mock_story_prompt_service):
    mock_story_prompt_service.generate_structured_story.side_effect = Exception("LLM Error")
    request = StoryRequest(title="Test Story", prompt=TEST_PROMPT, user_id=UUID(TEST_USER_ID))
    
    with (
        patch('app.database.supabase_client.StoryRepository', return_value=mock_db_client),
        patch('app.services.story_prompt_service.StoryPromptService', return_value=mock_story_prompt_service)
    ):
        result = await generate_story_async(TEST_STORY_ID, request, TEST_USER_ID)

        assert result["status"] == StoryStatus.FAILED
        assert "LLM Error" in result["error"]
        mock_db_client.update_story_status.assert_called_once_with(TEST_STORY_ID, StoryStatus.FAILED)

@pytest.mark.asyncio
async def test_generate_story_async_image_generation_failure(
    mock_db_client, 
    mock_storage_service, 
    mock_ai_service, 
    mock_story_prompt_service
):
    mock_ai_service.generate_image.side_effect = Exception("Image Gen Error")
    request = StoryRequest(title="Test Story", prompt=TEST_PROMPT, user_id=UUID(TEST_USER_ID))

    with (
        patch('app.database.supabase_client.StoryRepository', return_value=mock_db_client),
        patch('app.database.supabase_client.StorageService', return_value=mock_storage_service),
        patch('app.services.ai_service.AIService', return_value=mock_ai_service),
        patch('app.services.story_prompt_service.StoryPromptService', return_value=mock_story_prompt_service)
    ):
        result = await generate_story_async(TEST_STORY_ID, request, TEST_USER_ID)

        assert result["status"] == StoryStatus.FAILED
        assert "Image Gen Error" in result["error"]
        mock_db_client.update_story_status.assert_called_once_with(TEST_STORY_ID, StoryStatus.FAILED)

@pytest.mark.asyncio
async def test_process_single_scene_success(mock_db_client, mock_storage_service, mock_ai_service):
    scene = Scene(
        scene_id=uuid4(), 
        title="Test Scene", 
        text="Some scene text.", 
        image_prompt="prompt", 
        image_url=None, 
        audio_url=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    await process_single_scene(mock_db_client, mock_storage_service, mock_ai_service, TEST_STORY_ID, 0, scene)

    mock_ai_service.generate_image.assert_called_once_with(scene.image_prompt)
    mock_storage_service.upload_image.assert_called_once_with(TEST_STORY_ID, 0, b"mock_image_bytes")
    mock_ai_service.generate_audio.assert_called_once_with(scene.text)
    mock_storage_service.upload_audio.assert_called_once_with(TEST_STORY_ID, 0, b"mock_audio_bytes")
    mock_db_client.create_scene.assert_called_once_with(
        story_id=TEST_STORY_ID,
        sequence=0,
        title=scene.title,
        text=scene.text,
        image_prompt=scene.image_prompt,
        image_url=MOCK_IMAGE_URL,
        audio_url=MOCK_AUDIO_URL
    )

@pytest.mark.asyncio
async def test_generate_and_store_media_success(mock_storage_service, mock_ai_service):
    scene = Scene(
        scene_id=uuid4(), 
        title="Test Scene", 
        text="Some scene text.", 
        image_prompt="prompt", 
        image_url=None, 
        audio_url=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    await generate_and_store_media(mock_storage_service, mock_ai_service, TEST_STORY_ID, 0, scene)

    assert scene.image_url == MOCK_IMAGE_URL
    assert scene.audio_url == MOCK_AUDIO_URL
    mock_ai_service.generate_image.assert_called_once_with(scene.image_prompt)
    mock_storage_service.upload_image.assert_called_once_with(TEST_STORY_ID, 0, b"mock_image_bytes")
    mock_ai_service.generate_audio.assert_called_once_with(scene.text)
    mock_storage_service.upload_audio.assert_called_once_with(TEST_STORY_ID, 0, b"mock_audio_bytes")

@pytest.mark.asyncio
async def test_complete_story(mock_db_client):
    story_data = {
        "story_id": TEST_STORY_ID,
        "title": "Initial Title",
        "status": StoryStatus.PROCESSING,
        "user_id": TEST_USER_ID,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    scene = Scene(
        scene_id=uuid4(), 
        title="Completed Scene", 
        text="Completed text.", 
        image_prompt="Completed prompt.", 
        image_url=MOCK_IMAGE_URL, 
        audio_url=MOCK_AUDIO_URL,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    scenes = [scene]

    result = await complete_story(mock_db_client, story_data, scenes)

    mock_db_client.update_story_status.assert_called_once_with(TEST_STORY_ID, StoryStatus.COMPLETED)
    assert result["status"] == StoryStatus.COMPLETED
    assert result["scenes"][0]["image_url"] == MOCK_IMAGE_URL
    assert result["scenes"][0]["audio_url"] == MOCK_AUDIO_URL

@pytest.mark.asyncio
async def test_handle_story_error(mock_db_client):
    error_message = "Something went wrong"
    mock_db_client.get_story.return_value = {
        "story_id": TEST_STORY_ID,
        "title": "Errored Story",
        "status": StoryStatus.PENDING,
        "user_id": TEST_USER_ID,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    result = await handle_story_error(mock_db_client, TEST_STORY_ID, Exception(error_message))

    mock_db_client.update_story_status.assert_called_once_with(TEST_STORY_ID, StoryStatus.FAILED)
    assert result["status"] == StoryStatus.FAILED
    assert result["error"] == error_message 