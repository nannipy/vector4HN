import os
import abc
import asyncio
import time
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from src.logger import log_usage

# Conditional import for Gemini to avoid crashing if dependency is missing during transition
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

import ollama

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Sends a chat request to the LLM.
        Returns a dict with 'content' (str) and usage stats.
        """
        pass

class OllamaProvider(LLMProvider):
    def __init__(self, host: str, model: str):
        self.host = host
        self.model = model
        self.client = ollama.AsyncClient(host=self.host)

    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        response = await self.client.chat(model=self.model, messages=messages)
        return {
            'content': response['message']['content'],
            'usage': {
                'input_tokens': response.get('prompt_eval_count', 0),
                'output_tokens': response.get('eval_count', 0),
                'duration_s': response.get('total_duration', 0) / 1e9,
            }
        }

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview"):
        if not HAS_GEMINI:
            raise ImportError("google-genai package is not installed.")
        self.client = genai.Client(api_key=api_key)
        self.model = model_name

    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        # Convert OpenAI/Ollama style messages to Gemini history
        # New SDK supports 'user' and 'model' roles.
        
        gemini_contents = []
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'user':
                role = 'user'
            elif role == 'assistant':
                role = 'model'
            else:
                continue
            
            gemini_contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=content)]
            ))

        # The new SDK is sync by default but has async support via http_options?
        # Actually checking docs, V1 beta SDK had async_generate_content.
        # The new `google-genai` SDK is different.
        # It seems `client.aio.models.generate_content` is the way.
        
        start_time = time.perf_counter()
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=gemini_contents
        )
        duration = time.perf_counter() - start_time
        
        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count if usage else 0
        output_tokens = usage.candidates_token_count if usage else 0
        
        return {
            'content': response.text,
            'usage': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'duration_s': duration, 
            }
        }

class Analyzer:
    def __init__(self):
        self._provider = None

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            self._provider = self._setup_provider()
        return self._provider

    def _setup_provider(self) -> LLMProvider:
        provider_type = os.getenv("LLM_PROVIDER", "ollama").lower()
        
        if provider_type == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required for Gemini provider.")
            model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
            return GeminiProvider(api_key=api_key, model_name=model)
        
        else:
            # Default to Ollama
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "llama3")
    def set_provider(self, provider_type: str, **kwargs) -> bool:
        """
        Dynamically sets the LLM provider.
        kwargs can contain: host (for ollama), model (for both), api_key (for gemini)
        """
        try:
            if provider_type == "gemini":
                api_key = kwargs.get("api_key") or os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("API Key required for Gemini")
                model = kwargs.get("model") or os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
                self._provider = GeminiProvider(api_key=api_key, model_name=model)
            elif provider_type == "ollama":
                host = kwargs.get("host") or os.getenv("OLLAMA_HOST", "http://localhost:11434")
                model = kwargs.get("model") or os.getenv("OLLAMA_MODEL", "llama3")
                self._provider = OllamaProvider(host=host, model=model)
            else:
                return False
                
            # Update env vars to persist in session (though not to file)
            os.environ["LLM_PROVIDER"] = provider_type
            if "model" in kwargs:
                if provider_type == "gemini":
                    os.environ["GEMINI_MODEL"] = kwargs["model"]
                else:
                    os.environ["OLLAMA_MODEL"] = kwargs["model"]
            
            return True
        except Exception as e:
            print(f"Error setting provider: {e}")
            return False

    def _clean_html(self, html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator=' ', strip=True)

    async def generate_report(self, story: Dict[str, Any], article_text: str, comments: List[Dict[str, Any]]) -> str:
        """
        Generates a comprehensive markdown report for a story.
        """
        
        # Prepare context data
        comment_text = "\n".join([
            f"- {c.get('by', 'anon')}: {self._clean_html(c.get('text', ''))}" 
            for c in comments[:30] 
        ])
        
        prompt = f"""
        You are an expert tech analyst. Analyze this Hacker News submission. 
        
        Metadata:
        Title: {story.get('title')}
        URL: {story.get('url')}
        Score: {story.get('score')}
        
        Article Content (Excerpt):
        {article_text[:4000]}
        
        Top Comments:
        {comment_text}
        
        Task:
        Create a detailed Markdown summary. Use the following structure EXACTLY:
        
        # {story.get('title')}
        
        ## 📝 Summary
        (A concise 3-sentence summary of the article)
        
        ## ⚖️ Pro & Cons / Key Arguments
        (Bulleted list of pros, cons, or key technical points discussed in article and comments)
        
        ## 💬 Community Sentiment
        (What are the commenters saying? What is the controversy? What are the top insights?)
        
        ## 🧠 Deep Dive Hooks
        (List 3 specific complex topics mentioned in this thread that the user might want to ask more about)
        """
        
        try:
            response = await self.provider.chat(messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            # Log Usage
            log_usage(
                model=getattr(self.provider, 'model', 'unknown'),
                input_tokens=response['usage']['input_tokens'],
                output_tokens=response['usage']['output_tokens'],
                duration_s=response['usage']['duration_s'],
                operation_type="report_generation"
            )
            
            return response['content']
        except Exception as e:
            return f"Error analyzing story: {str(e)}"

    async def chat_with_context(self, story: Dict[str, Any], article_text: str, comments: List[Dict[str, Any]], question: str, history: List[Dict[str, str]] = None) -> str:
        """
        Answers a specific question based on the full context using a structured prompt.
        """
        # Format comments with indentation based on depth
        formatted_comments = []
        for c in comments[:100]:
            depth = c.get("depth", 0)
            indent = "  " * depth
            author = c.get("by", "anon")
            text = self._clean_html(c.get("text", ""))
            formatted_comments.append(f"{indent}- {author}: {text}")
        
        comment_block = "\n".join(formatted_comments)
        
        prompt = f"""
        This is the article:
        ---
        TITLE: {story.get('title')}
        CONTENT:
        {article_text[:12000]}
        ---
        
        And these are the comments (top 100 with hierarchy):
        ---
        {comment_block}
        ---
        
        The user wants to know more about: {question}
        
        Task:
        Provide a detailed, well-structured answer based strictly on the provided context. 
        If the information is not in the article or comments, state that.
        Use Markdown for structure.
        """
        
        messages = []
        if history:
            messages.extend(history)
        
        messages.append({'role': 'user', 'content': prompt})
        
        try:
            response = await self.provider.chat(messages=messages)
            
            # Log Usage
            log_usage(
                model=getattr(self.provider, 'model', 'unknown'),
                input_tokens=response['usage']['input_tokens'],
                output_tokens=response['usage']['output_tokens'],
                duration_s=response['usage']['duration_s'],
                operation_type="chat_query"
            )
            
            return response['content']
        except Exception as e:
            return f"Error generating answer: {str(e)}"

analyzer = Analyzer()
