import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.analyze import GeminiProvider

@pytest.mark.asyncio
async def test_gemini_provider_retries_on_failure():
    # Mocking genai.Client
    with patch('src.analyze.genai.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mocking the async generate_content call
        mock_generate_content = AsyncMock()
        mock_client.aio.models.generate_content = mock_generate_content
        
        # Configure the mock to fail twice and then succeed
        mock_generate_content.side_effect = [
            Exception("503 UNAVAILABLE"),
            Exception("503 UNAVAILABLE"),
            MagicMock(text="Success report", usage_metadata=MagicMock(prompt_token_count=10, candidates_token_count=20))
        ]
        
        provider = GeminiProvider(api_key="test_key", model_name="test_model")
        
        messages = [{'role': 'user', 'content': 'hello'}]
        # Need to patch types.Content and types.Part as well or avoid real calls
        with patch('src.analyze.types.Content'), patch('src.analyze.types.Part.from_text'):
            response = await provider.chat(messages)
        
        assert response['content'] == "Success report"
        # Verify it was called 3 times
        assert mock_generate_content.call_count == 3

@pytest.mark.asyncio
async def test_gemini_provider_fails_after_max_retries():
    # Mocking genai.Client
    with patch('src.analyze.genai.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mocking the async generate_content call
        mock_generate_content = AsyncMock()
        mock_client.aio.models.generate_content = mock_generate_content
        
        # Configure the mock to always fail
        mock_generate_content.side_effect = Exception("Persistent error")
        
        provider = GeminiProvider(api_key="test_key", model_name="test_model")
        
        messages = [{'role': 'user', 'content': 'hello'}]
        with patch('src.analyze.types.Content'), patch('src.analyze.types.Part.from_text'):
            with pytest.raises(Exception, match="Persistent error"):
                await provider.chat(messages)
        
        # tenacity is configured for 3 attempts (1 initial + 2 retries)
        assert mock_generate_content.call_count == 3
