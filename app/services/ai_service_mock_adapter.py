from typing import Optional, Union
import asyncio

from app.config import settings
from app.mocks.mock_ai_service import MockAIService
from app.services.ai_service import AIService

class AIServiceFactory:
    """Factory class to create the appropriate AIService implementation
    
    This class decides whether to use the real AIService or the MockAIService
    based on configuration settings.
    """
    
    @staticmethod
    async def create_service() -> Union[AIService, MockAIService]:
        """Create and return the appropriate AIService implementation
        
        Returns:
            Either a real AIService or a MockAIService based on configuration
        """
        # Check if we should use mock services
        use_mock = getattr(settings, "USE_MOCK_AI_SERVICES", False)
        
        if use_mock:
            # Return the mock implementation
            return MockAIService()
        else:
            # Return the real implementation
            return AIService()