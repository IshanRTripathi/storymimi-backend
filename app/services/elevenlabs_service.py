import aiohttp
import logging
from typing import Dict, Any, Optional
from app.core.config.settings import settings

logger = logging.getLogger(__name__)

class ElevenLabsService:
    """Service for interacting with ElevenLabs API"""
    
    def __init__(self):
        """Initialize the ElevenLabs service"""
        self.base_url = "https://api.elevenlabs.io/v1"
        self.api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
        
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
    
    async def get_conversation_transcript(self, conversation_id: str, agent_id: str) -> Optional[str]:
        """Fetch conversation transcript from ElevenLabs API
        
        Args:
            conversation_id: ElevenLabs conversation ID
            agent_id: ElevenLabs agent ID
            
        Returns:
            Conversation transcript as string or None if not available
        """
        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            return None
        
        try:
            # This is a placeholder implementation
            # You'll need to check ElevenLabs API documentation for the actual endpoint
            url = f"{self.base_url}/conversations/{conversation_id}/transcript"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            params = {
                "agent_id": agent_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        transcript = data.get("transcript", "")
                        logger.info(f"Successfully fetched transcript for conversation: {conversation_id}")
                        return transcript
                    else:
                        logger.error(f"Failed to fetch transcript: {response.status} - {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching ElevenLabs transcript: {str(e)}", exc_info=True)
            return None
    
    async def get_conversation_summary(self, conversation_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """Fetch conversation summary from ElevenLabs API
        
        Args:
            conversation_id: ElevenLabs conversation ID
            agent_id: ElevenLabs agent ID
            
        Returns:
            Conversation summary as dict or None if not available
        """
        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            return None
        
        try:
            # This is a placeholder implementation
            # You'll need to check ElevenLabs API documentation for the actual endpoint
            url = f"{self.base_url}/conversations/{conversation_id}/summary"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            params = {
                "agent_id": agent_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched summary for conversation: {conversation_id}")
                        return data
                    else:
                        logger.error(f"Failed to fetch summary: {response.status} - {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching ElevenLabs summary: {str(e)}", exc_info=True)
            return None
    
    async def get_conversation_metadata(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch conversation metadata from ElevenLabs API
        
        Args:
            conversation_id: ElevenLabs conversation ID
            
        Returns:
            Conversation metadata as dict or None if not available
        """
        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            return None
        
        try:
            # This is a placeholder implementation
            # You'll need to check ElevenLabs API documentation for the actual endpoint
            url = f"{self.base_url}/conversations/{conversation_id}"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched metadata for conversation: {conversation_id}")
                        return data
                    else:
                        logger.error(f"Failed to fetch metadata: {response.status} - {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching ElevenLabs metadata: {str(e)}", exc_info=True)
            return None 