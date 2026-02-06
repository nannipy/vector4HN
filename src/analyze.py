import ollama
import os
import asyncio
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from src.logger import log_usage

# Load model from env or default
MODEL = os.getenv("OLLAMA_MODEL", "llama3")

class Analyzer:
    def __init__(self):
        self.client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

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
            # Ollama lib is sync by default, but we can wrap it or use the async client if available in newer versions.
            # The `ollama` pip package `Client` allows async with `AsyncClient`.
            # Let's switch to AsyncClient.
            async_client = ollama.AsyncClient(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
            response = await async_client.chat(model=MODEL, messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            # Log Usage
            log_usage(
                model=MODEL,
                input_tokens=response.get('prompt_eval_count', 0),
                output_tokens=response.get('eval_count', 0),
                duration_s=response.get('total_duration', 0) / 1e9, # duration is in nanoseconds
                operation_type="report_generation"
            )
            
            return response['message']['content']
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
            # We don't want to repeat the entire article in every message of the history if it's too long,
            # but for the first message in this deep dive format, we use the prompt above.
            # If there's history, we might want to just append the new question to the conversation.
            # However, the user specifically asked for this template.
            messages.extend(history)
        
        messages.append({'role': 'user', 'content': prompt})
        
        try:
            async_client = ollama.AsyncClient(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
            response = await async_client.chat(model=MODEL, messages=messages)
            
            # Log Usage
            log_usage(
                model=MODEL,
                input_tokens=response.get('prompt_eval_count', 0),
                output_tokens=response.get('eval_count', 0),
                duration_s=response.get('total_duration', 0) / 1e9,
                operation_type="chat_query"
            )
            
            return response['message']['content']
        except Exception as e:
            return f"Error generating answer: {str(e)}"

analyzer = Analyzer()

